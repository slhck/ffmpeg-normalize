from __future__ import division
import os
import sys
import subprocess
from platform import system as _current_os
import re

from ._errors import FFmpegNormalizeError
from ._logger import setup_custom_logger
logger = setup_custom_logger('ffmpeg_normalize')

CUR_OS = _current_os()
IS_WIN = CUR_OS in ['Windows', 'cli']
IS_NIX = (not IS_WIN) and any(
    CUR_OS.startswith(i) for i in
    ['CYGWIN', 'MSYS', 'Linux', 'Darwin', 'SunOS', 'FreeBSD', 'NetBSD'])
NUL = 'NUL' if IS_WIN else '/dev/null'

# https://gist.github.com/Hellowlol/5f8545e999259b4371c91ac223409209
def to_ms(s=None, des=None, **kwargs):
    if s:
        hour = int(s[0:2])
        minute = int(s[3:5])
        sec = int(s[6:8])
        ms = int(s[10:11])
    else:
        hour = int(kwargs.get('hour', 0))
        minute = int(kwargs.get('min', 0))
        sec = int(kwargs.get('sec', 0))
        ms = int(kwargs.get('ms'))

    result = (hour * 60 * 60 * 1000) + (minute * 60 * 1000) + (sec * 1000) + ms
    if des and isinstance(des, int):
        return round(result, des)
    return result

class CommandRunner():
    DUR_REGEX = re.compile(r'Duration: (?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})\.(?P<ms>\d{2})')
    TIME_REGEX = re.compile(r'\stime=(?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})\.(?P<ms>\d{2})')

    def __init__(self, cmd, dry=False):
        self.cmd = cmd
        self.dry = dry
        self.output = None

    def run_ffmpeg_command(self):
        """
        Run an ffmpeg command, trying to capture the process output and calculate
        the duration / progress.
        Yields the progress in percent.
        """
        logger.debug("Running ffmpeg command: {}".format(self.cmd))

        if self.dry:
            logger.debug("Dry mode specified, not actually running command")
            return

        total_dur = None

        stderr = []

        p = subprocess.Popen(
            self.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=False
        )

        # for stderr_line in iter(p.stderr):
        while True:
            line = p.stderr.readline().decode("utf8", errors='replace')
            if line == '' and p.poll() is not None:
                break
            stderr.append(line.strip())
            self.output = "\n".join(stderr)

            if not total_dur and CommandRunner.DUR_REGEX.search(line):
                total_dur = CommandRunner.DUR_REGEX.search(line).groupdict()
                total_dur = to_ms(**total_dur)
                continue
            if total_dur:
                result = CommandRunner.TIME_REGEX.search(line)
                if result:
                    elapsed_time = to_ms(**result.groupdict())
                    yield int(elapsed_time / total_dur * 100)

        if p.returncode != 0:
            raise RuntimeError("Error running command {}: {}".format(self.cmd, str("\n".join(stderr))))

        yield 100

    def run_command(self):
        logger.debug("Running command: {}".format(self.cmd))

        if self.dry:
            logger.debug("Dry mode specified, not actually running command")
            return

        p = subprocess.Popen(
            self.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=False
        )

        # simple running of command
        stdout, stderr = p.communicate()

        stdout = stdout.decode("utf8", errors='replace')
        stderr = stderr.decode("utf8", errors='replace')

        if p.returncode == 0:
            self.output = (stdout + stderr)
        else:
            raise RuntimeError("Error running command {}: {}".format(self.cmd, str(stderr)))

    def get_output(self):
        return self.output

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
                logger.debug("found executable in path: " + str(exe_file))
                return exe_file

    return None

def dict_to_filter_opts(opts):
    filter_opts = []
    for k, v in opts.items():
        filter_opts.append("{}={}".format(k, v))
    return ":".join(filter_opts)

def get_ffmpeg_exe():
    """
    Return path to ffmpeg executable
    """
    if 'FFMPEG_PATH' in os.environ:
        ffmpeg_exe = os.environ['FFMPEG_PATH']
    else:
        ffmpeg_exe = which('ffmpeg')

    if not ffmpeg_exe:
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

    return ffmpeg_exe

def ffmpeg_has_loudnorm():
    """
    Run feature detection on ffmpeg, returns True if ffmpeg supports
    the loudnorm filter
    """
    cmd_runner = CommandRunner([get_ffmpeg_exe(), '-filters'])
    cmd_runner.run_command()
    output = cmd_runner.get_output()
    if 'loudnorm' in output:
        return True
    else:
        logger.warning(
            "Your ffmpeg version does not support the 'loudnorm' filter. "
            "Please make sure you are running ffmpeg v3.1 or above."
        )
        return False
