# Developer Guide

## Tests

Tests are located in `tests/test_*.py`. To run them:

- Install `requirements.txt` and `requirements.dev.txt`
- Run `pytest`

## Creating API Docs

```bash
pdoc -d google -o docs-api ./ffmpeg_normalize
```

## Creating MKdocs Releases

```bash
uvx --with mkdocs-material mkdocs gh-deploy
```

(We do not have a CI pipeline for this, so we need to do it manually.)
