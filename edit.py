import argparse
from datetime import datetime
import glob
import logging
import os
import sys
import warnings
import cv2
import json
import numpy as np
warnings.filterwarnings('ignore')

import torch, random
import torch.distributed as dist
from PIL import Image

import wan
from wan.configs import WAN_CONFIGS, SIZE_CONFIGS, MAX_AREA_CONFIGS, SUPPORTED_SIZES
from wan.utils.prompt_extend import DashScopePromptExpander, QwenPromptExpander
from wan.utils.utils import cache_video, cache_image, str2bool

EXAMPLE_PROMPT = {
    "t2v-1.3B": {
        "prompt": "Two anthropomorphic cats in comfy boxing gear and bright gloves fight intensely on a spotlighted stage.",
    },
}


def _validate_args(args):
    # Basic check
    assert args.ckpt_dir is not None, "Please specify the checkpoint directory."
    assert args.task in WAN_CONFIGS, f"Unsupport task: {args.task}"
    assert args.task in EXAMPLE_PROMPT, f"Unsupport task: {args.task}"

    # Standard FlowTrack setting for text-to-video editing.
    if args.sample_steps is None:
        args.sample_steps = 50

    if args.sample_shift is None:
        args.sample_shift = 5.0

    if args.frame_num is None:
        args.frame_num = 81

    args.base_seed = args.base_seed if args.base_seed >= 0 else random.randint(
        0, sys.maxsize)
    # Size check
    assert args.size in SUPPORTED_SIZES[
        args.
        task], f"Unsupport size {args.size} for task {args.task}, supported sizes are: {', '.join(SUPPORTED_SIZES[args.task])}"

    # Core method knobs: keep values in safe ranges.
    if args.use_flowtrack is None:
        args.use_flowtrack = bool(args.use_traj_prox)
    args.use_flowtrack = bool(args.use_flowtrack)
    if args.flowtrack_lambda is None:
        args.flowtrack_lambda = float(args.traj_lambda)
    args.flowtrack_lambda = float(max(0.0, float(args.flowtrack_lambda)))
    args.flowtrack_s_min = float(max(0.0, min(1.0, float(args.flowtrack_s_min))))
    args.flowtrack_state_mode = str(args.flowtrack_state_mode).lower()
    args.flowtrack_memory_mode = str(args.flowtrack_memory_mode).lower()
    if args.flowtrack_log_stats is None:
        args.flowtrack_log_stats = bool(args.traj_log_stats)
    args.flowtrack_log_stats = bool(args.flowtrack_log_stats)

    if args.use_flowtrack:
        # Use only the FlowTrack execution controller.
        args.use_prior_region = False
        args.use_esa = False

    args.region_guidance_out_mult = float(max(0.0, min(1.0, float(args.region_guidance_out_mult))))
    args.prior_force = float(max(0.0, min(1.0, float(args.prior_force))))
    args.esa_scale = float(max(0.0, min(1.0, float(args.esa_scale))))
    args.conf_threshold_scale = float(max(0.0, float(args.conf_threshold_scale)))
    args.conf_mask_sharpness = float(max(1e-3, float(args.conf_mask_sharpness)))
    args.phase_switch_ratio = float(max(0.0, min(1.0, float(args.phase_switch_ratio))))
    args.traj_lambda = float(max(0.0, float(args.traj_lambda)))
    args.prior_region_dilate = int(max(0, int(args.prior_region_dilate)))
    args.prior_region_temporal = int(max(0, int(args.prior_region_temporal)))
    if args.tgt_guide_scale_late is not None:
        args.tgt_guide_scale_late = float(args.tgt_guide_scale_late)
    if args.region_guidance_out_mult_late is not None:
        args.region_guidance_out_mult_late = float(
            max(0.0, min(1.0, float(args.region_guidance_out_mult_late))))
    if args.esa_scale_late is not None:
        args.esa_scale_late = float(
            max(0.0, min(1.0, float(args.esa_scale_late))))
    if args.prior_force_late is not None:
        args.prior_force_late = float(max(0.0, min(1.0, float(args.prior_force_late))))
    args.start_index = int(max(0, int(args.start_index)))
    if args.max_items is not None:
        args.max_items = int(args.max_items)
    args.num_shards = int(max(1, int(args.num_shards)))
    args.shard_id = int(max(0, int(args.shard_id)))
    if args.shard_id >= args.num_shards:
        raise ValueError("shard_id must be in [0, num_shards).")
    if getattr(args, "log_file", None):
        args.log_file = os.path.expanduser(str(args.log_file))


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Run FlowTrack video editing with a Wan text-to-video model."
    )
    parser.add_argument(
        "--task",
        type=str,
        default="t2v-1.3B",
        choices=list(WAN_CONFIGS.keys()),
        help="Model configuration to use.")
    parser.add_argument(
        "--size",
        type=str,
        default="1280*720",
        choices=list(SIZE_CONFIGS.keys()),
        help="Output size for single-video editing."
    )
    parser.add_argument(
        "--frame_num",
        type=int,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--ckpt_dir",
        type=str,
        default=None,
        help="The path to the checkpoint directory.")
    parser.add_argument(
        "--offload_model",
        type=str2bool,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--ulysses_size",
        type=int,
        default=1,
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--ring_size",
        type=int,
        default=1,
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--t5_fsdp",
        action="store_true",
        default=False,
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--t5_cpu",
        action="store_true",
        default=False,
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--dit_fsdp",
        action="store_true",
        default=False,
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--data_dir",
        type=str,
        default="data",
        help="Directory containing source videos.")
    parser.add_argument(
        "--save_dir",
        type=str,
        default="outputs",
        help="Directory for edited videos.")
    parser.add_argument(
        "--save_file",
        type=str,
        default=None,
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--log_file",
        type=str,
        default=None,
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Source prompt for single-video editing.")
    parser.add_argument(
        "--tgt_prompt",
        type=str,
        default=None,
        help="Target prompt for single-video editing.")
    parser.add_argument(
        "--use_prompt_extend",
        action="store_true",
        default=False,
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--prompt_extend_method",
        type=str,
        default="local_qwen",
        choices=["dashscope", "local_qwen"],
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--prompt_extend_model",
        type=str,
        default=None,
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--prompt_extend_target_lang",
        type=str,
        default="ch",
        choices=["ch", "en"],
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--base_seed",
        type=int,
        default=-1,
        help="Random seed. If negative, a random seed is used.")
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--sample_solver",
        type=str,
        default='unipc',
        choices=['unipc', 'dpm++'],
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--sample_steps", type=int, default=None, help="Number of sampling steps.")
    parser.add_argument(
        "--sample_shift",
        type=float,
        default=None,
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--sample_guide_scale",
        type=float,
        default=5.0,
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--tgt_guide_scale",
        type=float,
        default=10.0,
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--skip_timesteps",
        type=int,
        default=16,
        help=argparse.SUPPRESS)
    parser.add_argument(
        "--use_prior_region",
        type=str2bool,
        default=False,
        help="Legacy prior-region execution layer. Disabled for FlowTrack.",
    )
    parser.add_argument(
        "--prior_region_root",
        type=str,
        default="",
        help="Root folder of prior masks, expected layout: <root>/<video_name>/*.png|jpg",
    )
    parser.add_argument(
        "--prior_region_dilate",
        type=int,
        default=1,
        help="Spatial dilation radius for prior region on latent grid.",
    )
    parser.add_argument(
        "--prior_region_temporal",
        type=int,
        default=0,
        help="Temporal dilation radius for prior region on latent grid.",
    )
    parser.add_argument(
        "--region_guidance_out_mult",
        type=float,
        default=1.0,
        help="Legacy outside-region guidance multiplier. FlowTrack uses 1.0.",
    )
    parser.add_argument(
        "--prior_force",
        type=float,
        default=0.0,
        help="Legacy prior support strength. Ignored by FlowTrack.",
    )
    parser.add_argument(
        "--esa_ablation_mode",
        type=str,
        default="full",
        choices=["full", "confidence_only", "prior_only"],
        help="ESA mechanism ablation mode: full prior+confidence fusion, confidence-only gating, or prior-only gating.",
    )
    parser.add_argument(
        "--use_esa",
        type=str2bool,
        default=False,
        help="Legacy edit-support arbitration. Disabled for FlowTrack.",
    )
    parser.add_argument(
        "--esa_scale",
        type=float,
        default=0.9,
        help="Overall ESA gate strength alpha_esa (0..1).",
    )
    parser.add_argument(
        "--conf_threshold_scale",
        type=float,
        default=1.0,
        help="Threshold scale for internal edit confidence.",
    )
    parser.add_argument(
        "--conf_mask_sharpness",
        type=float,
        default=15.0,
        help="Sigmoid sharpness for internal edit confidence.",
    )
    parser.add_argument(
        "--phase_switch_ratio",
        type=float,
        default=0.5,
        help="Two-phase switch ratio on effective edit steps (0..1).",
    )
    parser.add_argument(
        "--tgt_guide_scale_late",
        type=float,
        default=None,
        help="Optional late-phase tgt_guide_scale; use base value if unset.",
    )
    parser.add_argument(
        "--region_guidance_out_mult_late",
        type=float,
        default=None,
        help="Optional late-phase outside-prior CFG multiplier; use base value if unset.",
    )
    parser.add_argument(
        "--esa_scale_late",
        type=float,
        default=None,
        help="Optional late-phase esa_scale; use base value if unset.",
    )
    parser.add_argument(
        "--prior_force_late",
        type=float,
        default=None,
        help="Optional late-phase prior_force; use base value if unset.",
    )
    parser.add_argument(
        "--use_traj_prox",
        type=str2bool,
        default=True,
        help="Legacy alias for --use_flowtrack when --use_flowtrack is unset.",
    )
    parser.add_argument(
        "--traj_lambda",
        type=float,
        default=0.20,
        help="Legacy alias for --flowtrack_lambda when --flowtrack_lambda is unset.",
    )
    parser.add_argument(
        "--traj_log_stats",
        type=str2bool,
        default=False,
        help="Legacy alias for --flowtrack_log_stats when --flowtrack_log_stats is unset.",
    )
    parser.add_argument(
        "--use_flowtrack",
        type=str2bool,
        default=None,
        help="Enable FlowTrack causal execution control. If unset, follows --use_traj_prox.",
    )
    parser.add_argument(
        "--flowtrack_lambda",
        type=float,
        default=0.20,
        help="FlowTrack memory strength lambda >= 0.",
    )
    parser.add_argument(
        "--flowtrack_s_min",
        type=float,
        default=0.0,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--flowtrack_state_mode",
        type=str,
        default="otsu",
        choices=["otsu", "none", "uniform"],
        help="FlowTrack state-cost ablation: otsu=default pointwise cost, none=no state cost, uniform=spatially uniform cost.",
    )
    parser.add_argument(
        "--flowtrack_memory_mode",
        type=str,
        default="pre",
        choices=["pre", "none"],
        help="FlowTrack memory ablation: pre=default pre-execution recursion, none=execute current reference without temporal memory.",
    )
    parser.add_argument(
        "--flowtrack_log_stats",
        type=str2bool,
        default=None,
        help="Log FlowTrack V_d, V_u, E_track, rho_var, and rho_track diagnostics.",
    )
    
    # FiVE
    parser.add_argument(
        "--video_dir",
        type=str,
        default="data")
    parser.add_argument(
        "--video_name",
        type=str,
        default=None)
    parser.add_argument(
        "--FiVE_dataset_json",
        type=str,
        default=None,
        help="dataset json: data_FiVE/edit_prompt/edit1_FiVE.json, including src, tgt promts")
    parser.add_argument(
        "--video_names",
        type=str,
        default="",
        help="Comma-separated FiVE video_name filter, e.g. '0001_bus,0014_burnout'",
    )
    parser.add_argument(
        "--indices",
        type=str,
        default="",
        help="Comma-separated 0-based indices after video_names filtering.",
    )
    parser.add_argument(
        "--start_index",
        type=int,
        default=0,
        help="Start index after video_names/indices filtering.",
    )
    parser.add_argument(
        "--max_items",
        type=int,
        default=None,
        help="Keep only first N entries after filtering.",
    )
    parser.add_argument(
        "--num_shards",
        type=int,
        default=1,
        help="Shard count for FiVE loop.",
    )
    parser.add_argument(
        "--shard_id",
        type=int,
        default=0,
        help="Current shard id in [0, num_shards).",
    )
    parser.add_argument(
        "--eval_gpu_time",
        type=bool,
        default=False,
        help="if enable, it will be used to test GPU memory and running time.")

    args = parser.parse_args()

    _validate_args(args)

    return args


def _init_logging(rank, log_file=None):
    # logging
    if rank == 0:
        handlers = [logging.StreamHandler(stream=sys.stdout)]
        if log_file:
            log_dir = os.path.dirname(os.path.abspath(log_file))
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            handlers.append(logging.FileHandler(log_file, mode="a", encoding="utf-8"))
        # set format
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] %(levelname)s: %(message)s",
            handlers=handlers,
            force=True)
        if log_file:
            logging.info("Saving runtime log to %s", log_file)
    else:
        logging.basicConfig(level=logging.ERROR, force=True)

