import logging
import os
import re
import subprocess
from platform import system
from shutil import which
from typing import Dict, Iterator, List, Union

from ffmpeg_progress_yield import FfmpegProgress

from ._errors import FFmpegNormalizeError
from ._logger import setup_custom_logger

logger = setup_custom_logger("ffmpeg_normalize")

NUL = "NUL" if system() in ("Windows", "cli") else "/dev/null"
DUR_REGEX = re.compile(
    r"Duration: (?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})\.(?P<ms>\d{2})"
)


def to_ms(s: Union[str, None] = None, decimals: Union[int, None] = None, **kwargs) -> int:
    """This function converts a string with time format "hh:mm:ss:ms" to milliseconds

    Args:
        s (str): String with time format "hh:mm:ss:ms", if not provided, the function will use the keyword arguments (optional)
        decimals (int): Number of decimals to round to (optional)

    Keyword Args:
        hour: Number of hours (optional)
        min: Number of minutes (optional)
        sec: Number of seconds (optional)
        ms: Number of milliseconds (optional)

    Returns:
        int: Integer with the number of milliseconds
    """
    if s:
        hour = int(s[0:2])
        minute = int(s[3:5])
        sec = int(s[6:8])
        ms = int(s[10:11])
    else:
        hour = int(kwargs.get("hour", 0))
        minute = int(kwargs.get("min", 0))
        sec = int(kwargs.get("sec", 0))
        ms = int(kwargs.get("ms", 0))

    result = (hour * 60 * 60 * 1000) + (minute * 60 * 1000) + (sec * 1000) + ms
    if decimals and isinstance(decimals, int):
        return round(result, decimals)
    return result


class CommandRunner:
    """
    Wrapper for running ffmpeg commands
    """
    def __init__(self, cmd: List[str], dry: bool = False):
        """Create a CommandRunner object

        Args:
            cmd: Command to run as a list of strings
            dry (bool, optional): Dry run mode. Defaults to False.
        """
        self.cmd = cmd
        self.dry = dry
        self.output: Union[str, None] = None

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


    def run_ffmpeg_command(self) -> Iterator[int]:
        """
        Run an ffmpeg command

        Yields:
            int: Progress percentage
        """
        # wrapper for 'ffmpeg-progress-yield'
        logger.debug(f"Running command: {self.cmd}")
        ff = FfmpegProgress(self.cmd, dry_run=self.dry)
        yield from ff.run_command_with_progress()

        self.output = ff.stderr

        if logger.getEffectiveLevel() == logging.DEBUG and self.output is not None:
            logger.debug(
                f"ffmpeg output: {CommandRunner.prune_ffmpeg_progress_from_output(self.output)}"
            )


    def run_command(self) -> None:
        """
        Run the actual command (not ffmpeg)

        Raises:
            RuntimeError: If command returns non-zero exit code
        """
        logger.debug(f"Running command: {self.cmd}")

        if self.dry:
            logger.debug("Dry mode specified, not actually running command")
            return

        p = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,  # Apply stdin isolation by creating separate pipe.
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=False,
        )

        # simple running of command
        stdout_bytes, stderr_bytes = p.communicate()

        stdout = stdout_bytes.decode("utf8", errors="replace")
        stderr = stderr_bytes.decode("utf8", errors="replace")

        if p.returncode == 0:
            self.output = stdout + stderr
        else:
            raise RuntimeError(f"Error running command {self.cmd}: {stderr}")


    def get_output(self) -> str:
        if self.output is None:
            raise FFmpegNormalizeError("Command has not been run yet")
        return self.output


def dict_to_filter_opts(opts: Dict[str, str]) -> str:
    """
    Convert a dictionary to a ffmpeg filter option string

    Args:
        opts (Dict[str, str]): Dictionary of options

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
    cmd_runner = CommandRunner([get_ffmpeg_exe(), "-filters"])
    cmd_runner.run_command()

    supports_loudnorm = "loudnorm" in cmd_runner.get_output()
    if not supports_loudnorm:
        logger.error(
            "Your ffmpeg does not support the 'loudnorm' filter. "
            "Please make sure you are running ffmpeg v4.2 or above."
        )
    return supports_loudnorm
