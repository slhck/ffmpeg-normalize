from __future__ import annotations

import logging
import os
import re
import shlex
import subprocess
from shutil import which
from typing import Any, Iterator

from ffmpeg_progress_yield import FfmpegProgress

from ._errors import FFmpegNormalizeError

_logger = logging.getLogger(__name__)

DUR_REGEX = re.compile(
    r"Duration: (?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})\.(?P<ms>\d{2})"
)


class CommandRunner:
    """
    Wrapper for running ffmpeg commands
    """

    def __init__(self, dry: bool = False):
        """Create a CommandRunner object

        Args:
            cmd: Command to run as a list of strings
            dry: Dry run mode. Defaults to False.
        """
        self.dry = dry
        self.output: str | None = None

    @staticmethod
    def prune_ffmpeg_progress_from_output(output: str) -> str:
        """
        Prune ffmpeg progress lines from output

        Args:
            output (str): Output from ffmpeg

        Returns:
            str: Output with progress lines removed
        """
        return "\n".join(
            [
                line
                for line in output.splitlines()
                if not any(
                    key in line
                    for key in [
                        "bitrate=",
                        "total_size=",
                        "out_time_us=",
                        "out_time_ms=",
                        "out_time=",
                        "dup_frames=",
                        "drop_frames=",
                        "speed=",
                        "progress=",
                    ]
                )
            ]
        )

    def run_ffmpeg_command(self, cmd: list[str]) -> Iterator[float]:
        """
        Run an ffmpeg command

        Yields:
            float: Progress percentage
        """
        # wrapper for 'ffmpeg-progress-yield'
        _logger.debug(f"Running command: {shlex.join(cmd)}")
        with FfmpegProgress(cmd, dry_run=self.dry) as ff:
            yield from ff.run_command_with_progress()

            self.output = ff.stderr

        if _logger.getEffectiveLevel() == logging.DEBUG and self.output is not None:
            _logger.debug(
                f"ffmpeg output: {CommandRunner.prune_ffmpeg_progress_from_output(self.output)}"
            )

    def run_command(self, cmd: list[str]) -> CommandRunner:
        """
        Run a command with subprocess

        Returns:
            CommandRunner: itself

        Raises:
            RuntimeError: If command returns non-zero exit code
        """
        _logger.debug(f"Running command: {shlex.join(cmd)}")

        if self.dry:
            _logger.debug("Dry mode specified, not actually running command")
            return self

        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,  # Apply stdin isolation by creating separate pipe.
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=False,
        )

        stdout_bytes, stderr_bytes = p.communicate()

        stdout = stdout_bytes.decode("utf8", errors="replace")
        stderr = stderr_bytes.decode("utf8", errors="replace")

        if p.returncode != 0:
            raise RuntimeError(f"Error running command {shlex.join(cmd)}: {stderr}")

        self.output = stdout + stderr
        return self

    def get_output(self) -> str:
        if self.output is None:
            raise FFmpegNormalizeError("Command has not been run yet")
        return self.output


def dict_to_filter_opts(opts: dict[str, Any]) -> str:
    """
    Convert a dictionary to a ffmpeg filter option string

    Args:
        opts (dict[str, Any]): Dictionary of options

    Returns:
        str: Filter option string
    """
    filter_opts = []
    for k, v in opts.items():
        filter_opts.append(f"{k}={v}")
    return ":".join(filter_opts)


def get_ffmpeg_exe() -> str:
    """
    Return path to ffmpeg executable

    Returns:
        str: Path to ffmpeg executable

    Raises:
        FFmpegNormalizeError: If ffmpeg is not found
    """
    if ff_path := os.getenv("FFMPEG_PATH"):
        if os.sep in ff_path:
            if not os.path.isfile(ff_path):
                raise FFmpegNormalizeError(f"No file exists at {ff_path}")

            return ff_path

        ff_exe = which(ff_path)
        if not ff_exe:
            raise FFmpegNormalizeError(f"Could not find '{ff_path}' in your $PATH.")

        return ff_exe

    ff_path = which("ffmpeg")
    if not ff_path:
        raise FFmpegNormalizeError(
            "Could not find ffmpeg in your $PATH or $FFMPEG_PATH. "
            "Please install ffmpeg from http://ffmpeg.org"
        )

    return ff_path


def ffmpeg_has_loudnorm() -> bool:
    """
    Run feature detection on ffmpeg to see if it supports the loudnorm filter.

    Returns:
        bool: True if loudnorm is supported, False otherwise
    """
    output = CommandRunner().run_command([get_ffmpeg_exe(), "-filters"]).get_output()
    supports_loudnorm = "loudnorm" in output
    if not supports_loudnorm:
        _logger.error(
            "Your ffmpeg does not support the 'loudnorm' filter. "
            "Please make sure you are running ffmpeg v4.2 or above."
        )
    return supports_loudnorm


def validate_input_file(input_file: str) -> tuple[bool, str | None]:
    """
    Validate that an input file exists, is readable, and contains audio streams.

    This function performs a lightweight probe of the file using ffmpeg to check
    if it can be read and contains at least one audio stream.

    Args:
        input_file: Path to the input file to validate

    Returns:
        tuple: (is_valid, error_message)
            - is_valid: True if the file is valid, False otherwise
            - error_message: None if valid, otherwise a descriptive error message
    """
    # Check if file exists
    if not os.path.exists(input_file):
        return False, f"File does not exist: {input_file}"

    # Check if it's actually a file (not a directory)
    if not os.path.isfile(input_file):
        return False, f"Path is not a file: {input_file}"

    # Check if file is readable
    if not os.access(input_file, os.R_OK):
        return False, f"File is not readable (permission denied): {input_file}"

    # Check if file has audio streams using ffmpeg probe
    ffmpeg_exe = get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe,
        "-i",
        input_file,
        "-c",
        "copy",
        "-t",
        "0",
        "-map",
        "0",
        "-f",
        "null",
        os.devnull,
    ]

    try:
        output = CommandRunner().run_command(cmd).get_output()
    except RuntimeError as e:
        error_str = str(e)
        # Extract a cleaner error message from ffmpeg output
        if "Invalid data found" in error_str:
            return False, f"Invalid or corrupted media file: {input_file}"
        if "No such file or directory" in error_str:
            return False, f"File not found or cannot be opened: {input_file}"
        if "Permission denied" in error_str:
            return False, f"Permission denied when reading file: {input_file}"
        if "does not contain any stream" in error_str:
            return False, f"File contains no media streams: {input_file}"
        # Generic error for other ffmpeg failures
        return False, f"Cannot read media file: {input_file}"

    # Check for audio streams in the output
    has_audio = False
    for line in output.split("\n"):
        if line.strip().startswith("Stream") and "Audio" in line:
            has_audio = True
            break

    if not has_audio:
        return False, f"File does not contain any audio streams: {input_file}"

    return True, None