def _get_video_meta_cv2(video_path: str):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    return width, height, fps, frame_count


def _pad_to_4n1(frame_num: int) -> int:
    """
    Wan VAE expects 4n+1 frames to avoid dropping tail frames.
    We pad by repeating the last frame if needed.
    """
    if frame_num <= 0:
        return frame_num
    if (frame_num - 1) % 4 == 0:
        return frame_num
    n = (frame_num - 1) // 4 + 1
    return 4 * n + 1


def _resolve_prior_region_root(args):
    if not bool(getattr(args, "use_prior_region", False)):
        return None

    candidates = []
    if getattr(args, "prior_region_root", None):
        candidates.append(os.path.expanduser(str(args.prior_region_root)))

    if getattr(args, "FiVE_dataset_json", None):
        candidates.append(
            os.path.abspath(
                os.path.join(
                    os.path.dirname(os.path.expanduser(str(args.FiVE_dataset_json))),
                    "..",
                    "bmasks",
                )
            )
        )

    if getattr(args, "data_dir", None):
        candidates.append(
            os.path.abspath(
                os.path.join(
                    os.path.expanduser(str(args.data_dir)),
                    "..",
                    "bmasks",
                )
            )
        )

    seen = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        if os.path.isdir(c):
            return c
    return None


def _load_prior_region_mask(
    prior_region_root: str,
    video_name: str,
    frame_num: int,
    target_size,
):
    """Load pixel-space prior region mask as tensor [1,T,H,W]."""
    if prior_region_root is None or str(prior_region_root).strip() == "":
        return None

    mask_dir = os.path.join(str(prior_region_root), str(video_name))
    if not os.path.isdir(mask_dir):
        return None

    files = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        files.extend(glob.glob(os.path.join(mask_dir, ext)))
    files = sorted(files)
    if not files:
        return None

    target_w, target_h = int(target_size[0]), int(target_size[1])
    frame_num = int(max(1, frame_num))
    src_len = len(files)
    out_masks = []
    last_valid = None

    for t in range(frame_num):
        if frame_num <= 1:
            idx = 0
        else:
            idx = int(round(t * (src_len - 1) / (frame_num - 1)))
        idx = max(0, min(src_len - 1, idx))

        m = cv2.imread(files[idx], cv2.IMREAD_GRAYSCALE)
        if m is None:
            if last_valid is None:
                m = np.zeros((target_h, target_w), dtype=np.float32)
            else:
                m = last_valid.copy()
        else:
            if (m.shape[1], m.shape[0]) != (target_w, target_h):
                m = cv2.resize(m, (target_w, target_h), interpolation=cv2.INTER_NEAREST)
            m = (m > 0).astype(np.float32)
            last_valid = m

        out_masks.append(m)

    prior = np.stack(out_masks, axis=0)  # [T,H,W]
    return torch.from_numpy(prior)[None]  # [1,T,H,W]


