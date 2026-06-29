# ffmpeg-normalize

[![PyPI version](https://img.shields.io/pypi/v/ffmpeg-normalize.svg)](https://pypi.org/project/ffmpeg-normalize)
![Docker Image Version](https://img.shields.io/docker/v/slhck/ffmpeg-normalize?sort=semver&label=Docker%20image)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/slhck/ffmpeg-normalize/python-package.yml)

A utility for batch-normalizing audio using ffmpeg.

This program normalizes media files to a certain loudness level using the EBU R128 loudness normalization procedure. It can also perform RMS-based normalization (where the mean is lifted or attenuated), or peak normalization to a certain target level.

Batch processing of several input files is possible, including video files.

## Quick Start


1. Install a recent version of [ffmpeg](https://ffmpeg.org/download.html) and Python 3.10 or higher
2. Run `pip3 install ffmpeg-normalize` and `ffmpeg-normalize /path/to/your/file.mp4`, alternatively install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) and run `uvx ffmpeg-normalize /path/to/your/file.mp4`
3. Done! 🎧 (the normalized file will be called `normalized/file.mkv`)

## ✨ Features

- **EBU R128 loudness normalization** — Two-pass by default, with an option for one-pass dynamic normalization
- **RMS-based normalization** — Adjust audio to a specific RMS level
- **Peak normalization** — Adjust audio to a specific peak level
- **Selective audio stream normalization** — Normalize specific audio streams or only default streams
- **Skip files already at target** — Avoid re-encoding files already within a threshold of the target level
- **Per-file outcome reporting** — `status` field in `--print-stats` plus exit codes for scripting
- **Video file support** — Process video files while preserving video streams
- **Docker support** — Run via Docker container
- **Python API** — Use programmatically in your Python projects
- **Shell completions** — Available for bash, zsh, and fish
- **Album Batch normalization** – Process files jointly, preserving relative loudness

## 🆕 What's New

- Version 1.41.0 automatically picks the correct output audio codec for the output container, so you no longer need to specify `-c:a`/`--audio-codec` unless you want to override the default. PCM is chosen for containers that support it; others will use teh default that ffmpeg picks. See [the usage guide](https://slhck.info/ffmpeg-normalize/usage/file-input-output/#how-the-output-audio-codec-is-chosen) for details.

- Version 1.40.0 can optionally **skip files that are already at the target level** via `--threshold` (e.g. `--threshold 0.5`, disabled by default). Such files are copied through unchanged instead of being re-encoded. The `--print-stats` output now includes a per-file `status` (`normalized`, `skipped`, or `error`, plus an `error` message on failure), and the exit code is non-zero if any file failed to process, so a script can tell what happened to each file.

    Example:

    ```bash
    ffmpeg-normalize input.flac -nt peak -t 0 -c:a flac --print-stats -o output.flac
    ```

- Version 1.39.0 preserves the **input bit depth** by default when encoding to formats like FLAC, so 16-bit input stays 16-bit without needing `-e "-sample_fmt s16"`. Use `--no-keep-bit-depth` to opt out. It also adds `--keep-mtime` to copy the input file's modification time to the output, which is useful for preserving when a track was added to a music library.

    Example:

    ```bash
    ffmpeg-normalize input.flac -nt peak -t 0 -c:a flac --keep-mtime -o output.flac
    ```

- Version 1.38.0 writes the normalized output directly to its destination without using temporary files

- Version 1.36.0 introduces **presets** with `--preset`! Save and reuse your favorite normalization configurations for different use cases. Comes with three built-in presets: `podcast` (AES standard), `music` (RMS-based batch normalization), and `streaming-video` (video content). Create custom presets too!

    Example:

    ```bash
    ffmpeg-normalize input.mp3 --preset podcast
    ```

    applies the podcast preset (EBU R128, -16 LUFS) to your file. Learn more in the [presets guide](usage/presets.md).

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

- **Shell completions** (v1.31.0) — Tab completion for bash, zsh, and fish shells. See the [installation guide](getting-started/installation/#shell-completions) for setup instructions.
- **`--lower-only` option** — Prevent audio from increasing in loudness, only lower it if needed (works with all normalization types).

See the [full changelog](about/changelog.md) for all updates.
