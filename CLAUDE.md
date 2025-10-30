# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ffmpeg-normalize is a Python utility for audio normalization using ffmpeg. It supports EBU R128 loudness normalization, RMS-based normalization, and peak normalization for audio and video files.

## Development Commands

### Testing
- `uv run pytest` - Run all tests
- `uv run python -m ffmpeg_normalize [args]` - Run the tool directly for testing

### Code Quality
- `uv run ruff check .` - Linting
- `uv run ruff format .` - Code formatting  
- `uv run mypy src/ffmpeg_normalize` - Type checking

### Installation
- `uv sync --dev` - Install all dependencies (runtime and development)

### Documentation
- `pdoc -d google -o docs-api ./ffmpeg_normalize` - Generate API documentation
- `uvx --with mkdocs-material mkdocs gh-deploy` - Deploy MKdocs documentation

### Shell Completions
To regenerate shell completions after adding new CLI options:
```bash
# Bash
uv run python -c "
from ffmpeg_normalize.__main__ import create_parser
import shtab
parser = create_parser()
print(shtab.complete(parser, shell='bash'))
" > completions/ffmpeg-normalize-shtab.bash

# Zsh
uv run python -c "
from ffmpeg_normalize.__main__ import create_parser
import shtab
parser = create_parser()
print(shtab.complete(parser, shell='zsh'))
" > completions/ffmpeg-normalize-shtab.zsh
```

## Architecture

### Core Components

- **FFmpegNormalize** (`_ffmpeg_normalize.py`): Main class that orchestrates the normalization process
- **MediaFile** (`_media_file.py`): Represents a media file with its streams and metadata
- **Stream classes** (`_streams.py`): AudioStream, VideoStream, SubtitleStream, MediaStream for handling different stream types
- **Command utilities** (`_cmd_utils.py`): FFmpeg command generation and execution helpers
- **Error handling** (`_errors.py`): Custom exception classes
- **Logger** (`_logger.py`): Logging configuration and utilities

### Normalization Types
The tool supports three normalization types defined in `NORMALIZATION_TYPES`:
- `ebu`: EBU R128 loudness normalization (default)
- `rms`: RMS-based normalization
- `peak`: Peak normalization

### Entry Point
- Console script entry point: `ffmpeg-normalize = ffmpeg_normalize.__main__:main`
- Module execution: `python -m ffmpeg_normalize`

## Development Notes

When committing, YOU MUST use conventional commits.

### CLI Changes Checklist

When adding, removing, or modifying CLI options, YOU MUST:

1. **Update the documentation** at `docs/usage/options.md` with the new option details
2. **Regenerate shell completions** for bash and zsh (see Shell Completions section above)
3. **Test the changes** with `uv run python -m ffmpeg_normalize --help` to verify help text
4. **Update tests** if the new option affects behavior

This ensures users have accurate documentation and working shell completions for all CLI flags.

### Dependencies
The project uses:
- `tqdm` for progress bars
- `ffmpeg-progress-yield` for FFmpeg progress monitoring
- `colorlog` for colored logging
- `mutagen` for metadata handling
- `colorama` (Windows only) for colored terminal output

### File Structure
- `src/ffmpeg_normalize/` - Main package directory
- `tests/` - Test files and test media samples
- `docs/` - MKdocs documentation source
- `completions/` - Shell completion scripts

### Testing
Tests use pytest and include actual media files in the `tests/` directory. The test suite calls the CLI directly using `python -m ffmpeg_normalize` to test the full pipeline.

### Requirements
- Python 3.9+
- FFmpeg binary must be available in PATH
- The tool checks for FFmpeg loudnorm filter availability at runtime