def _video_name_from_path(video_path: str) -> str:
    base = os.path.basename(str(video_path).rstrip("/"))
    stem, ext = os.path.splitext(base)
    return stem if ext != "" else base


def _parse_csv_list(s):
    if s is None:
        return []
    return [p.strip() for p in str(s).split(",") if p.strip() != ""]


def _parse_int_csv(s):
    out = []
    for p in _parse_csv_list(s):
        try:
            out.append(int(p))
        except Exception:
            continue
    return out


def _filter_five_entries(entries, args):
    out = list(entries)

    vns = set(_parse_csv_list(getattr(args, "video_names", "")))
    if len(vns) > 0:
        out = [e for e in out if str(e.get("video_name", "")) in vns]

    idxs = _parse_int_csv(getattr(args, "indices", ""))
    if len(idxs) > 0:
        out = [out[i] for i in idxs if 0 <= i < len(out)]

    start_index = int(getattr(args, "start_index", 0))
    if start_index > 0:
        out = out[start_index:] if start_index < len(out) else []

    max_items = getattr(args, "max_items", None)
    if (max_items is not None) and (int(max_items) > 0):
        out = out[: int(max_items)]

    num_shards = int(getattr(args, "num_shards", 1))
    shard_id = int(getattr(args, "shard_id", 0))
    if num_shards > 1:
        out = [e for i, e in enumerate(out) if (i % num_shards) == shard_id]

    return out


