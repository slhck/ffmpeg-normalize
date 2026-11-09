"""Report ffmpeg startup failures without tracebacks."""

import os

import subprocess

import sys

import pytest

from ffmpeg_normalize import FFmpegNormalize

from ffmpeg_normalize._errors import FFmpegNormalizeError


def run_cli(*arguments, env=None):
    return subprocess.run(
        [sys.executable, "-m", "ffmpeg_normalize", *map(str, arguments)],
        capture_output=True,
        text=True,
        env=env,
    )


@pytest.mark.parametrize(
    "problem", ["missing", "not_executable", "broken", "not_on_path"]
)
def test_startup_errors_are_concise(tmp_path, problem):
    executable = tmp_path / "ffmpeg"
    env = {**os.environ, "FFMPEG_PATH": str(executable)}
    if problem in ["not_executable", "broken"]:
        executable.write_text(
            "#!/bin/sh\necho 'Library not loaded: libmissing.dylib' >&2\nexit 127\n"
        )
    if problem == "broken":
        executable.chmod(0o755)
    if problem == "not_on_path":
        env.update(FFMPEG_PATH="", PATH=str(tmp_path))
    result = run_cli("tests/test.mp3", env=env)
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert len(result.stderr.splitlines()) <= 3
    if problem != "not_on_path":
        assert str(executable) in result.stderr
    if problem == "broken":
        assert "Library not loaded: libmissing.dylib" in result.stderr


def test_api_reports_broken_ffmpeg_as_domain_error(tmp_path, monkeypatch):
    executable = tmp_path / "ffmpeg"
    executable.write_text(
        "#!/bin/sh\necho 'Library not loaded: libmissing.dylib' >&2\nexit 127\n"
    )
    executable.chmod(0o755)
    monkeypatch.setenv("FFMPEG_PATH", str(executable))
    with pytest.raises(FFmpegNormalizeError, match="Could not start ffmpeg"):
        FFmpegNormalize()
