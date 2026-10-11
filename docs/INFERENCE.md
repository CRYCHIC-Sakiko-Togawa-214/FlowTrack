# Research inference setup

The static website needs none of these dependencies. This guide documents the included
`edit.py`/`wan/` implementation; it is not a claim that inference has been reproduced on
this machine. Model weights, FiVE-Bench inputs, and the original experiment environment
are not included.

## Environment

Use a Linux CUDA environment with Python 3.10+ and an NVIDIA GPU compatible with your
PyTorch build. Install a matched CUDA-enabled `torch`/`torchvision` pair using the
[PyTorch installation selector](https://pytorch.org/get-started/locally/), then:

```sh
python -m venv .venv
. .venv/bin/activate
# Install CUDA-enabled torch/torchvision in this environment first.
pip install -r requirements-inference.txt
```

The requirements file lists the dependency inventory derived from source imports; it is
not a tested lockfile. Record exact package, CUDA, driver, and
checkpoint versions with any reproduced results. Some attention paths need a compatible
FlashAttention installation; install it for your CUDA/PyTorch combination if required.
Multi-GPU context parallelism additionally imports `xfuser`. These compiled/distributed
packages are deliberately not installed by the website CI.

Obtain the Wan2.1 T2V 1.3B checkpoint through the
[upstream Wan project](https://github.com/Wan-Video/Wan2.1) and follow its checkpoint
layout and license. Keep checkpoints outside Git or under ignored `checkpoints/`.
The entry point currently validates only the `t2v-1.3B` editing task even though other
Wan configurations are present in the source.

## Single-video editing

From the repository root, with the environment and checkpoints available:

```sh
python edit.py \
  --task t2v-1.3B --size '832*480' \
  --ckpt_dir /path/to/Wan2.1-T2V-1.3B \
  --video_dir /path/to/source-videos --video_name example.mp4 \
  --prompt 'Describe the source video accurately.' \
  --tgt_prompt 'Describe the desired edited video.' \
  --save_dir outputs --base_seed 42 \
  --use_flowtrack true --flowtrack_lambda 0.20
```

`832*480` is a supported size; the CLI's generic default `1280*720` is not supported by
`t2v-1.3B`, so specify the size explicitly. `--video_name` includes the extension for this
single-video path. The source frame loader has its own resizing/sampling behavior; read
`edit.py` before comparing outputs with dataset-mode evaluation. Inspect `python edit.py
--help` for the controller and ablation options once dependencies are installed.

## Dataset mode

Supply `--FiVE_dataset_json /path/to/prompts.json` and `--video_dir /path/to/videos`.
The JSON is a list of entries with `video_name` (without `.mp4`), `source_prompt`, and
`target_prompt`; videos are looked up as `<video_name>.mp4`. Filters include
`--video_names`, `--indices`, `--start_index`, `--max_items`, and shard options.
Preserve the original benchmark records and evaluation protocol for reproducibility.

The CI compiles Python syntax but does not import CUDA modules, download weights,
execute editing, or reproduce the paper's quantitative results.
