# FlowTrack

**Controlling Edit-Signal Execution in Inversion-Free Flow Video Editing**

[![Repository checks](https://github.com/CRYCHIC-Sakiko-Togawa-214/FlowTrack/actions/workflows/ci.yml/badge.svg)](https://github.com/CRYCHIC-Sakiko-Togawa-214/FlowTrack/actions/workflows/ci.yml)
[![Demo](https://img.shields.io/badge/demo-GitHub%20Pages-blue)](https://crychic-sakiko-togawa-214.github.io/FlowTrack/)

A self-contained research project page with synchronized source/FlowTrack video previews,
category filters, a method overview, and FiVE-Bench region-aware evaluation results.
The repository also includes the Python research implementation in `edit.py` and `wan/`.

**[Live demo](https://crychic-sakiko-togawa-214.github.io/FlowTrack/)** ·
**[Paper](assets/FlowTrack-paper.pdf)** · **[Implementation](docs/INFERENCE.md)**

## Quick start

The website needs only Python 3.9+ and a modern browser. No npm installation, frontend
build, model checkpoint, or GPU is required to view the demo.

```sh
git clone --depth 1 https://github.com/CRYCHIC-Sakiko-Togawa-214/FlowTrack.git
cd FlowTrack
python3 serve.py
```

Open <http://127.0.0.1:8765/>. Use `--port 8080` for another port. The local server
supports byte-range requests for video seeking and binds to loopback by default.
The clone includes large research media; use a sparse checkout for source-only maintenance.

## What is included

The published catalog has **37 curated cases** and **74 paired videos**, covering subject,
creative, color, material, and addition edits. These are selected qualitative results,
not the complete evaluation dataset. Each source/result pair has matching resolution,
frame rate, frame count, and duration. Delivery videos use H.264 CRF 22 with faststart;
there is no frame interpolation or speed change.

Video previews load when visible and pause offscreen. The page respects reduced-motion
preferences and works on desktop and mobile. Numerical results are recorded in
`index.html`; prompts and per-case measurements are in `assets/cases.js`.

| Path | Purpose |
| --- | --- |
| `index.html`, `styles.css`, `app.js` | Static project page and interactions |
| `assets/cases.js` | Generated case catalog, prompts, and media mapping |
| `assets/provenance.json` | Original/web video geometry and timing metadata |
| `assets/videos/`, `assets/posters/` | Published clips and preview images |
| `edit.py`, `wan/` | Research inference implementation |
| `serve.py` | Standard-library local preview server |
| `scripts/prepare_assets.py` | Rebuild publication assets from original research inputs |
| `scripts/validate.py`, `tests/` | Offline integrity checks and behavior tests |

## Validation

```sh
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
node --check app.js
node --check assets/cases.js
```

Node.js 22+ is needed only for JavaScript syntax checks. The validator checks local links,
HTML anchors, case IDs, media mappings, and metadata against provenance. Tests cover real
HTTP range requests and rejection of corrupted data. GitHub Actions runs these checks on
pushes and pull requests without installing GPU dependencies.

For a sparse checkout, run `python3 scripts/validate.py --tracked-assets`: this verifies
omitted media paths against the Git index. Default validation verifies files on disk.
Neither mode replaces playing new clips or independently inspecting their binary metadata.

## Updating and deploying

See [the asset workflow](docs/ASSETS.md) for configurable source paths, original inputs,
FFmpeg/FFprobe requirements, and validation before replacing media. The generation script
requires unpublished research workspace inputs that are not bundled in this repository.
Do not run it just to preview the site.

GitHub Pages currently publishes `main` from the repository root. Keep `.nojekyll` and
relative asset paths. Other static hosts can serve the same files without a build step.
The CI workflow checks the repository; it does not change deployment configuration.

## Research implementation and attribution

See [inference setup](docs/INFERENCE.md) for dependencies, checkpoints, and example commands.
Static checks do not reproduce GPU inference or verify the full benchmark. The PDF remains
an anonymous manuscript; author names, arXiv IDs, DOI, and BibTeX are not fabricated here.
Use the published paper for method details and update citation metadata when available.

The original design references are preserved in [DESIGN_REFERENCES.md](DESIGN_REFERENCES.md).
Manrope is self-hosted under the [SIL Open Font License](assets/fonts/OFL.txt).
There is no repository-wide reuse license yet; see [license status](LICENSE_STATUS.md).
For maintenance changes, follow [CONTRIBUTING.md](CONTRIBUTING.md).
