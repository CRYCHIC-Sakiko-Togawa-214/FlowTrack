# Contributing

Start with an issue describing the change, especially for research content or large media.
Fork the repository or create a feature branch, keep the change focused, and submit a pull request.

## Local workflow

```sh
python3 serve.py
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

The website uses plain HTML, CSS, and JavaScript. Python 3.9+ is sufficient for
maintenance tools. Node.js 22+ is used only for JavaScript syntax checks in CI.
No npm install or frontend build is needed.

Check JavaScript syntax with `node --check app.js` and `node --check assets/cases.js`.
When updating videos, follow [the asset workflow](docs/ASSETS.md). Keep source/result
geometry and timing matched, and update provenance alongside case metadata.
Do not run asset preparation without the original research inputs.

## Review expectations

- Include the commands you ran and their results in the pull request.
- Check relevant interactions, keyboard focus, mobile layout, and reduced motion for UI changes.
- Preserve measured values, comparator outcomes, prompts, and source attribution.
- Keep media paths relative so GitHub Pages subdirectory hosting continues to work.
- Keep model weights, virtual environments, caches, credentials, and raw datasets out of Git.
- Do not bulk-format the completed demo as part of unrelated maintenance.

CI checks local references and data consistency. Its sparse checkout verifies media paths
against the Git index; before publishing new media, also run the default validator from
a full checkout to verify files exist on disk, and play the changed clips in a browser.
See [license and attribution status](LICENSE_STATUS.md) before contributing third-party material.