def load_frames(video_path=None, num_frames=41, target_size=(832, 480)):
    # Open video file
    cap = cv2.VideoCapture(video_path)
    # Check if video is successfully opened
    if not cap.isOpened():
        raise ValueError("Cannot open video file")
    frames = []
    # Read first num_frames frames
    for i in range(num_frames):
        ret, frame = cap.read()
        # If video ends, exit loop early
        if not ret:
            break
        # Resize frame (optional)
        if target_size is not None:
            resized_frame = cv2.resize(frame, target_size)
        else:
            resized_frame = frame
        # Convert frame from BGR to RGB
        resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
        # Convert frame to tensor and normalize [-1, 1]
        tensor_frame = torch.tensor(resized_frame).permute(2, 0, 1).float() / 255.0
        tensor_frame = 2 * tensor_frame - 1
        # Add to frame list
        frames.append(tensor_frame)
    # Release video object
    cap.release()
    # Stack frame list into tensor
    if frames:
        frames_tensor = torch.stack(frames).permute(1,0,2,3)
    else:
        raise ValueError("Video does not have enough frames")
    return frames_tensor.unsqueeze(0)

def load_frames_path(video_path=None, num_frames=41, target_size=(832, 480)):
    frame_files = sorted(os.listdir(video_path))  # Get and sort frame filenames
    frame_files = [f for f in frame_files if f.endswith('.jpg') or f.endswith('.png')]  # Ensure only .jpg and .png files are selected

    frames = []
    for i in range(min(num_frames, len(frame_files))):  # Read specified number of frames in order
        frame_path = os.path.join(video_path, frame_files[i])
        
        # Use OpenCV to read image
        frame = cv2.imread(frame_path)
        if frame is None:
            logging.warning("Cannot read image: %s", frame_path)
            continue
        
        # Convert BGR to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # resize image (optional)
        if target_size is not None:
            frame = cv2.resize(frame, target_size)
        
        # Convert to float and normalize to [-1, 1]
        frame = 2 * frame.astype(np.float32) / 255.0 - 1
        
        # Adjust dimension order to [C, H, W]
        frame = np.transpose(frame, (2, 0, 1))
        
        frames.append(frame)

    # Convert frame list to tensor
    frames_tensor = torch.tensor(np.array(frames)).float()
    frames_tensor = frames_tensor.permute(1,0,2,3).unsqueeze(0)
    return frames_tensor


