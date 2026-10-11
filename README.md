# FlowTrack

### Controlling Edit-Signal Execution in Inversion-Free Flow Video Editing

[Project page](https://crychic-sakiko-togawa-214.github.io/FlowTrack/) ·
[Code](https://github.com/CRYCHIC-Sakiko-Togawa-214/FlowTrack)

FlowTrack is a training-free, inversion-free video editing method built on Wan2.1.
It carries the edit signal across denoising steps and uses a support-aware execution
cost to control where that signal is applied.

This repository contains the method implementation and inference entry point.

## Installation

Use Python 3.10+ on Linux with an NVIDIA GPU. Create an environment, install a
CUDA-compatible PyTorch/torchvision pair from [PyTorch](https://pytorch.org/get-started/locally/),
then install the remaining dependencies:

```bash
git clone --depth 1 https://github.com/CRYCHIC-Sakiko-Togawa-214/FlowTrack.git
cd FlowTrack
conda create -n flowtrack python=3.11 -y
conda activate flowtrack
# Install matching CUDA-enabled torch and torchvision for your machine.
pip install -r requirements.txt
```

The supported model is **Wan2.1 T2V 1.3B**. Download the checkpoint from
[Wan-AI/Wan2.1-T2V-1.3B](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B) and retain
its original directory layout. Point `--ckpt_dir` at that directory; the model
weights are not bundled in this repository.

The main attention path falls back to PyTorch SDPA. FlashAttention and `xfuser`
are optional extensions for compatible attention and multi-GPU configurations;
install them separately if using those paths. Prompt expansion requires its
corresponding model or service, and is disabled by default.

## Video editing

```bash
mkdir -p outputs
python edit.py \
  --task t2v-1.3B \
  --size '832*480' \
  --ckpt_dir /path/to/Wan2.1-T2V-1.3B \
  --video_dir /path/to/videos \
  --video_name example.mp4 \
  --prompt 'A description of the source video.' \
  --tgt_prompt 'A description of the desired edited video.' \
  --save_file outputs/edited.mp4 \
  --base_seed 42 \
  --use_flowtrack true \
  --flowtrack_lambda 0.20
```

Supported sizes are `832*480` and `480*832`; set `--size` explicitly. The single-video
loader samples up to 41 frames and resizes to `832×480`. It is intended as an editing
entry point; use dataset mode below for source-resolution evaluation.

### Dataset mode

Prepare a JSON list of editing records. `video_name` omits the `.mp4` extension:

```json
[
  {
    "video_name": "example",
    "source_prompt": "A description of the source video.",
    "target_prompt": "A description of the desired edited video."
  }
]
```

```bash
python edit.py \
  --task t2v-1.3B --size '832*480' \
  --ckpt_dir /path/to/Wan2.1-T2V-1.3B \
  --FiVE_dataset_json /path/to/edit1_prompts.json \
  --data_dir /path/to/source-videos \
  --save_dir outputs \
  --base_seed 42 --use_flowtrack true --flowtrack_lambda 0.20
```

Dataset mode reads `<data_dir>/<video_name>.mp4`. It uses source FPS and frame count,
rounds spatial dimensions down to multiples of 16 if required, pads the model input
to `4n+1` frames, and crops saved output back to the original count. Existing output
files are skipped. Filters include `--video_names`, `--indices`, `--start_index`,
`--max_items`, `--num_shards`, and `--shard_id`.

### Method options

| Option | Default | Purpose |
| --- | --- | --- |
| `--flowtrack_lambda` | `0.20` | Strength of causal edit-signal memory |
| `--flowtrack_state_mode` | `otsu` | State cost: `otsu`, `none`, or `uniform` |
| `--flowtrack_memory_mode` | `pre` | Pre-execution memory; `none` for the ablation |
| `--flowtrack_log_stats` | `false` | Record controller diagnostics |
| `--sample_steps` | `50` | Denoising steps |
| `--sample_shift` | `5.0` | Flow sampling shift |

Use `python edit.py --help` for the complete CLI. The configuration above follows
code defaults; retain the paper's exact prompts, seeds, data, and environment when
reproducing experiments. Benchmark data, metric implementations, and model weights
must be obtained separately. The code check in CI verifies Python syntax, not GPU
inference or benchmark results.

## Code structure

```text
edit.py                 # Single-video and dataset editing entry point
wan/text2video.py       # Wan pipeline and FlowTrack execution controller
wan/configs/            # Model and sampling configuration
wan/modules/            # Backbone, text encoder, and VAE
wan/utils/              # Solvers, I/O, and prompt utilities
wan/distributed/        # Optional distributed inference support
requirements.txt
```

## Acknowledgements

The backbone implementation is adapted from [Wan2.1](https://github.com/Wan-Video/Wan2.1).
Its Apache 2.0 license is retained in [wan/LICENSE.txt](wan/LICENSE.txt).
Publication metadata and a BibTeX entry will be added when the paper is publicly available.
