"""Verify encoded outputs and report ffmpeg startup failures without tracebacks."""

import json
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


@pytest.mark.parametrize("mode", ["ebu", "rms", "peak"])
@pytest.mark.parametrize("codec,extension", [("pcm_s16le", "wav"), ("aac", "m4a")])
def test_verifies_lossless_and_lossy_encoded_audio(tmp_path, mode, codec, extension):
    destination = tmp_path / f"output.{extension}"
    # AAC transients can overshoot sample peaks substantially; exercise the
    # configurable tolerance while still measuring the actual encoded audio.
    tolerance = 5 if codec == "aac" and mode == "peak" else 0.5
    peak_tolerance = 5 if codec == "aac" and mode == "peak" else 0.1
    result = run_cli(
        "tests/test_quiet.m4a",
        "-nt",
        mode,
        "-t",
        "-23",
        "-c:a",
        codec,
        "-o",
        destination,
        "--verify",
        "--verify-loudness-tolerance",
        str(tolerance),
        "--verify-peak-tolerance",
        str(peak_tolerance),
        "--print-stats",
        "--print-summary",
    )
    assert result.returncode == 0, result.stderr
    (stats,) = json.loads(result.stdout)
    verification = stats["verification"]
    assert verification["passed"] is True
    assert verification["output_level"] == pytest.approx(-23, abs=tolerance)
    assert verification["output_peak"] <= verification["peak_limit"] + peak_tolerance
    assert "measured after encoding" in result.stderr
    assert "calculated from applied gain" in result.stderr
    assert destination.is_file()


def test_post_filter_level_change_is_detected(tmp_path):
    destination = tmp_path / "output.wav"
    result = run_cli(
        "tests/test_quiet.m4a",
        "-nt",
        "rms",
        "-t",
        "-23",
        "-pof",
        "volume=-6dB",
        "-o",
        destination,
        "--verify",
        "--print-stats",
        "--print-summary",
    )
    assert result.returncode == 1
    (stats,) = json.loads(result.stdout)
    assert stats["status"] == "error"
    assert stats["verification"]["passed"] is False
    assert stats["verification"]["expected_level"] == pytest.approx(-23)
    assert stats["verification"]["output_level"] == pytest.approx(-29, abs=0.02)
    assert "Encoded-output verification failed" in stats["error"]
    assert "FAILED" in result.stderr
    assert destination.is_file()


def test_peak_overshoot_is_checked_independently(tmp_path):
    result = run_cli(
        "tests/test_quiet.m4a",
        "-nt",
        "peak",
        "-t",
        "-10",
        "-pof",
        "volume=1dB",
        "-o",
        tmp_path / "output.wav",
        "--verify",
        "--verify-loudness-tolerance",
        "2",
        "--verify-peak-tolerance",
        "0.1",
        "--print-stats",
    )
    assert result.returncode == 1
    verification = json.loads(result.stdout)[0]["verification"]
    assert len(verification["errors"]) == 1
    assert "exceeds ceiling" in verification["errors"][0]