def generate(args):
    rank = int(os.getenv("RANK", 0))
    world_size = int(os.getenv("WORLD_SIZE", 1))
    local_rank = int(os.getenv("LOCAL_RANK", 0))
    device = local_rank
    _init_logging(rank, args.log_file)

    if args.video_path.endswith('.mp4'):
        video = load_frames(args.video_path)
    elif os.path.isdir(args.video_path):
        video = load_frames_path(args.video_path)
    else:
        raise ValueError(f"Invalid video path: {args.video_path}")

    if args.offload_model is None:
        args.offload_model = False if world_size > 1 else True
        logging.info(
            f"offload_model is not specified, set to {args.offload_model}.")
    if world_size > 1:
        torch.cuda.set_device(local_rank)
        dist.init_process_group(
            backend="nccl",
            init_method="env://",
            rank=rank,
            world_size=world_size)
    else:
        assert not (
            args.t5_fsdp or args.dit_fsdp
        ), f"t5_fsdp and dit_fsdp are not supported in non-distributed environments."
        assert not (
            args.ulysses_size > 1 or args.ring_size > 1
        ), f"context parallel are not supported in non-distributed environments."

    if args.ulysses_size > 1 or args.ring_size > 1:
        assert args.ulysses_size * args.ring_size == world_size, f"The number of ulysses_size and ring_size should be equal to the world size."
        from xfuser.core.distributed import (initialize_model_parallel,
                                             init_distributed_environment)
        init_distributed_environment(
            rank=dist.get_rank(), world_size=dist.get_world_size())

        initialize_model_parallel(
            sequence_parallel_degree=dist.get_world_size(),
            ring_degree=args.ring_size,
            ulysses_degree=args.ulysses_size,
        )

    if args.use_prompt_extend:
        if args.prompt_extend_method == "dashscope":
            prompt_expander = DashScopePromptExpander(
                model_name=args.prompt_extend_model, is_vl="i2v" in args.task)
        elif args.prompt_extend_method == "local_qwen":
            prompt_expander = QwenPromptExpander(
                model_name=args.prompt_extend_model,
                is_vl="i2v" in args.task,
                device=rank)
        else:
            raise NotImplementedError(
                f"Unsupport prompt_extend_method: {args.prompt_extend_method}")

    cfg = WAN_CONFIGS[args.task]
    if args.ulysses_size > 1:
        assert cfg.num_heads % args.ulysses_size == 0, f"`num_heads` must be divisible by `ulysses_size`."

    logging.info(f"Generation job args: {args}")
    logging.info(f"Generation model config: {cfg}")

    if dist.is_initialized():
        base_seed = [args.base_seed] if rank == 0 else [None]
        dist.broadcast_object_list(base_seed, src=0)
        args.base_seed = base_seed[0]

    if "t2v" in args.task or "t2i" in args.task:
        if args.prompt is None:
            args.prompt = EXAMPLE_PROMPT[args.task]["prompt"]
        logging.info(f"Input prompt: {args.prompt}")
        if args.use_prompt_extend:
            logging.info("Extending prompt ...")
            if rank == 0:
                prompt_output = prompt_expander(
                    args.prompt,
                    tar_lang=args.prompt_extend_target_lang,
                    seed=args.base_seed)
                if prompt_output.status == False:
                    logging.info(
                        f"Extending prompt failed: {prompt_output.message}")
                    logging.info("Falling back to original prompt.")
                    input_prompt = args.prompt
                else:
                    input_prompt = prompt_output.prompt
                input_prompt = [input_prompt]
            else:
                input_prompt = [None]
            if dist.is_initialized():
                dist.broadcast_object_list(input_prompt, src=0)
            args.prompt = input_prompt[0]
            logging.info(f"Extended prompt: {args.prompt}")

        logging.info("Creating WanT2V pipeline.")
        wan_t2v = wan.WanT2V(
            config=cfg,
            checkpoint_dir=args.ckpt_dir,
            device_id=device,
            rank=rank,
            t5_fsdp=args.t5_fsdp,
            dit_fsdp=args.dit_fsdp,
            use_usp=(args.ulysses_size > 1 or args.ring_size > 1),
            t5_cpu=args.t5_cpu,
        )

        logging.info(
            f"Generating {'image' if 't2i' in args.task else 'video'} ...")

        prior_region_mask = None
        prior_region_root = _resolve_prior_region_root(args)
        if bool(args.use_prior_region):
            if prior_region_root is None:
                logging.warning("use_prior_region=True but no valid prior_region_root found. Continue without prior mask.")
            else:
                video_name = _video_name_from_path(args.video_path)
                prior_region_mask = _load_prior_region_mask(
                    prior_region_root=prior_region_root,
                    video_name=video_name,
                    frame_num=min(args.frame_num, int(video.shape[2])),
                    target_size=SIZE_CONFIGS[args.size],
                )
                if prior_region_mask is None:
                    logging.warning(
                        "Prior mask not found for video_name=%s under %s. Continue without prior mask.",
                        video_name,
                        prior_region_root,
                    )

        video = wan_t2v.edit(
            video,
            args.prompt,
            args.tgt_prompt,
            size=SIZE_CONFIGS[args.size],
            frame_num=min(args.frame_num, video.shape[2]),
            shift=args.sample_shift,
            sample_solver=args.sample_solver,
            sampling_steps=args.sample_steps,
            guide_scale=args.sample_guide_scale,
            tgt_guide_scale=args.tgt_guide_scale,
            skip_timesteps=args.skip_timesteps,
            use_prior_region=args.use_prior_region,
            prior_region_mask=prior_region_mask,
            prior_region_dilate=args.prior_region_dilate,
            prior_region_temporal=args.prior_region_temporal,
            region_guidance_out_mult=args.region_guidance_out_mult,
            use_esa=args.use_esa,
            esa_scale=args.esa_scale,
            conf_threshold_scale=args.conf_threshold_scale,
            conf_mask_sharpness=args.conf_mask_sharpness,
            prior_force=args.prior_force,
            esa_ablation_mode=args.esa_ablation_mode,
            phase_switch_ratio=args.phase_switch_ratio,
            tgt_guide_scale_late=args.tgt_guide_scale_late,
            region_guidance_out_mult_late=args.region_guidance_out_mult_late,
            esa_scale_late=args.esa_scale_late,
            prior_force_late=args.prior_force_late,
            use_traj_prox=args.use_traj_prox,
            traj_lambda=args.traj_lambda,
            traj_log_stats=args.traj_log_stats,
            use_flowtrack=args.use_flowtrack,
            flowtrack_lambda=args.flowtrack_lambda,
            flowtrack_s_min=args.flowtrack_s_min,
            flowtrack_state_mode=args.flowtrack_state_mode,
            flowtrack_memory_mode=args.flowtrack_memory_mode,
            flowtrack_log_stats=args.flowtrack_log_stats,
            seed=args.base_seed,
            offload_model=args.offload_model)
        
    else:
        if args.prompt is None:
            args.prompt = EXAMPLE_PROMPT[args.task]["prompt"]
        if args.image is None:
            args.image = EXAMPLE_PROMPT[args.task]["image"]
        logging.info(f"Input prompt: {args.prompt}")
        logging.info(f"Input image: {args.image}")

        img = Image.open(args.image).convert("RGB")
        if args.use_prompt_extend:
            logging.info("Extending prompt ...")
            if rank == 0:
                prompt_output = prompt_expander(
                    args.prompt,
                    tar_lang=args.prompt_extend_target_lang,
                    image=img,
                    seed=args.base_seed)
                if prompt_output.status == False:
                    logging.info(
                        f"Extending prompt failed: {prompt_output.message}")
                    logging.info("Falling back to original prompt.")
                    input_prompt = args.prompt
                else:
                    input_prompt = prompt_output.prompt
                input_prompt = [input_prompt]
            else:
                input_prompt = [None]
            if dist.is_initialized():
                dist.broadcast_object_list(input_prompt, src=0)
            args.prompt = input_prompt[0]
            logging.info(f"Extended prompt: {args.prompt}")

        logging.info("Creating WanI2V pipeline.")
        wan_i2v = wan.WanI2V(
            config=cfg,
            checkpoint_dir=args.ckpt_dir,
            device_id=device,
            rank=rank,
            t5_fsdp=args.t5_fsdp,
            dit_fsdp=args.dit_fsdp,
            use_usp=(args.ulysses_size > 1 or args.ring_size > 1),
            t5_cpu=args.t5_cpu,
        )

        logging.info("Generating video ...")
        video = wan_i2v.generate(
            args.prompt,
            img,
            max_area=MAX_AREA_CONFIGS[args.size],
            frame_num=args.frame_num,
            shift=args.sample_shift,
            sample_solver=args.sample_solver,
            sampling_steps=args.sample_steps,
            guide_scale=args.sample_guide_scale,
            seed=args.base_seed,
            offload_model=args.offload_model)

    if rank == 0:
        if args.save_file is None:
            formatted_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            formatted_prompt = args.prompt.replace(" ", "_").replace("/",
                                                                     "_")[:50]
            suffix = '.png' if "t2i" in args.task else '.mp4'
            args.save_file = f"{args.task}_{args.size}_{args.ulysses_size}_{args.ring_size}_{formatted_prompt}_{formatted_time}" + suffix

        if "t2i" in args.task:
            logging.info(f"Saving generated image to {args.save_file}")
            cache_image(
                tensor=video.squeeze(1)[None],
                save_file=args.save_file,
                nrow=1,
                normalize=True,
                value_range=(-1, 1))
        else:
            logging.info(f"Saving generated video to {args.save_file}")
            cache_video(
                tensor=video[None],
                save_file=args.save_file,
                fps=cfg.sample_fps,
                nrow=1,
                normalize=True,
                value_range=(-1, 1))
    logging.info("Finished.")


