# ffmpeg-normalize

[![PyPI version](https://img.shields.io/pypi/v/ffmpeg-normalize.svg)](https://pypi.org/project/ffmpeg-normalize)
![Docker Image Version](https://img.shields.io/docker/v/slhck/ffmpeg-normalize?sort=semver&label=Docker%20image)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/slhck/ffmpeg-normalize/python-package.yml)

A utility for batch-normalizing audio using ffmpeg.

This program normalizes media files to a certain loudness level using the EBU R128 loudness normalization procedure. It can also perform RMS-based normalization (where the mean is lifted or attenuated), or peak normalization to a certain target level.

Batch processing of several input files is possible, including video files.

## Quick Start


1. Install a recent version of [ffmpeg](https://ffmpeg.org/download.html)
2. Run `pip3 install ffmpeg-normalize` and `ffmpeg-normalize /path/to/your/file.mp4`, alternatively install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) and run `uvx ffmpeg-normalize /path/to/your/file.mp4`
3. Done! 🎧 (the normalized file will be called `normalized/file.mkv`)

## ✨ Features

- **EBU R128 loudness normalization** — Two-pass by default, with an option for one-pass dynamic normalization
- **RMS-based normalization** — Adjust audio to a specific RMS level
- **Peak normalization** — Adjust audio to a specific peak level
- **Selective audio stream normalization** — Normalize specific audio streams or only default streams
- **Video file support** — Process video files while preserving video streams
- **Docker support** — Run via Docker container
- **Python API** — Use programmatically in your Python projects
- **Shell completions** — Available for bash, zsh, and fish
- **Album Batch normalization** – Process files jointy, preserving relative loudness

## 🆕 What's New

- Version 1.35.0 has **batch/album normalization** with `--batch`. It preserves relative loudness between files! Perfect for music albums where you want to shift all tracks by the same amount.

    Example:

    ```bash
    ffmpeg-normalize album/*.flac --batch -nt rms -t -20
    ```

    shifts the entire album so the average RMS is -20 dB, preserving the original relative loudness as mastered.

- Version 1.34.0 brings **selective audio stream normalization**! You can now:

    - Normalize specific audio streams with `-as/--audio-streams` (e.g., `-as 1,2` to normalize only streams 1 and 2)
    - Normalize only default audio streams with `--audio-default-only` (useful for files with multiple language tracks)
    - Keep other streams unchanged with `--keep-other-audio` (copy non-selected streams without normalization)

    Example:

    ```bash
    ffmpeg-normalize input.mkv -as 1 --keep-other-audio
    ```

    normalizes stream 1 and copies all other audio streams unchanged.

Other recent additions:

- **Shell completions** (v1.31.0) — Tab completion for bash, zsh, and fish shells. See the [installation guide](../getting-started/installation/#shell-completions) for setup instructions.
- **`--lower-only` option** — Prevent audio from increasing in loudness, only lower it if needed (works with all normalization types).

See the [full changelog](about/changelog.md) for all updates.
