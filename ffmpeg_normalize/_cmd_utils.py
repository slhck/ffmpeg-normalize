from __future__ import annotations

import logging
import os
import re
import shlex
import subprocess
from platform import system
from shutil import which
from typing import Iterator

from ffmpeg_progress_yield import FfmpegProgress

from ._errors import FFmpegNormalizeError

_logger = logging.getLogger(__name__)

NUL = "NUL" if system() in ("Windows", "cli") else "/dev/null"
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
        ff = FfmpegProgress(cmd, dry_run=self.dry)
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


def dict_to_filter_opts(opts: dict[str, object]) -> str:
    """
    Convert a dictionary to a ffmpeg filter option string

    Args:
        opts (dict[str, object]): Dictionary of options

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