if __name__ == "__main__":
    args = _parse_args()

    if args.FiVE_dataset_json is None:
        args.video_path = os.path.join(
            args.video_dir,
            args.video_name
        )
        generate(args)

    else:
        with open(args.FiVE_dataset_json, 'r') as file:
            data = json.load(file)
        if not isinstance(data, list):
            raise ValueError(f"FiVE_dataset_json must be a list: {args.FiVE_dataset_json}")

        raw_count = len(data)
        data = _filter_five_entries(data, args)
        filtered_count = len(data)

        # Ensure args.save_dir exists for per-run artifacts (e.g. memory_stats.txt)
        os.makedirs(args.save_dir, exist_ok=True)

        rank = int(os.getenv("RANK", 0))
        world_size = int(os.getenv("WORLD_SIZE", 1))
        local_rank = int(os.getenv("LOCAL_RANK", 0))
        device = local_rank
        _init_logging(rank, args.log_file)

        # One-time pipeline init (avoid re-loading weights for every video)
        if args.offload_model is None:
            args.offload_model = False if world_size > 1 else True
            logging.info(
                f"offload_model is not specified, set to {args.offload_model}.")

        if world_size > 1:
            torch.cuda.set_device(local_rank)
            dist.init_process_group(
                backend="nccl",
                init_method="env://",
                rank=rank,
                world_size=world_size)
        else:
            assert not (
                args.t5_fsdp or args.dit_fsdp
            ), f"t5_fsdp and dit_fsdp are not supported in non-distributed environments."
            assert not (
                args.ulysses_size > 1 or args.ring_size > 1
            ), f"context parallel are not supported in non-distributed environments."

        cfg = WAN_CONFIGS[args.task]
        logging.info("Creating WanT2V pipeline (single init for FiVE dataset loop).")
        wan_t2v = wan.WanT2V(
            config=cfg,
            checkpoint_dir=args.ckpt_dir,
            device_id=device,
            rank=rank,
            t5_fsdp=args.t5_fsdp,
            dit_fsdp=args.dit_fsdp,
            use_usp=(args.ulysses_size > 1 or args.ring_size > 1),
            t5_cpu=args.t5_cpu,
        )
        prior_region_root = _resolve_prior_region_root(args)
        if bool(args.use_prior_region):
            if prior_region_root is None:
                logging.warning("use_prior_region=True but no valid prior_region_root found. Continue without prior mask.")
            else:
                logging.info(f"Using prior_region_root: {prior_region_root}")

        logging.info(
            "FiVE entries: raw=%d filtered=%d video_names='%s' indices='%s' start_index=%d max_items=%s num_shards=%d shard_id=%d",
            raw_count,
            filtered_count,
            str(args.video_names),
            str(args.indices),
            int(args.start_index),
            str(args.max_items),
            int(args.num_shards),
            int(args.shard_id),
        )
        if filtered_count <= 0:
            logging.warning("No FiVE entries left after filtering. Exit.")
            sys.exit(0)

        # GPU/Speed
        import psutil, time
        if args.eval_gpu_time:
            data = data[:1]
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / (1024 ** 2)  
        start_time = time.time()

        filed_videos = []
        num_videos = len(data)
        for vid, entry in enumerate(data):
            video_name = entry["video_name"]
            logging.info("Processing %d/%d video: %s ...", vid, num_videos, video_name)

            args.prompt = entry["source_prompt"]
            args.tgt_prompt = entry["target_prompt"]
            args.video_path = os.path.join(
                args.data_dir, 
                entry["video_name"]+'.mp4'
            )
            type_idx = args.FiVE_dataset_json.split('/')[-1].split('_')[0].replace("edit", "")
            args.save_file = os.path.join(
                args.save_dir, 
                entry["video_name"],
                type_idx + '_' + entry["target_prompt"][:20]+'.mp4'
            )

            if os.path.exists(args.save_file):
                logging.info("The video has been edited. Skip %s", args.save_file)
                continue

            try: 
                # --- Use original video FPS / resolution / frame count ---
                w, h, fps, frame_count = _get_video_meta_cv2(args.video_path)
                if frame_count <= 0:
                    # Fallback: best-effort using requested frame_num
                    frame_count = int(args.frame_num) if args.frame_num is not None else 81
                if fps is None or fps <= 0:
                    fps = float(cfg.sample_fps)

                # Make sure spatial dims are compatible with the model (divisible by 16).
                # If not, round down to the nearest multiple to avoid shape mismatches.
                if w % 16 != 0 or h % 16 != 0:
                    w2 = (w // 16) * 16
                    h2 = (h // 16) * 16
                    logging.warning(
                        f"Video size {w}x{h} is not divisible by 16; resizing to {w2}x{h2} for model compatibility."
                    )
                    w, h = w2, h2

                # Pad to 4n+1 for the model, but crop back to original frame_count when saving.
                model_frame_num = _pad_to_4n1(frame_count)

                video = load_frames(
                    args.video_path,
                    num_frames=frame_count,
                    # Keep original resolution when possible; if we had to adjust
                    # to a multiple-of-16 size, this will resize accordingly.
                    target_size=(w, h),
                )
                if video.shape[2] < model_frame_num:
                    # Repeat last frame to pad.
                    last = video[:, :, -1:, :, :].repeat(1, 1, model_frame_num - video.shape[2], 1, 1)
                    video = torch.cat([video, last], dim=2)

                prior_region_mask = None
                if bool(args.use_prior_region) and prior_region_root is not None:
                    prior_region_mask = _load_prior_region_mask(
                        prior_region_root=prior_region_root,
                        video_name=video_name,
                        frame_num=model_frame_num,
                        target_size=(w, h),
                    )
                    if prior_region_mask is None:
                        logging.warning(
                            "Prior mask not found for %s under %s. Continue without prior mask.",
                            video_name,
                            prior_region_root,
                        )

                edited = wan_t2v.edit(
                    video,
                    args.prompt,
                    args.tgt_prompt,
                    size=(w, h),
                    frame_num=model_frame_num,
                    shift=args.sample_shift,
                    sample_solver=args.sample_solver,
                    sampling_steps=args.sample_steps,
                    guide_scale=args.sample_guide_scale,
                    tgt_guide_scale=args.tgt_guide_scale,
                    skip_timesteps=args.skip_timesteps,
                    use_prior_region=args.use_prior_region,
                    prior_region_mask=prior_region_mask,
                    prior_region_dilate=args.prior_region_dilate,
                    prior_region_temporal=args.prior_region_temporal,
                    region_guidance_out_mult=args.region_guidance_out_mult,
                    use_esa=args.use_esa,
                    esa_scale=args.esa_scale,
                    conf_threshold_scale=args.conf_threshold_scale,
                    conf_mask_sharpness=args.conf_mask_sharpness,
                    prior_force=args.prior_force,
                    esa_ablation_mode=args.esa_ablation_mode,
                    phase_switch_ratio=args.phase_switch_ratio,
                    tgt_guide_scale_late=args.tgt_guide_scale_late,
                    region_guidance_out_mult_late=args.region_guidance_out_mult_late,
                    esa_scale_late=args.esa_scale_late,
                    prior_force_late=args.prior_force_late,
                    use_traj_prox=args.use_traj_prox,
                    traj_lambda=args.traj_lambda,
                    traj_log_stats=args.traj_log_stats,
                    use_flowtrack=args.use_flowtrack,
                    flowtrack_lambda=args.flowtrack_lambda,
                    flowtrack_s_min=args.flowtrack_s_min,
                    flowtrack_state_mode=args.flowtrack_state_mode,
                    flowtrack_memory_mode=args.flowtrack_memory_mode,
                    flowtrack_log_stats=args.flowtrack_log_stats,
                    seed=args.base_seed,
                    offload_model=args.offload_model,
                )

                if edited is None:
                    raise RuntimeError("WanT2V.edit returned None")

                # Crop back to the original frame count (e.g., 80) after 4n+1 padding.
                edited = edited[:, :frame_count, :, :]

                logging.info(f"Saving generated video to {args.save_file}")
                cache_video(
                    tensor=edited[None],
                    save_file=args.save_file,
                    fps=fps,
                    nrow=1,
                    normalize=True,
                    value_range=(-1, 1),
                )
            except Exception as e:
                # Keep skipping failed items while preserving the full traceback in the run log.
                logging.exception("Failed to process video index=%d name=%s", vid, video_name)
                filed_videos.append(vid)
                continue

        # save GPU Memory / Speed
        running_time = time.time() - start_time
        max_cpu_memory = process.memory_info().rss / (1024 ** 2)  # to MB

        if torch.cuda.is_available():
            peak_gpu_memory = torch.cuda.max_memory_allocated(device="cuda") / (1024 ** 2)  # to MB
        else:
            peak_gpu_memory = 0.0  

        os.makedirs(args.save_dir, exist_ok=True)
        with open(f"{args.save_dir}/memory_stats.txt", "a") as f:
            f.write(f"FlowTrack: Max CPU Memory Usage: {max_cpu_memory:.2f} MB\n")
            f.write(f"FlowTrack: Peak GPU Memory Usage: {peak_gpu_memory:.2f} MB\n")
            f.write(f"FlowTrack: Running Time: {running_time:.2f} seconds\n\n")

        logging.info("Max CPU Memory Usage: %.2f MB", max_cpu_memory)
        logging.info("Peak GPU Memory Usage: %.2f MB", peak_gpu_memory)
        logging.info("Running Time: %.2f seconds", running_time)

        logging.info("failed videos: %s", filed_videos)