def test_tolerances_can_allow_measured_deviation(tmp_path):
    result = run_cli(
        "tests/test_quiet.m4a",
        "-nt",
        "peak",
        "-t",
        "-10",
        "-pof",
        "volume=1dB",
        "-o",
        tmp_path / "output.wav",
        "--verify",
        "--verify-loudness-tolerance",
        "2",
        "--verify-peak-tolerance",
        "2",
        "--print-stats",
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[0]["verification"]["passed"] is True


@pytest.mark.parametrize(
    "options", [["--batch"], ["--lower-only"], ["--batch", "--lower-only"]]
)
def test_effective_levels_are_verified(tmp_path, options):
    normalizer = FFmpegNormalize(
        normalization_type="rms",
        target_level=-10,
        verify=True,
        batch="--batch" in options,
        lower_only="--lower-only" in options,
    )
    for index, source in enumerate(["tests/test_quiet.m4a", "tests/test_loud.m4a"]):
        normalizer.add_media_file(source, str(tmp_path / f"output{index}.wav"))
    normalizer.run_normalization()
    for row in normalizer.get_summary():
        assert row["status"] == "normalized"
        assert row["output_source"] == "calculated"
        assert row["verification"]["passed"] is True
        assert row["verification"]["output_level"] == pytest.approx(
            row["output_level"], abs=0.5
        )


@pytest.mark.parametrize(
    "options,target,tolerance",
    [(["--dynamic"], -10, 0.5), (["--auto-lower-loudness-target"], -5, 1.0)],
)
def test_ebu_effective_targets(tmp_path, options, target, tolerance):
    result = run_cli(
        "tests/test_quiet.m4a",
        "-t",
        str(target),
        *options,
        "-o",
        tmp_path / "output.wav",
        "--verify",
        "--verify-loudness-tolerance",
        str(tolerance),
        "--print-stats",
    )
    assert result.returncode == 0, result.stderr
    verification = json.loads(result.stdout)[0]["verification"]
    assert verification["passed"] is True
    if "--auto-lower-loudness-target" in options:
        assert verification["expected_level"] < -5


@pytest.mark.parametrize(
    "keep_options", [[], ["--keep-other-audio"], ["--keep-original-audio"]]
)
def test_selected_stream_is_mapped_to_encoded_output(tmp_path, keep_options):
    result = run_cli(
        "tests/test.mp4",
        "-as",
        "2",
        *keep_options,
        "-nt",
        "peak",
        "-t",
        "-10",
        "-o",
        tmp_path / "output.mkv",
        "--verify",
        "--print-stats",
    )
    assert result.returncode == 0, result.stderr
    stats = json.loads(result.stdout)
    selected = next(stream for stream in stats if stream["stream_id"] == 2)
    assert selected["verification"]["passed"] is True
    assert selected["verification"]["output_stream_id"] == 1
    assert all(
        "verification" not in stream for stream in stats if stream["stream_id"] != 2
    )


def test_skipped_files_are_measured_at_their_unchanged_levels(tmp_path):
    normalizer = FFmpegNormalize(
        normalization_type="peak",
        target_level=-23,
        threshold=2,
        verify=True,
        audio_codec="aac",
    )
    normalizer.add_media_file("tests/test_quiet.m4a", str(tmp_path / "copy.m4a"))
    normalizer.run_normalization()
    (row,) = normalizer.get_summary()
    assert row["status"] == "skipped"
    assert row["verification"]["passed"] is True
    assert row["verification"]["expected_level"] == row["input_level"]


def test_dry_run_does_not_measure_output(tmp_path):
    destination = tmp_path / "output.wav"
    result = run_cli(
        "tests/test_quiet.m4a",
        "-o",
        destination,
        "--verify",
        "-n",
        "--print-summary",
        "--print-stats",
    )
    assert result.returncode == 0, result.stderr
    assert not destination.exists()
    assert "verification" not in json.loads(result.stdout)[0]
    assert "verification skipped: dry run" in result.stderr


@pytest.mark.parametrize(
    "option,value",
    [
        ("--verify-loudness-tolerance", "-1"),
        ("--verify-peak-tolerance", "nan"),
        ("--verify-peak-tolerance", "inf"),
    ],
)
def test_invalid_tolerance_has_no_traceback(option, value):
    result = run_cli("tests/test.mp3", "--verify", option, value)
    assert result.returncode == 1
    assert "Traceback" not in result.stderr


def test_replaygain_verification_is_rejected():
    result = run_cli("tests/test.mp3", "--verify", "--replaygain")
    assert result.returncode == 1
    assert "cannot be combined" in result.stderr
    assert "Traceback" not in result.stderr


def test_null_output_verification_is_rejected():
    result = run_cli("tests/test.mp3", "--verify", "-o", os.devnull, "-f")
    assert result.returncode == 1
    assert "requires an output file" in result.stderr


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


def test_verification_does_not_reapply_pre_filter(tmp_path):
    result = run_cli(
        "tests/test_quiet.m4a",
        "-nt",
        "rms",
        "-t",
        "-23",
        "-prf",
        "volume=-6dB",
        "-o",
        tmp_path / "output.wav",
        "--verify",
        "--print-stats",
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[0]["verification"][
        "output_level"
    ] == pytest.approx(-23, abs=0.02)


def test_nonfinite_output_measurements_fail_verification(tmp_path):
    result = run_cli(
        "tests/test_quiet.m4a",
        "-nt",
        "rms",
        "-t",
        "-23",
        "-pof",
        "volume=0",
        "-o",
        tmp_path / "output.wav",
        "--verify",
        "--print-stats",
    )
    assert result.returncode == 1
    verification = json.loads(result.stdout)[0]["verification"]
    assert verification["passed"] is False
    assert verification["output_level"] is None
    assert verification["output_peak"] is None
    assert "not finite" in verification["errors"][0]


def test_verification_preserves_requested_timestamps(tmp_path):
    normalizer = FFmpegNormalize(
        normalization_type="rms", target_level=-23, verify=True, keep_mtime=True
    )
    destination = tmp_path / "output.wav"
    normalizer.add_media_file("tests/test_quiet.m4a", str(destination))
    normalizer.run_normalization()
    (media_file,) = normalizer.media_files
    assert media_file.status == "normalized"
    assert media_file.input_timestamps is not None
    actual = destination.stat()
    assert (actual.st_atime, actual.st_mtime) == pytest.approx(
        media_file.input_timestamps, abs=0.01
    )
