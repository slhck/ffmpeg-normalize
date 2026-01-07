# Developer Guide

## Tests

Tests are located in `tests/test_*.py`. To run them:

- Install `uv` (see [installation guide](https://github.com/astral-sh/uv#installation))
- Run `uv sync --dev` to install all dependencies
- Run `uv run pytest` to run the tests

## Creating API Docs

```bash
pdoc -d google -o docs-api ./src/ffmpeg_normalize
```

## Creating MKdocs Releases

```bash
uvx --with mkdocs-material mkdocs gh-deploy
```

We have a CI pipeline for this, so we do not need to do it manually (normally).
