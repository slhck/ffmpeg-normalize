import subprocess
import sys

import pytest

from ffmpeg_normalize._cmd_utils import (
    FFmpegCommandError,
    describe_error,
    summarize_ffmpeg_output,
)

FFMPEG_HEADER = """Input #0, mov,mp4,m4a,3gp,3g2,mj2, from 'in.m4a':
Metadata:
major_brand     : M4A
compatible_brands: M4A isomiso2
Duration: 00:00:03.00, start: 0.000000, bitrate: 68 kb/s
Stream #0:0[0x1](und): Audio: aac (LC), 44100 Hz, mono, fltp, 64 kb/s (default)
Metadata:
handler_name    : SoundHandler
Side data:
Replay Gain: track gain - 17.440001, track peak - 0.000001,
"""


@pytest.mark.parametrize(
    "tail,expected",
    [
        (
            "[aost#0:0 @ 0x1] Unknown encoder 'x'\n"
            "[aost#0:0 @ 0x1] Error selecting an encoder\n"
            "Error opening output files: Encoder not found",
            "Unknown encoder 'x'; Error selecting an encoder",
        ),
        (
            "[AVFilterGraph @ 0xc8] No option name near '1'\n"
            "[AVFilterGraph @ 0xc8] Error parsing a filter description around: ,astats\n"
            "Error : Invalid argument",
            "No option name near '1'; Error parsing a filter description around: ,astats",
        ),
        (
            "Expected number for ar but found: x\n"
            "Error parsing options for output file out.wav.\n"
            "Error opening output files: Invalid argument",
            "Expected number for ar but found: x; Error parsing options for output file out.wav.",
        ),
    ],
)
def test_summarize_ffmpeg_output(tail, expected):
    assert summarize_ffmpeg_output(FFMPEG_HEADER + tail) == expected


def test_summarize_ffmpeg_output_without_message():
    assert summarize_ffmpeg_output("") == "ffmpeg failed without an error message"


def test_ffmpeg_command_error_keeps_full_output():
    output = FFMPEG_HEADER + "Unknown encoder 'x'"
    error = FFmpegCommandError(["ffmpeg", "-i", "in.m4a"], output)
    # str() keeps the full output for callers that inspect it
    assert "Duration: 00:00:03.00" in str(error)
    assert describe_error(error) == "ffmpeg failed: Unknown encoder 'x'"


def test_cli_reports_ffmpeg_error_once(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ffmpeg_normalize",
            "tests/test.m4a",
            "-nt",
            "rms",
            "-c:a",
            "nonexistent_codec",
            "-o",
            str(tmp_path / "out.mp3"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert result.stderr.count("Unknown encoder 'nonexistent_codec'") == 1
    # The full ffmpeg output is only shown with --debug
    assert "Stream #0" not in result.stderr
    assert "1 of 1 file(s) failed to process: tests/test.m4a" in result.stderr
    assert "--debug" in result.stderr
