# FlowTrack Code

This directory contains the anonymized implementation used for FlowTrack experiments.

## Structure

- `edit.py`: main entry point for video editing and FiVE-Bench style batch evaluation.
- `text2video.py`: compatibility import for the text-to-video pipeline.
- `wan/text2video.py`: Wan text-to-video editing pipeline with the FlowTrack execution controller.
- `wan/configs/`: model and inference configuration files.
- `wan/modules/`: model, VAE, tokenizer, CLIP, and T5 modules.
- `wan/utils/`: sampling solvers, prompt utilities, and video/image IO helpers.
- `wan/distributed/`: distributed and context-parallel helper functions.

## Basic Usage

Prepare the pretrained Wan checkpoints and the evaluation videos separately. They are not included in this code release.

Example command:

```bash
python edit.py \
  --task t2v-1.3B \
  --ckpt_dir /path/to/wan/checkpoints \
  --FiVE_dataset_json /path/to/edit_prompt.json \
  --data_dir /path/to/source/videos \
  --save_dir outputs \
  --use_flowtrack True \
  --flowtrack_lambda 0.20
```

## Notes

- The code is training-free and does not finetune the pretrained generator.
- Paths in the example command are placeholders; use local paths for checkpoints, datasets, and outputs.
- Runtime logs and generated videos are written under the user-specified output directory.
- Do not commit generated logs, outputs, checkpoints, or datasets to the public repository.
