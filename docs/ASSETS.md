# FlowTrack asset workflow

The committed page is a static publication bundle. Its videos and posters are generated from matched source and FlowTrack outputs; the generation script does not invent missing examples.

## Rebuild from research inputs

Run this from a workspace that contains the original inputs (`videos/`, FiVE-Bench prompt JSON, the FlowTrack result directories, the paper, and the source code archive):

```sh
python3 scripts/prepare_assets.py --workspace /path/to/workspace
```

`--workspace` expects `it2v_edit_zjl/videos`, `it2v_edit_zjl/nips/FlowTrack/FlowTrack/edit1…edit6`,
`bench/FiVE-Bench/files`, the manuscript under `it2v_edit_zjl/nips`, and `it2v_edit_zjl/nips/code`.
For another layout, use `--source-dir`, `--results-dir`, `--prompts-dir`, `--paper`, and `--code-dir`.
Use `python3 scripts/prepare_assets.py --help` for the exact arguments. The historical relative
layout is retained when no option is supplied. Input directories, tools, and selected-pair
metadata are checked before obsolete publication clips are removed. Results must contain exactly
one MP4 per selected case. FFmpeg and FFprobe are required. The script writes `assets/cases.js`
and `assets/provenance.json`, and packages the code directory; that directory should contain
only the intended research source, without model weights, secrets, or generated data.

Do not run with `--force` unless you intend to replace every generated video and poster. Review metadata and play changed clips before committing. Keep each source/result pair at the same resolution, frame rate, frame count, and duration; only delivery encoding may differ.

## Review checklist

- Case IDs, categories, prompts, and instructions match the source evaluation record.
- Every `media.source` and `media.ours` item has a provenance record.
- `python3 scripts/validate.py` passes from a full checkout.
- `node --check app.js` and `node --check assets/cases.js` pass.
- Updated paper, code archive, and videos have explicit attribution and reuse permission.
