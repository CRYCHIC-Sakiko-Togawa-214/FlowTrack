# FlowTrack

FlowTrack is a training-free, inversion-free approach for consistent text-guided video editing.

## Demo

The project page is available directly from the repository root:

- GitHub Pages: `https://crychic-sakiko-togawa-214.github.io/FlowTrack/`
- Local preview: `python3 serve.py`, then open `http://127.0.0.1:8765/`

The page is a static showcase built around **26 manually reviewed positive editing examples**. It includes synchronized Source / FlowTrack comparisons, swipe inspection, lazy-loaded result previews, category filters, search, shareable case URLs, the paper, and the code archive.

The demo assets are self-contained under `assets/`; no external scripts, fonts, model weights, or inference service are required. The page intentionally excludes failed or visibly unstable examples so the showcase focuses on clear, presentation-ready results.

## Code

- `edit.py`: main entry point for video editing and FiVE-Bench style batch evaluation.
- `wan/text2video.py`: Wan text-to-video editing pipeline with the FlowTrack execution controller.
- `wan/`: model, solver, prompt, distributed, and video I/O utilities.

Prepare the pretrained Wan checkpoints and evaluation videos separately. They are not included in this repository.

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

## Citation

Please cite the FlowTrack paper when using the method or demo assets.
