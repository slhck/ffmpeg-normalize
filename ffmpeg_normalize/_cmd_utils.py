import os
import sys
import subprocess
from platform import system as _current_os

from ._errors import FFmpegNormalizeError
from ._logger import setup_custom_logger
logger = setup_custom_logger('ffmpeg_normalize')

CUR_OS = _current_os()
IS_WIN = CUR_OS in ['Windows', 'cli']
IS_NIX = (not IS_WIN) and any(
    CUR_OS.startswith(i) for i in
    ['CYGWIN', 'MSYS', 'Linux', 'Darwin', 'SunOS', 'FreeBSD', 'NetBSD'])
NUL = 'NUL' if IS_WIN else '/dev/null'

def which(program):
    """
    Find a program in PATH and return path
    From: http://stackoverflow.com/q/377017/
    """
    def is_exe(fpath):
        found = os.path.isfile(fpath) and os.access(fpath, os.X_OK)
        if not found and sys.platform == 'win32':
            fpath = fpath + ".exe"
            found = os.path.isfile(fpath) and os.access(fpath, os.X_OK)
        return found

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            logger.debug("found executable: " + str(program))
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = os.path.expandvars(os.path.expanduser(path)).strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                logger.debug("found executable: " + str(exe_file))
                return exe_file

    return None

def dict_to_filter_opts(opts):
    filter_opts = []
    for k, v in opts.items():
        filter_opts.append("{}={}".format(k, v))
    return ":".join(filter_opts)

def run_command(cmd, dry=False):
    """
    Generic function to run a command.
    Set dry to just print and don't actually run.

    Returns stdout + stderr.
    """
    logger.debug("Running command: {}".format(cmd))

    if dry:
        logger.debug("Dry mode specified, not actually running command")
        return

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    stdout, stderr = p.communicate()

    if p.returncode == 0:
        return (stdout + stderr)
    else:
        raise RuntimeError("Error running command {}: {}".format(cmd, str(stderr)))


# run feature detection on ffmpeg after module import
if 'FFMPEG_PATH' in os.environ:
    ffmpeg_exe = os.environ['FFMPEG_PATH']
else:
    ffmpeg_exe = which('ffmpeg')

FFMPEG_HAS_LOUDNORM = False
if not ffmpeg_exe or not os.path.isfile(ffmpeg_exe):
    if which('avconv'):
        raise FFmpegNormalizeError(
            "avconv is not supported. "
            "Please install ffmpeg from http://ffmpeg.org instead."
        )
    else:
        raise FFmpegNormalizeError(
            "Could not find ffmpeg in your $PATH or $FFMPEG_PATH. "
            "Please install ffmpeg from http://ffmpeg.org"
        )
else:
    output = run_command(['ffmpeg', '-filters'])
    if 'loudnorm' in output:
        FFMPEG_HAS_LOUDNORM = True
    else:
        logger.warning(
            "Your ffmpeg version does not support the 'loudnorm' filter. "
            "Please make sure you are running ffmpeg v3.1 or above."
        )
