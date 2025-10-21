# Contributing

Thank you for your interest in contributing to ffmpeg-normalize! This guide will help you get started.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- FFmpeg installed and available in PATH
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or pip

### Setting Up Your Development Environment

1. **Fork and clone the repository**

    ```bash
    git clone https://github.com/YOUR-USERNAME/ffmpeg-normalize.git
    cd ffmpeg-normalize
    ```

2. **Install dependencies**

    Using uv (recommended):
    ```bash
    uv sync --group dev
    ```

    Or using pip:
    ```bash
    pip install -e ".[dev]"
    ```

3. **Verify your setup**

    ```bash
    # Run tests
    uv run pytest

    # Run the tool
    uv run python -m ffmpeg_normalize --help
    ```

## Development Workflow

### Making Changes

1. **Create a new branch** from `master`

    ```bash
    git checkout -b feature/your-feature-name
    ```

2. **Make your changes** following the code style guidelines below

3. **Run tests** to ensure everything works

    ```bash
    uv run pytest
    ```

4. **Check code quality**

    ```bash
    # Linting
    uv run ruff check .

    # Code formatting
    uv run ruff format .

    # Type checking
    uv run mypy src/ffmpeg_normalize
    ```

### Commit Guidelines

We use [Conventional Commits](https://www.conventionalcommits.org/) for commit messages. Each commit message should follow this format:

```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `test:` — Adding or updating tests
- `refactor:` — Code refactoring
- `chore:` — Maintenance tasks

**Examples:**
```bash
git commit -m "feat: add selective audio stream normalization"
git commit -m "fix: apply extra input options to first pass"
git commit -m "docs: update contributing guide"
```

### Submitting a Pull Request

1. **Push your changes** to your fork

    ```bash
    git push origin feature/your-feature-name
    ```

2. **Create a pull request** on GitHub

    - Provide a clear title and description
    - Reference any related issues
    - Ensure all tests pass
    - Request review from maintainers

## Code Guidelines

### Project Structure

- `src/ffmpeg_normalize/` — Main package directory
  - `_ffmpeg_normalize.py` — Main orchestration class
  - `_media_file.py` — Media file representation
  - `_streams.py` — Stream classes (Audio, Video, Subtitle)
  - `_cmd_utils.py` — FFmpeg command utilities
  - `_errors.py` — Custom exceptions
  - `_logger.py` — Logging configuration
- `tests/` — Test files and test media samples
- `docs/` — MKdocs documentation source

### Testing

- Tests use pytest and include actual media files in `tests/`
- Tests call the CLI directly using `python -m ffmpeg_normalize` to test the full pipeline
- Always add tests for new features
- Ensure existing tests pass before submitting PR

### Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Run `ruff format` before committing
- Ensure `mypy` passes without errors

## Development Commands Reference

### Testing
```bash
uv run pytest                              # Run all tests
uv run pytest tests/test_all.py -v        # Run specific test file
uv run python -m ffmpeg_normalize [args]  # Test the tool directly
```

### Code Quality
```bash
uv run ruff check .                # Linting
uv run ruff format .               # Auto-format code
uv run mypy src/ffmpeg_normalize   # Type checking
```

### Documentation
```bash
pdoc -d google -o docs-api ./ffmpeg_normalize          # Generate API docs
uvx --with mkdocs-material mkdocs serve                # Preview docs locally
uvx --with mkdocs-material mkdocs gh-deploy            # Deploy docs
```

## Getting Help

- Check existing [issues](https://github.com/slhck/ffmpeg-normalize/issues)
- Create a new issue for bugs or feature requests
- Join discussions for questions and ideas

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
