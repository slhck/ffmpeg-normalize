import logging
import os
from shutil import which
import subprocess
from platform import system as _current_os
import re
from ffmpeg_progress_yield import FfmpegProgress

from ._errors import FFmpegNormalizeError
from ._logger import setup_custom_logger

logger = setup_custom_logger("ffmpeg_normalize")

CUR_OS = _current_os()
IS_WIN = CUR_OS in ["Windows", "cli"]
IS_NIX = (not IS_WIN) and any(
    CUR_OS.startswith(i)
    for i in ["CYGWIN", "MSYS", "Linux", "Darwin", "SunOS", "FreeBSD", "NetBSD"]
)
NUL = "NUL" if IS_WIN else "/dev/null"
DUR_REGEX = re.compile(
    r"Duration: (?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})\.(?P<ms>\d{2})"
)


# https://gist.github.com/Hellowlol/5f8545e999259b4371c91ac223409209
def to_ms(s=None, des=None, **kwargs):
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
    if des and isinstance(des, int):
        return round(result, des)
    return result


class CommandRunner:
    def __init__(self, cmd, dry=False):
        self.cmd = cmd
        self.dry = dry
        self.output = None

    @staticmethod
    def prune_ffmpeg_progress_from_output(output: str) -> str:
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

    def run_ffmpeg_command(self):
        # wrapper for 'ffmpeg-progress-yield'
        logger.debug(f"Running command: {self.cmd}")
        ff = FfmpegProgress(self.cmd, dry_run=self.dry)
        yield from ff.run_command_with_progress()

        self.output = ff.stderr

        if logger.getEffectiveLevel() == logging.DEBUG and self.output is not None:
            logger.debug(
                f"ffmpeg output: {CommandRunner.prune_ffmpeg_progress_from_output(self.output)}"
            )

    def run_command(self):
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
        stdout, stderr = p.communicate()

        stdout = stdout.decode("utf8", errors="replace")
        stderr = stderr.decode("utf8", errors="replace")

        if p.returncode == 0:
            self.output = stdout + stderr
        else:
            raise RuntimeError(f"Error running command {self.cmd}: {str(stderr)}")

    def get_output(self):
        if self.output is None:
            raise FFmpegNormalizeError("Command has not been run yet")
        return self.output


def dict_to_filter_opts(opts):
    filter_opts = []
    for k, v in opts.items():
        filter_opts.append(f"{k}={v}")
    return ":".join(filter_opts)


def get_ffmpeg_exe():
    """
    Return path to ffmpeg executable
    """
    ffmpeg_path = os.getenv("FFMPEG_PATH")
    if ffmpeg_path:
        if os.sep in ffmpeg_path:
            ffmpeg_exe = ffmpeg_path
            if not os.path.isfile(ffmpeg_exe):
                raise FFmpegNormalizeError(f"No file exists at {ffmpeg_exe}")
        else:
            ffmpeg_exe = which(ffmpeg_path)
            if not ffmpeg_exe:
                raise FFmpegNormalizeError(
                    f"Could not find '{ffmpeg_path}' in your $PATH."
                )
    else:
        ffmpeg_exe = which("ffmpeg")

    if not ffmpeg_exe:
        if which("avconv"):
            raise FFmpegNormalizeError(
                "avconv is not supported. "
                "Please install ffmpeg from http://ffmpeg.org instead."
            )
        else:
            raise FFmpegNormalizeError(
                "Could not find ffmpeg in your $PATH or $FFMPEG_PATH. "
                "Please install ffmpeg from http://ffmpeg.org"
            )

    return ffmpeg_exe


def ffmpeg_has_loudnorm():
    """
    Run feature detection on ffmpeg, returns True if ffmpeg supports
    the loudnorm filter
    """
    cmd_runner = CommandRunner([get_ffmpeg_exe(), "-filters"])
    cmd_runner.run_command()
    output = cmd_runner.get_output()
    if "loudnorm" in output:
        return True
    else:
        logger.error(
            "Your ffmpeg version does not support the 'loudnorm' filter. "
            "Please make sure you are running ffmpeg v3.1 or above."
        )
        return False
