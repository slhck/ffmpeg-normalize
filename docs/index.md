# ffmpeg-normalize

[![PyPI version](https://img.shields.io/pypi/v/ffmpeg-normalize.svg)](https://pypi.org/project/ffmpeg-normalize)
![Docker Image Version](https://img.shields.io/docker/v/slhck/ffmpeg-normalize?sort=semver&label=Docker%20image)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/slhck/ffmpeg-normalize/python-package.yml)

A utility for batch-normalizing audio using ffmpeg.

This program normalizes media files to a certain loudness level using the EBU R128 loudness normalization procedure. It can also perform RMS-based normalization (where the mean is lifted or attenuated), or peak normalization to a certain target level.

Batch processing of several input files is possible, including video files.

## Quick Start

1. Install a recent version of [ffmpeg](https://ffmpeg.org/download.html)
2. Run `pip3 install ffmpeg-normalize`
3. Run `ffmpeg-normalize /path/to/your/file.mp4`
4. Done! 🎧 (the normalized file will be called `normalized/file.mkv`)

## Features

- EBU R128 loudness normalization
- RMS-based normalization
- Peak normalization
- Video file support
- Docker support
- Python API
