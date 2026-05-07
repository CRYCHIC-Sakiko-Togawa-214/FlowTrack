import gc
import logging
import math
import os
import random
import sys
import types
from contextlib import contextmanager
from functools import partial

import torch
import torch.cuda.amp as amp
import torch.distributed as dist
import torch.nn.functional as F
from tqdm import tqdm

from .distributed.fsdp import shard_model
from .modules.model import WanModel
from .modules.t5 import T5EncoderModel
from .modules.vae import WanVAE
from .utils.fm_solvers import (FlowDPMSolverMultistepScheduler,
                               get_sampling_sigmas, retrieve_timesteps)
from .utils.fm_solvers_unipc import FlowUniPCMultistepScheduler


class WanT2V:

    def __init__(
        self,
        config,
        checkpoint_dir,
        device_id=0,
        rank=0,
        t5_fsdp=False,
        dit_fsdp=False,
        use_usp=False,
        t5_cpu=False,
    ):
        r"""
        Initializes the Wan text-to-video generation model components.

        Args:
            config (EasyDict):
                Object containing model parameters initialized from config.py
            checkpoint_dir (`str`):
                Path to directory containing model checkpoints
            device_id (`int`,  *optional*, defaults to 0):
                Id of target GPU device
            rank (`int`,  *optional*, defaults to 0):
                Process rank for distributed training
            t5_fsdp (`bool`, *optional*, defaults to False):
                Enable FSDP sharding for T5 model
            dit_fsdp (`bool`, *optional*, defaults to False):
                Enable FSDP sharding for DiT model
            use_usp (`bool`, *optional*, defaults to False):
                Enable distribution strategy of USP.
            t5_cpu (`bool`, *optional*, defaults to False):
                Whether to place T5 model on CPU. Only works without t5_fsdp.
        """
        self.device = torch.device(f"cuda:{device_id}")
        self.config = config
        self.rank = rank
        self.t5_cpu = t5_cpu

        self.num_train_timesteps = config.num_train_timesteps
        self.param_dtype = config.param_dtype

        shard_fn = partial(shard_model, device_id=device_id)
        self.text_encoder = T5EncoderModel(
            text_len=config.text_len,
            dtype=config.t5_dtype,
            device=torch.device('cpu'),
            checkpoint_path=os.path.join(checkpoint_dir, config.t5_checkpoint),
            tokenizer_path=os.path.join(checkpoint_dir, config.t5_tokenizer),
            shard_fn=shard_fn if t5_fsdp else None)

        self.vae_stride = config.vae_stride
        self.patch_size = config.patch_size
        self.vae = WanVAE(
            vae_pth=os.path.join(checkpoint_dir, config.vae_checkpoint),
            device=self.device)

        logging.info(f"Creating WanModel from {checkpoint_dir}")
        self.model = WanModel.from_pretrained(checkpoint_dir)
        self.model.eval().requires_grad_(False)

        if use_usp:
            from xfuser.core.distributed import \
                get_sequence_parallel_world_size

            from .distributed.xdit_context_parallel import (usp_attn_forward,
                                                            usp_dit_forward)
            for block in self.model.blocks:
                block.self_attn.forward = types.MethodType(
                    usp_attn_forward, block.self_attn)
            self.model.forward = types.MethodType(usp_dit_forward, self.model)
            self.sp_size = get_sequence_parallel_world_size()
        else:
            self.sp_size = 1

        if dist.is_initialized():
            dist.barrier()
        if dit_fsdp:
            self.model = shard_fn(self.model)
        else:
            self.model.to(self.device)

        self.sample_neg_prompt = config.sample_neg_prompt

    @staticmethod
    def _align_prior_region_to_latent(
        prior_region_mask,
        latent_ref: torch.Tensor,
        *,
        spatial_dilate: int = 0,
        temporal_dilate: int = 0,
    ):
        """Align pixel-space prior mask to latent grid as soft mask M_p in [0, 1].

        Args:
            prior_region_mask: tensor-like [1,T,H,W] or [T,H,W], pixel-space mask.
            latent_ref: latent tensor [C,T,H,W] that defines target grid.
            spatial_dilate: optional spatial dilation radius on latent grid.
            temporal_dilate: optional temporal dilation radius on latent grid.
        """
        if prior_region_mask is None:
            return None

        if not torch.is_tensor(prior_region_mask):
            prior_region_mask = torch.tensor(prior_region_mask)

        if prior_region_mask.ndim == 3:
            prior = prior_region_mask.unsqueeze(0)  # [1,T,H,W]
        elif prior_region_mask.ndim == 4:
            prior = prior_region_mask
        else:
            raise ValueError(
                f"prior_region_mask must be [T,H,W] or [1,T,H,W], got {tuple(prior_region_mask.shape)}"
            )

        if int(prior.shape[0]) != 1:
            prior = prior.mean(dim=0, keepdim=True)

        target_t = int(latent_ref.shape[1])
        target_h = int(latent_ref.shape[2])
        target_w = int(latent_ref.shape[3])

        prior = prior.to(device=latent_ref.device, dtype=torch.float32)

        if int(prior.shape[1]) != target_t:
            if target_t <= 1:
                idxs = torch.tensor([0], dtype=torch.long, device=prior.device)
            else:
                idxs = torch.linspace(
                    0,
                    int(prior.shape[1]) - 1,
                    target_t,
                    device=prior.device,
                ).round().to(torch.long)
            prior = prior[:, idxs]

        if int(prior.shape[2]) != target_h or int(prior.shape[3]) != target_w:
            prior_t = prior.permute(1, 0, 2, 3)  # [T,1,H,W]
            prior_t = F.interpolate(
                prior_t,
                size=(target_h, target_w),
                mode='nearest',
            )
            prior = prior_t.permute(1, 0, 2, 3)

        spatial_dilate = int(max(0, spatial_dilate))
        temporal_dilate = int(max(0, temporal_dilate))
        if spatial_dilate > 0 or temporal_dilate > 0:
            prior = F.max_pool3d(
                prior.unsqueeze(0),  # [1,1,T,H,W]
                kernel_size=(
                    1 + 2 * temporal_dilate,
                    1 + 2 * spatial_dilate,
                    1 + 2 * spatial_dilate,
                ),
                stride=1,
                padding=(temporal_dilate, spatial_dilate, spatial_dilate),
            ).squeeze(0)

        return prior.clamp(0.0, 1.0).to(dtype=latent_ref.dtype)

    @staticmethod
    def _compute_edit_confidence(
        v_delta: torch.Tensor,
        *,
        conf_threshold_scale: float = 1.0,
        conf_mask_sharpness: float = 15.0,
    ) -> torch.Tensor:
        """Compute internal edit confidence from the raw source-target differential."""
        v_mag = torch.abs(v_delta.to(dtype=torch.float32)).mean(dim=0, keepdim=True)  # [1,T,H,W]
        tau = v_mag.mean() * float(max(0.0, conf_threshold_scale))
        sharp = float(max(1e-3, conf_mask_sharpness))
        conf = torch.sigmoid(sharp * (v_mag - tau) / (tau + 1e-8))
        # Lightweight spatial smooth for stability; keep temporal granularity unchanged.
        conf = F.avg_pool3d(
            conf.unsqueeze(0),
            kernel_size=(1, 3, 3),
            stride=1,
            padding=(0, 1, 1),
        ).squeeze(0)
        return conf.clamp(0.0, 1.0).to(dtype=v_delta.dtype)

    @staticmethod
    def _apply_region_adaptive_guidance(
        v_cond: torch.Tensor,
        v_uncond: torch.Tensor,
        *,
        guide_scale: float,
        prior_region: torch.Tensor = None,
        out_mult: float = 1.0,
    ) -> torch.Tensor:
        """Region-adaptive guidance: downscale CFG outside prior region."""
        if prior_region is None:
            return v_uncond + float(guide_scale) * (v_cond - v_uncond)

        out_mult = float(max(0.0, min(1.0, out_mult)))
        cfg_map = float(guide_scale) * (out_mult + (1.0 - out_mult) * prior_region.to(dtype=torch.float32))
        cfg_map = cfg_map.to(device=v_cond.device, dtype=v_cond.dtype)
        return v_uncond + cfg_map * (v_cond - v_uncond)

    @staticmethod
    def _compute_edit_support_gate(
        *,
        edit_conf: torch.Tensor,
        prior_region: torch.Tensor = None,
        esa_scale: float = 0.9,
        prior_force: float = 0.6,
    ) -> torch.Tensor:
        """Compute a local edit-support gate from confidence and prior support."""
        alpha_esa = float(max(0.0, min(1.0, esa_scale)))
        conf = edit_conf.to(dtype=torch.float32).clamp(0.0, 1.0)

        if prior_region is None:
            prior_support = torch.zeros_like(conf)
        else:
            force = float(max(0.0, min(1.0, prior_force)))
            prior = prior_region.to(dtype=torch.float32).clamp(0.0, 1.0)
            prior_support = (force * prior).clamp(0.0, 1.0)

        edit_support = (conf + (1.0 - conf) * prior_support).clamp(0.0, 1.0)
        edit_gate = ((1.0 - alpha_esa) + alpha_esa * edit_support).clamp(0.0, 1.0)
        return edit_gate.to(dtype=edit_conf.dtype, device=edit_conf.device)

    @staticmethod
    def _apply_edit_support_arbitration(
        v_delta: torch.Tensor,
        *,
        edit_conf: torch.Tensor,
        prior_region: torch.Tensor = None,
        esa_scale: float = 0.9,
        prior_force: float = 0.6,
    ) -> torch.Tensor:
        """Apply the edit-support gate to the candidate differential update."""
        edit_gate = WanT2V._compute_edit_support_gate(
            edit_conf=edit_conf,
            prior_region=prior_region,
            esa_scale=esa_scale,
            prior_force=prior_force,
        )
        return v_delta * edit_gate.to(device=v_delta.device, dtype=v_delta.dtype)

    @staticmethod
    def _solve_causal_pre_execution_control(
        v_delta: torch.Tensor,
        *,
        support_gate: torch.Tensor,
        prev_pre_control: torch.Tensor = None,
        traj_lambda: float = 0.0,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Legacy two-stage execution controller kept for old ablations.

        This is not the FlowTrack controller used by the current method.
        It implements the older two-stage form:

            w_k = (d_k + lambda * w_{k-1}) / (1 + lambda)
            u_k = s_k * w_k

        where `d_k` is the candidate differential update, `w_k` is the
        pre-execution control, and `support_gate == s_k in [0, 1]` is the
        local proximal execution coefficient.
        """
        lam = float(max(0.0, traj_lambda))
        gate = support_gate.to(device=v_delta.device, dtype=v_delta.dtype).clamp(0.0, 1.0)
        drift = v_delta.to(dtype=torch.float32)
        gate_f = gate.to(dtype=torch.float32)
        if prev_pre_control is None:
            prev = torch.zeros_like(drift)
        else:
            prev = prev_pre_control.to(device=v_delta.device, dtype=torch.float32)

        if lam == 0.0:
            pre_control = drift
        else:
            pre_control = (drift + lam * prev) / (1.0 + lam)
        control = gate_f * pre_control
        return (
            pre_control.to(device=v_delta.device, dtype=v_delta.dtype),
            control.to(device=v_delta.device, dtype=v_delta.dtype),
        )

    @staticmethod
    def _compute_flowtrack_state_cost(
        reference_velocity: torch.Tensor,
        *,
        flowtrack_lambda: float = 0.0,
        flowtrack_s_min: float = 0.0,
        assignment_sharpness: float = 30.0,
        response_eps: float = 1e-12,
    ) -> torch.Tensor:
        """Construct a_k from two-class response-calibrated execution assignment.

        Theory mapping:
            m_k(i) = mean_c |d_k(i, c)|
            tau_k = Otsu threshold that minimizes two-class within variance
            z_k(i) = sigmoid(kappa * (m_k(i) - tau_k) / (tau_k + eps))
            tilde_s_k(i) = z_k(i)
            alpha_k(i) = (1 + lambda_tau) * (1 / tilde_s_k(i) - 1)
            a_k(i, c) = alpha_k(i)

        The returned tensor has shape [1, T, H, W] and is broadcast over the
        channel dimension when used in the control update.
        """
        lam = float(max(0.0, flowtrack_lambda))
        s_min = float(max(0.0, min(1.0, flowtrack_s_min)))
        drift = reference_velocity.to(dtype=torch.float32)
        response = drift.abs().mean(dim=0, keepdim=True)
        if lam == 0.0:
            return torch.zeros_like(response).to(
                device=reference_velocity.device,
                dtype=reference_velocity.dtype,
            )
        response = F.avg_pool3d(
            response.unsqueeze(0),
            kernel_size=(1, 3, 3),
            stride=1,
            padding=(0, 1, 1),
        ).squeeze(0)
        if float((response.max() - response.min()).abs().item()) <= float(response_eps):
            return torch.zeros_like(response).to(
                device=reference_velocity.device,
                dtype=reference_velocity.dtype,
            )
        threshold = WanT2V._otsu_response_threshold(response)
        sharpness = float(max(1e-3, assignment_sharpness))
        support = torch.sigmoid(sharpness * (response - threshold) / (threshold + float(response_eps)))
        support = support.clamp(0.0, 1.0)
        execution_coeff = s_min + (1.0 - s_min) * support
        execution_coeff = execution_coeff.clamp(min=s_min, max=1.0)
        state_cost = (1.0 + lam) * (1.0 / execution_coeff.clamp_min(1e-6) - 1.0)
        return state_cost.clamp_min(0.0).to(
            device=reference_velocity.device,
            dtype=reference_velocity.dtype,
        )

    @staticmethod
    def _resolve_flowtrack_state_cost(
        reference_velocity: torch.Tensor,
        *,
        flowtrack_lambda: float = 0.0,
        flowtrack_s_min: float = 0.0,
        flowtrack_state_mode: str = "otsu",
        assignment_sharpness: float = 30.0,
    ) -> torch.Tensor:
        """Resolve a_k for FlowTrack and its structural ablations.

        Modes:
            otsu: default pointwise state-dependent execution cost.
            none: no state-dependent execution cost, i.e. a_k = 0.
            uniform: replace pointwise a_k with its global mean.
        """
        mode = str(flowtrack_state_mode).lower()
        drift = reference_velocity.to(dtype=torch.float32)
        zero_cost = torch.zeros_like(drift[:1]).to(
            device=reference_velocity.device,
            dtype=reference_velocity.dtype,
        )
        if mode == "none":
            return zero_cost
        if mode not in {"otsu", "uniform"}:
            raise ValueError(f"Unsupported flowtrack_state_mode: {flowtrack_state_mode}")

        state_cost = WanT2V._compute_flowtrack_state_cost(
            reference_velocity,
            flowtrack_lambda=flowtrack_lambda,
            flowtrack_s_min=flowtrack_s_min,
            assignment_sharpness=assignment_sharpness,
        )
        if mode == "uniform":
            return state_cost.to(dtype=torch.float32).mean().expand_as(state_cost).clone().to(
                device=reference_velocity.device,
                dtype=reference_velocity.dtype,
            )
        return state_cost

    @staticmethod
    def _otsu_response_threshold(response: torch.Tensor, bins: int = 256) -> torch.Tensor:
        """Estimate a two-class response threshold by minimizing within variance."""
        values = response.detach().to(dtype=torch.float32).flatten()
        if values.numel() == 0:
            return response.new_tensor(0.0, dtype=torch.float32)

        v_min = values.min()
        v_max = values.max()
        if not torch.isfinite(v_min) or not torch.isfinite(v_max):
            return torch.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0).mean()
        if float((v_max - v_min).abs().item()) <= 1e-12:
            return v_min

        bins = int(max(8, bins))
        hist = torch.histc(values, bins=bins, min=float(v_min.item()), max=float(v_max.item()))
        bin_centers = torch.linspace(
            float(v_min.item()),
            float(v_max.item()),
            bins,
            device=values.device,
            dtype=torch.float32,
        )
        total = hist.sum().clamp_min(1.0)
        weight0 = hist.cumsum(dim=0)
        weight1 = total - weight0
        sum0 = (hist * bin_centers).cumsum(dim=0)
        sum_total = (hist * bin_centers).sum()
        valid = (weight0 > 0) & (weight1 > 0)
        mean0 = sum0 / weight0.clamp_min(1.0)
        mean1 = (sum_total - sum0) / weight1.clamp_min(1.0)
        between = weight0 * weight1 * (mean0 - mean1).square()
        between = torch.where(valid, between, torch.full_like(between, -1.0))
        threshold_idx = torch.argmax(between)
        return bin_centers[threshold_idx].to(device=response.device, dtype=torch.float32)

    @staticmethod
    def _solve_flowtrack_control(
        reference_velocity: torch.Tensor,
        *,
        prev_control: torch.Tensor = None,
        flowtrack_lambda: float = 0.0,
        flowtrack_s_min: float = 0.0,
        flowtrack_state_mode: str = "otsu",
        flowtrack_memory_mode: str = "pre",
        assignment_sharpness: float = 30.0,
        state_cost: torch.Tensor = None,
        return_pre_control: bool = False,
    ) -> torch.Tensor:
        """Solve FlowTrack's causal tracking controller.

        Theory mapping:
            d_k = reference_velocity
            w_k = pre-execution control
            u_k = executed control
            w_k = (d_k + lambda_tau * w_{k-1}) / (1 + lambda_tau)
            with state-dependent effort:
            u_k = (d_k + lambda_tau * w_{k-1})
                  / (1 + lambda_tau + a_k)

        If lambda_tau > 0, the first effective step uses w_0 = 0, matching
        the pre-execution recursion. If lambda_tau == 0, it degenerates to
        direct execution u_k = d_k.
        """
        lam = float(max(0.0, flowtrack_lambda))
        state_mode = str(flowtrack_state_mode).lower()
        memory_mode = str(flowtrack_memory_mode).lower()
        if state_mode not in {"otsu", "none", "uniform"}:
            raise ValueError(f"Unsupported flowtrack_state_mode: {flowtrack_state_mode}")
        if memory_mode not in {"pre", "none"}:
            raise ValueError(f"Unsupported flowtrack_memory_mode: {flowtrack_memory_mode}")

        drift = reference_velocity.to(dtype=torch.float32)
        if lam == 0.0:
            pre_control = drift
            control = drift
        else:
            if prev_control is None:
                prev = torch.zeros_like(drift)
            else:
                prev = prev_control.to(
                    device=reference_velocity.device,
                    dtype=torch.float32,
                )
            if memory_mode == "pre":
                numerator = drift + lam * prev
                pre_control = numerator / (1.0 + lam)
            else:
                pre_control = drift
                numerator = (1.0 + lam) * pre_control
            if state_cost is None:
                state_cost = WanT2V._resolve_flowtrack_state_cost(
                    reference_velocity,
                    flowtrack_lambda=lam,
                    flowtrack_s_min=flowtrack_s_min,
                    flowtrack_state_mode=state_mode,
                    assignment_sharpness=assignment_sharpness,
                )
            denom = 1.0 + lam + state_cost.to(
                device=reference_velocity.device,
                dtype=torch.float32,
            )
            control = numerator / denom
        control = control.to(device=reference_velocity.device, dtype=reference_velocity.dtype)
        pre_control = pre_control.to(device=reference_velocity.device, dtype=reference_velocity.dtype)
        if return_pre_control:
            return control, pre_control
        return control

    def generate(self,
                 input_prompt,
                 size=(1280, 720),
                 frame_num=81,
                 shift=5.0,
                 sample_solver='unipc',
                 sampling_steps=50,
                 guide_scale=5.0,
                 n_prompt="",
                 seed=-1,
                 offload_model=True):
        r"""
        Generates video frames from text prompt using diffusion process.

        Args:
            input_prompt (`str`):
                Text prompt for content generation
            size (tupele[`int`], *optional*, defaults to (1280,720)):
                Controls video resolution, (width,height).
            frame_num (`int`, *optional*, defaults to 81):
                How many frames to sample from a video. The number should be 4n+1
            shift (`float`, *optional*, defaults to 5.0):
                Noise schedule shift parameter. Affects temporal dynamics
            sample_solver (`str`, *optional*, defaults to 'unipc'):
                Solver used to sample the video.
            sampling_steps (`int`, *optional*, defaults to 40):
                Number of diffusion sampling steps. Higher values improve quality but slow generation
            guide_scale (`float`, *optional*, defaults 5.0):
                Classifier-free guidance scale. Controls prompt adherence vs. creativity
            n_prompt (`str`, *optional*, defaults to ""):
                Negative prompt for content exclusion. If not given, use `config.sample_neg_prompt`
            seed (`int`, *optional*, defaults to -1):
                Random seed for noise generation. If -1, use random seed.
            offload_model (`bool`, *optional*, defaults to True):
                If True, offloads models to CPU during generation to save GPU memory

        Returns:
            torch.Tensor:
                Generated video frames tensor. Dimensions: (C, N H, W) where:
                - C: Color channels (3 for RGB)
                - N: Number of frames (81)
                - H: Frame height (from size)
                - W: Frame width from size)
        """
        # preprocess
        F = frame_num
        target_shape = (self.vae.model.z_dim, (F - 1) // self.vae_stride[0] + 1,
                        size[1] // self.vae_stride[1],
                        size[0] // self.vae_stride[2])

        seq_len = math.ceil((target_shape[2] * target_shape[3]) /
                            (self.patch_size[1] * self.patch_size[2]) *
                            target_shape[1] / self.sp_size) * self.sp_size

        if n_prompt == "":
            n_prompt = self.sample_neg_prompt
        seed = seed if seed >= 0 else random.randint(0, sys.maxsize)
        seed_g = torch.Generator(device=self.device)
        seed_g.manual_seed(seed)

        if not self.t5_cpu:
            self.text_encoder.model.to(self.device)
            context = self.text_encoder([input_prompt], self.device)
            context_null = self.text_encoder([n_prompt], self.device)
            if offload_model:
                self.text_encoder.model.cpu()
        else:
            context = self.text_encoder([input_prompt], torch.device('cpu'))
            context_null = self.text_encoder([n_prompt], torch.device('cpu'))
            context = [t.to(self.device) for t in context]
            context_null = [t.to(self.device) for t in context_null]

        noise = [
            torch.randn(
                target_shape[0],
                target_shape[1],
                target_shape[2],
                target_shape[3],
                dtype=torch.float32,
                device=self.device,
                generator=seed_g)
        ]

        @contextmanager
        def noop_no_sync():
            yield

        no_sync = getattr(self.model, 'no_sync', noop_no_sync)

        # evaluation mode
        with amp.autocast(dtype=self.param_dtype), torch.no_grad(), no_sync():

            if sample_solver == 'unipc':
                sample_scheduler = FlowUniPCMultistepScheduler(
                    num_train_timesteps=self.num_train_timesteps,
                    shift=1,
                    use_dynamic_shifting=False)
                sample_scheduler.set_timesteps(
                    sampling_steps, device=self.device, shift=shift)
                timesteps = sample_scheduler.timesteps
            elif sample_solver == 'dpm++':
                sample_scheduler = FlowDPMSolverMultistepScheduler(
                    num_train_timesteps=self.num_train_timesteps,
                    shift=1,
                    use_dynamic_shifting=False)
                sampling_sigmas = get_sampling_sigmas(sampling_steps, shift)
                timesteps, _ = retrieve_timesteps(
                    sample_scheduler,
                    device=self.device,
                    sigmas=sampling_sigmas)
            else:
                raise NotImplementedError("Unsupported solver.")

            # sample videos
            latents = noise

            arg_c = {'context': context, 'seq_len': seq_len}
            arg_null = {'context': context_null, 'seq_len': seq_len}

            for _, t in enumerate(tqdm(timesteps)):
                latent_model_input = latents
                timestep = [t]

                timestep = torch.stack(timestep)

                self.model.to(self.device)
                noise_pred_cond = self.model(
                    latent_model_input, t=timestep, **arg_c)[0]
                noise_pred_uncond = self.model(
                    latent_model_input, t=timestep, **arg_null)[0]

                noise_pred = noise_pred_uncond + guide_scale * (
                    noise_pred_cond - noise_pred_uncond)

                temp_x0 = sample_scheduler.step(
                    noise_pred.unsqueeze(0),
                    t,
                    latents[0].unsqueeze(0),
                    return_dict=False,
                    generator=seed_g)[0]
                latents = [temp_x0.squeeze(0)]

            x0 = latents
            if offload_model:
                self.model.cpu()
            if self.rank == 0:
                videos = self.vae.decode(x0)

        del noise, latents
        del sample_scheduler
        if offload_model:
            gc.collect()
            torch.cuda.synchronize()
        if dist.is_initialized():
            dist.barrier()

        return videos[0] if self.rank == 0 else None

    def edit(self, video,
                 src_prompt,
                 tgt_prompt,
                 size=(1280, 720),
                 frame_num=81,
                 shift=5.0,
                 sample_solver='unipc',
                 sampling_steps=50,
                 guide_scale=5.0,
                 tgt_guide_scale=10.0,
                 skip_timesteps=15,
                 use_prior_region=False,
                 prior_region_mask=None,
                 prior_region_dilate=0,
                 prior_region_temporal=0,
                 region_guidance_out_mult=1.0,
                 use_esa=False,
                 esa_scale=0.9,
                 conf_threshold_scale=1.0,
                 conf_mask_sharpness=15.0,
                 prior_force=0.6,
                 esa_ablation_mode='full',
                 phase_switch_ratio=0.5,
                 tgt_guide_scale_late=None,
                 region_guidance_out_mult_late=None,
                 esa_scale_late=None,
                 prior_force_late=None,
                 use_traj_prox=True,
                 traj_lambda=0.20,
                 traj_log_stats=False,
                 use_flowtrack=True,
                 flowtrack_lambda=0.20,
                 flowtrack_s_min=0.0,
                 flowtrack_state_mode="otsu",
                 flowtrack_memory_mode="pre",
                 flowtrack_log_stats=None,
                 n_prompt="",
                 seed=-1,
                 offload_model=True):
        r"""
        Generates video frames from text prompt using diffusion process.

        Args:
            src_prompt (`str`):
                Text prompt for content generation
            size (tupele[`int`], *optional*, defaults to (1280,720)):
                Controls video resolution, (width,height).
            frame_num (`int`, *optional*, defaults to 81):
                How many frames to sample from a video. The number should be 4n+1
            shift (`float`, *optional*, defaults to 5.0):
                Noise schedule shift parameter. Affects temporal dynamics
            sample_solver (`str`, *optional*, defaults to 'unipc'):
                Solver used to sample the video.
            sampling_steps (`int`, *optional*, defaults to 40):
                Number of diffusion sampling steps. Higher values improve quality but slow generation
            guide_scale (`float`, *optional*, defaults 5.0):
                Classifier-free guidance scale. Controls prompt adherence vs. creativity
            tgt_guide_scale (`float`, *optional*, defaults to 10.0):
                Target guidance scale for reference velocity construction.
            skip_timesteps (`int`, *optional*, defaults to 15):
                Skip timesteps before enabling differential editing.
            phase_switch_ratio (`float`, *optional*, defaults to 0.5):
                Switch ratio for optional two-phase parameter schedule on effective edit steps.
            n_prompt (`str`, *optional*, defaults to ""):
                Negative prompt for content exclusion. If not given, use `config.sample_neg_prompt`
            seed (`int`, *optional*, defaults to -1):
                Random seed for noise generation. If -1, use random seed.
            offload_model (`bool`, *optional*, defaults to True):
                If True, offloads models to CPU during generation to save GPU memory

        Returns:
            torch.Tensor:
                Generated video frames tensor. Dimensions: (C, N H, W) where:
                - C: Color channels (3 for RGB)
                - N: Number of frames (81)
                - H: Frame height (from size)
                - W: Frame width from size)
        """
        # preprocess
        F = frame_num
        video = video.to('cuda')
        latents = self.vae.encode(video) #[b,c,t,h,w]
        target_shape = (self.vae.model.z_dim, (F - 1) // self.vae_stride[0] + 1,
                        size[1] // self.vae_stride[1],
                        size[0] // self.vae_stride[2])

        seq_len = math.ceil((target_shape[2] * target_shape[3]) /
                            (self.patch_size[1] * self.patch_size[2]) *
                            target_shape[1] / self.sp_size) * self.sp_size

        if n_prompt == "":
            n_prompt = self.sample_neg_prompt
        seed = seed if seed >= 0 else random.randint(0, sys.maxsize)
        seed_g = torch.Generator(device=self.device)
        seed_g.manual_seed(seed)

        if not self.t5_cpu:
            self.text_encoder.model.to(self.device)
            context_src = self.text_encoder([src_prompt], self.device)
            context_tgt = self.text_encoder([tgt_prompt], self.device)
            context_null = self.text_encoder([n_prompt], self.device)
            if offload_model:
                self.text_encoder.model.cpu()
        # else:
        #     context = self.text_encoder([src_prompt], torch.device('cpu'))
        #     context_null = self.text_encoder([n_prompt], torch.device('cpu'))
        #     context = [t.to(self.device) for t in context]
        #     context_null = [t.to(self.device) for t in context_null]

        

        @contextmanager
        def noop_no_sync():
            yield

        no_sync = getattr(self.model, 'no_sync', noop_no_sync)

        # evaluation mode
        with amp.autocast(dtype=self.param_dtype), torch.no_grad(), no_sync():

            if sample_solver == 'unipc':
                sample_scheduler = FlowUniPCMultistepScheduler(
                    num_train_timesteps=self.num_train_timesteps,
                    shift=1,
                    use_dynamic_shifting=False)
                sample_scheduler.set_timesteps(
                    sampling_steps, device=self.device, shift=shift)
                timesteps = sample_scheduler.timesteps
            elif sample_solver == 'dpm++':
                sample_scheduler = FlowDPMSolverMultistepScheduler(
                    num_train_timesteps=self.num_train_timesteps,
                    shift=1,
                    use_dynamic_shifting=False)
                sampling_sigmas = get_sampling_sigmas(sampling_steps, shift)
                timesteps, _ = retrieve_timesteps(
                    sample_scheduler,
                    device=self.device,
                    sigmas=sampling_sigmas)
            else:
                raise NotImplementedError("Unsupported solver.")

            # sample videos

            arg_src = {'context': context_src, 'seq_len': seq_len}
            arg_tgt = {'context': context_tgt, 'seq_len': seq_len}
            arg_null = {'context': context_null, 'seq_len': seq_len}
            start_latents = latents #[b, c, t, h, w]
            mv_latent = latents
            flowtrack_enabled = bool(use_flowtrack)
            if flowtrack_lambda is None:
                flowtrack_lambda = traj_lambda
            if flowtrack_log_stats is None:
                flowtrack_log_stats = traj_log_stats
            flowtrack_lambda = float(max(0.0, float(flowtrack_lambda)))
            flowtrack_s_min = float(max(0.0, min(1.0, float(flowtrack_s_min))))
            flowtrack_state_mode = str(flowtrack_state_mode).lower()
            flowtrack_memory_mode = str(flowtrack_memory_mode).lower()
            if flowtrack_state_mode not in {"otsu", "none", "uniform"}:
                raise ValueError(f"Unsupported flowtrack_state_mode: {flowtrack_state_mode}")
            if flowtrack_memory_mode not in {"pre", "none"}:
                raise ValueError(f"Unsupported flowtrack_memory_mode: {flowtrack_memory_mode}")
            if flowtrack_enabled and (bool(use_prior_region) or bool(use_esa)):
                logging.info(
                    "FlowTrack ignores prior-region / ESA execution layers; "
                    "using reference velocity difference d_k and causal control u_k only."
                )
                use_prior_region = False
                use_esa = False

            prior_region_latent = None
            if (not flowtrack_enabled) and bool(use_prior_region) and prior_region_mask is not None:
                prior_region_latent = self._align_prior_region_to_latent(
                    prior_region_mask=prior_region_mask,
                    latent_ref=start_latents[0],
                    spatial_dilate=int(prior_region_dilate),
                    temporal_dilate=int(prior_region_temporal),
                )
                if prior_region_latent is not None:
                    logging.info(
                        "Prior region enabled: ratio=%.4f out_mult=%.3f force=%.2f",
                        float(prior_region_latent.mean().item()),
                        float(max(0.0, min(1.0, region_guidance_out_mult))),
                        float(max(0.0, min(1.0, prior_force))),
                    )

            esa_ablation_mode = str(esa_ablation_mode).lower()
            if (not flowtrack_enabled) and esa_ablation_mode not in {"full", "confidence_only", "prior_only"}:
                raise ValueError(f"Unsupported esa_ablation_mode: {esa_ablation_mode}")

            switch_ratio = float(max(0.0, min(1.0, phase_switch_ratio)))
            has_two_phase = any(
                v is not None for v in (
                    tgt_guide_scale_late,
                    None if flowtrack_enabled else region_guidance_out_mult_late,
                    None if flowtrack_enabled else esa_scale_late,
                    None if flowtrack_enabled else prior_force_late,
                )
            )
            if has_two_phase:
                logging.info(
                    "Two-phase schedule enabled: switch=%.2f "
                    "tgt_guide(early=%.3f late=%s) out_mult(early=%.3f late=%s) "
                    "esa_scale(early=%.3f late=%s) prior_force(early=%.3f late=%s)",
                    switch_ratio,
                    float(tgt_guide_scale),
                    "None" if tgt_guide_scale_late is None else f"{float(tgt_guide_scale_late):.3f}",
                    float(region_guidance_out_mult),
                    "None" if region_guidance_out_mult_late is None else f"{float(region_guidance_out_mult_late):.3f}",
                    float(esa_scale),
                    "None" if esa_scale_late is None else f"{float(esa_scale_late):.3f}",
                    float(prior_force),
                    "None" if prior_force_late is None else f"{float(prior_force_late):.3f}",
                )

            total_edit_steps = max(1, int(len(timesteps) - int(skip_timesteps)))
            prev_reference_velocity = None
            prev_pre_control = None
            prev_executed_control = None
            flowtrack_stats = {
                "v_d": 0.0,
                "v_u": 0.0,
                "e_track": 0.0,
                "d_norm": 0.0,
                "e_effort": 0.0,
                "r_opt": 0.0,
                "a_mean": 0.0,
                "a_count": 0,
                "s_mean": 0.0,
                "s_q10": 0.0,
                "s_q50": 0.0,
                "s_q90": 0.0,
                "s_min": float("inf"),
                "s_count": 0,
            }

            def _pick(early, late, progress):
                if late is None:
                    return early
                return late if progress >= switch_ratio else early

            for i, t in enumerate(tqdm(timesteps)):
                noise = [
                    torch.randn(
                        target_shape[0],
                        target_shape[1],
                        target_shape[2],
                        target_shape[3],
                        dtype=torch.float32,
                        device=self.device,
                        generator=seed_g)
                ]
                latent_model_input = latents
                timestep = [t]
                timestep = torch.stack(timestep)
                if i < skip_timesteps:
                    continue
                edit_progress = float(i - int(skip_timesteps) + 1) / float(total_edit_steps)
                cur_tgt_guide_scale = float(_pick(tgt_guide_scale, tgt_guide_scale_late, edit_progress))
                cur_region_guidance_out_mult = float(
                    _pick(region_guidance_out_mult, region_guidance_out_mult_late, edit_progress))
                cur_esa_scale = float(_pick(esa_scale, esa_scale_late, edit_progress))
                cur_prior_force = float(_pick(prior_force, prior_force_late, edit_progress))
                t_prev = 1000 if i==0 else timesteps[i-1]
                src_latent = [t_prev/1000.0*noise[0] + (1000-t_prev)/1000.0*start_latents[0]]
                tgt_latent = [mv_latent[0]+src_latent[0]-start_latents[0]]
                self.model.to(self.device)
                noise_pred_cond_src = self.model(
                    src_latent, t=timestep, **arg_src)[0]
                noise_pred_cond_tgt = self.model(
                    tgt_latent, t=timestep, **arg_tgt)[0]
                noise_pred_uncond_src = self.model(
                    src_latent, t=timestep, **arg_null)[0]
                noise_pred_uncond_tgt = self.model(
                    tgt_latent, t=timestep, **arg_null)[0]

                noise_pred_src = noise_pred_uncond_src + guide_scale * (
                    noise_pred_cond_src - noise_pred_uncond_src)
                noise_pred_tgt_base = noise_pred_uncond_tgt + cur_tgt_guide_scale * (
                    noise_pred_cond_tgt - noise_pred_uncond_tgt)
                noise_pred_delta_base = noise_pred_tgt_base - noise_pred_src

                if flowtrack_enabled:
                    noise_pred_tgt = noise_pred_tgt_base
                else:
                    noise_pred_tgt = self._apply_region_adaptive_guidance(
                        noise_pred_cond_tgt,
                        noise_pred_uncond_tgt,
                        guide_scale=cur_tgt_guide_scale,
                        prior_region=prior_region_latent if bool(use_prior_region) else None,
                        out_mult=cur_region_guidance_out_mult,
                    )
                noise_pred_candidate = noise_pred_tgt - noise_pred_src
                reference_velocity = noise_pred_candidate
                noise_pred = reference_velocity
                support_gate = None

                if (not flowtrack_enabled) and bool(use_esa):
                    edit_conf = self._compute_edit_confidence(
                        noise_pred_delta_base,
                        conf_threshold_scale=conf_threshold_scale,
                        conf_mask_sharpness=conf_mask_sharpness,
                    )
                    esa_prior_region = prior_region_latent if bool(use_prior_region) else None
                    esa_edit_conf = edit_conf
                    if esa_ablation_mode == "confidence_only":
                        esa_prior_region = None
                    elif esa_ablation_mode == "prior_only":
                        esa_edit_conf = torch.zeros_like(edit_conf)
                    support_gate = self._compute_edit_support_gate(
                        edit_conf=esa_edit_conf,
                        prior_region=esa_prior_region,
                        esa_scale=cur_esa_scale,
                        prior_force=cur_prior_force,
                    )

                if flowtrack_enabled:
                    state_cost = None
                    if flowtrack_lambda > 0.0:
                        state_cost = self._resolve_flowtrack_state_cost(
                            reference_velocity,
                            flowtrack_lambda=flowtrack_lambda,
                            flowtrack_s_min=flowtrack_s_min,
                            flowtrack_state_mode=flowtrack_state_mode,
                        )
                    noise_pred, pre_control = self._solve_flowtrack_control(
                        reference_velocity,
                        prev_control=prev_pre_control,
                        flowtrack_lambda=flowtrack_lambda,
                        flowtrack_s_min=flowtrack_s_min,
                        flowtrack_state_mode=flowtrack_state_mode,
                        flowtrack_memory_mode=flowtrack_memory_mode,
                        state_cost=state_cost,
                        return_pre_control=True,
                    )
                    if bool(flowtrack_log_stats):
                        effective_step = int(i - int(skip_timesteps) + 1)
                        d_f = reference_velocity.to(dtype=torch.float32)
                        w_f = pre_control.to(dtype=torch.float32)
                        u_f = noise_pred.to(dtype=torch.float32)
                        lam = flowtrack_lambda
                        track = u_f - d_f
                        du_step = None if prev_executed_control is None else (
                            u_f - prev_executed_control.to(dtype=torch.float32)
                        )
                        flowtrack_stats["d_norm"] += float(d_f.square().sum().item())
                        flowtrack_stats["e_track"] += float(track.square().sum().item())
                        if prev_reference_velocity is not None:
                            prev_d_f = prev_reference_velocity.to(dtype=torch.float32)
                            prev_u_f = prev_executed_control.to(dtype=torch.float32)
                            dd = d_f - prev_d_f
                            du = u_f - prev_u_f
                            flowtrack_stats["v_d"] += float(dd.square().sum().item())
                            flowtrack_stats["v_u"] += float(du.square().sum().item())
                        if state_cost is not None:
                            a_f = state_cost.to(dtype=torch.float32)
                            flowtrack_stats["e_effort"] += float(
                                (a_f * u_f.square()).sum().item()
                            )
                            flowtrack_stats["a_mean"] += float(a_f.mean().item())
                            flowtrack_stats["a_count"] += 1
                            s_f = (1.0 + lam) / (1.0 + lam + a_f)
                            s_flat = s_f.flatten()
                            flowtrack_stats["s_mean"] += float(s_f.mean().item())
                            flowtrack_stats["s_q10"] += float(torch.quantile(s_flat, 0.10).item())
                            flowtrack_stats["s_q50"] += float(torch.quantile(s_flat, 0.50).item())
                            flowtrack_stats["s_q90"] += float(torch.quantile(s_flat, 0.90).item())
                            flowtrack_stats["s_min"] = min(
                                flowtrack_stats["s_min"],
                                float(s_f.min().item()),
                            )
                            flowtrack_stats["s_count"] += 1
                        if state_cost is not None:
                            a_f = state_cost.to(dtype=torch.float32)
                            effort_rms = float(
                                (a_f * u_f.square()).mean().sqrt().item()
                            )
                            a_mean = float(a_f.mean().item())
                            s_f = (1.0 + lam) / (1.0 + lam + a_f)
                            s_mean = float(s_f.mean().item())
                            s_flat = s_f.flatten()
                            s_q10 = float(torch.quantile(s_flat, 0.10).item())
                            s_q50 = float(torch.quantile(s_flat, 0.50).item())
                            s_q90 = float(torch.quantile(s_flat, 0.90).item())
                            s_min_obs = float(s_f.min().item())
                        else:
                            a_f = torch.zeros_like(u_f[:1], dtype=torch.float32)
                            effort_rms = 0.0
                            a_mean = 0.0
                            s_mean = 1.0
                            s_q10 = 1.0
                            s_q50 = 1.0
                            s_q90 = 1.0
                            s_min_obs = 1.0
                        if prev_executed_control is None:
                            du_rms = 0.0
                        else:
                            du_rms = float(du_step.square().mean().sqrt().item())
                        optimality = (1.0 + lam) * (u_f - w_f) + a_f * u_f
                        flowtrack_stats["r_opt"] += float(optimality.square().sum().item())
                        optimality_rms = float(optimality.square().mean().sqrt().item())
                        if effective_step == 1 or effective_step == total_edit_steps or (effective_step % 10) == 0:
                            logging.info(
                                "FlowTrack step %d/%d: lambda=%.4f "
                                "state_mode=%s memory_mode=%s "
                                "d_rms=%.4f w_rms=%.4f u_rms=%.4f track_rms=%.4f "
                                "du_rms=%.4f effort_rms=%.4f a_mean=%.4f "
                                "s_mean=%.4f s_q10=%.4f s_q50=%.4f s_q90=%.4f s_obs_min=%.4f "
                                "optimality_rms=%.4e",
                                effective_step,
                                total_edit_steps,
                                lam,
                                flowtrack_state_mode,
                                flowtrack_memory_mode,
                                float(d_f.square().mean().sqrt().item()),
                                float(w_f.square().mean().sqrt().item()),
                                float(u_f.square().mean().sqrt().item()),
                                float(track.square().mean().sqrt().item()),
                                du_rms,
                                effort_rms,
                                a_mean,
                                s_mean,
                                s_q10,
                                s_q50,
                                s_q90,
                                s_min_obs,
                                optimality_rms,
                            )
                elif bool(use_traj_prox):
                    if support_gate is None:
                        support_gate = torch.ones_like(noise_pred_candidate[:1])
                    pre_control, noise_pred = self._solve_causal_pre_execution_control(
                        noise_pred_candidate,
                        support_gate=support_gate,
                        prev_pre_control=prev_executed_control,
                        traj_lambda=traj_lambda,
                    )
                elif support_gate is not None:
                    noise_pred = noise_pred_candidate * support_gate.to(
                        device=noise_pred_candidate.device,
                        dtype=noise_pred_candidate.dtype,
                    )

                temp_x0 = sample_scheduler.step(
                    noise_pred.unsqueeze(0),
                    t,
                    mv_latent[0].unsqueeze(0),
                    return_dict=False,
                    generator=seed_g)[0]
                mv_latent = [temp_x0.squeeze(0)]
                if flowtrack_enabled:
                    prev_reference_velocity = reference_velocity.detach()
                    prev_pre_control = pre_control.detach()
                    prev_executed_control = noise_pred.detach()
                elif bool(use_traj_prox):
                    prev_executed_control = pre_control.detach()

            if flowtrack_enabled and bool(flowtrack_log_stats):
                eps = 1e-12
                rho_var = flowtrack_stats["v_u"] / (flowtrack_stats["v_d"] + eps)
                rho_track = flowtrack_stats["e_track"] / (flowtrack_stats["d_norm"] + eps)
                a_mean = (
                    flowtrack_stats["a_mean"] / max(1, int(flowtrack_stats["a_count"]))
                )
                s_count = int(flowtrack_stats["s_count"])
                if s_count > 0:
                    s_mean = flowtrack_stats["s_mean"] / s_count
                    s_q10 = flowtrack_stats["s_q10"] / s_count
                    s_q50 = flowtrack_stats["s_q50"] / s_count
                    s_q90 = flowtrack_stats["s_q90"] / s_count
                    s_min_obs = flowtrack_stats["s_min"]
                else:
                    s_mean = 1.0
                    s_q10 = 1.0
                    s_q50 = 1.0
                    s_q90 = 1.0
                    s_min_obs = 1.0
                logging.info(
                    "FlowTrack summary: lambda=%.4f state_mode=%s memory_mode=%s "
                    "V_d=%.6e V_u=%.6e "
                    "E_track=%.6e E_effort=%.6e R_opt=%.6e "
                    "rho_var=%.6f rho_track=%.6f a_mean=%.6f "
                    "s_mean=%.6f s_q10=%.6f s_q50=%.6f s_q90=%.6f s_obs_min=%.6f",
                    flowtrack_lambda,
                    flowtrack_state_mode,
                    flowtrack_memory_mode,
                    flowtrack_stats["v_d"],
                    flowtrack_stats["v_u"],
                    flowtrack_stats["e_track"],
                    flowtrack_stats["e_effort"],
                    flowtrack_stats["r_opt"],
                    rho_var,
                    rho_track,
                    a_mean,
                    s_mean,
                    s_q10,
                    s_q50,
                    s_q90,
                    s_min_obs,
                )
               
            x0 = mv_latent
            if offload_model:
                self.model.cpu()
            if self.rank == 0:
                videos = self.vae.decode(x0)

        del noise, latents
        del sample_scheduler
        if offload_model:
            gc.collect()
            torch.cuda.synchronize()
        if dist.is_initialized():
            dist.barrier()

        return videos[0] if self.rank == 0 else None
