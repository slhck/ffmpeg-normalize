#!/usr/bin/env python
"""
ffmpeg-normalize 0.1.3

ffmpeg / avconv macro for normalizing audio

Audio normalization script, normalizing media files to WAV output

This program normalizes audio to a certain dB level. The default is an RMS-based
normalization where the mean is lifted. Peak normalization is possible with the
-m/--max option. It takes any audio or video file as input, and writes the audio
part as output WAV file.

Usage:
  ffmpeg-normalize [options] <input-file>...

Options:
  -f --force            Force overwriting existing files
  -l --level <level>    dB level to normalize to [default: -26]
  -p --prefix <prefix>  Normalized file prefix [default: normalized]
  -m --max              Normalize to the maximum (peak) volume instead of RMS
  -v --verbose          Enable verbose output
  -n --dry-run          Show what would be done, do not convert
  -d --debug            Show debug output

Examples:

  ffmpeg-normalize -v file.mp3
  ffmpeg-normalize -v *.avi

"""
#
# The MIT License (MIT)
#
# Copyright (c) 2015 Werner Robitza
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from docopt import docopt
import subprocess
import os
import re
import sys
import logging

from . import __version__

logger = logging.getLogger('ffmpeg_normalize')
logger.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


args = dict()

# http://stackoverflow.com/questions/377017/test-if-executable-exists-in-python
def which(program):
    def is_exe(fpath):
        found = os.path.isfile(fpath) and os.access(fpath, os.X_OK)
        if not found and sys.platform == 'win32':
          fpath = fpath + ".exe"
          found = os.path.isfile(fpath) and os.access(fpath, os.X_OK)
        return found

    fpath, __ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

FFMPEG_CMD = which('ffmpeg') or which('avconv') or None

if not FFMPEG_CMD:
    raise SystemExit("Could not find ffmpeg or avconv in your $PATH")

if 'avconv' in FFMPEG_CMD:
    NORMALIZE_CMD = which('normalize-audio')
    if not NORMALIZE_CMD:
        raise SystemExit(
            "avconv needs the normalize-audio command:\n"
            "    sudo apt-get install normalize-audio"
        )

def run_command(cmd, raw=False, dry=False):
    cmd = cmd.replace("  ", " ")
    cmd = cmd.replace("  ", " ")
    logger.debug("[command] {0}".format(cmd))

    if dry:
        return

    if raw:
        p = subprocess.Popen(cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)
    else:
        p = subprocess.Popen(cmd.split(" "),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

    stdout, stderr = p.communicate()

    if p.returncode == 0:
        return stdout + stderr
    else:
        logger.error("Error running command: {}".format(cmd))
        logger.error(str(stderr))


def ffmpeg_get_mean(input_file):
    cmd = FFMPEG_CMD + ' -i "' + input_file + '" -filter:a "volumedetect" -vn -sn -f null /dev/null'
    output = run_command(cmd, True)
    logger.debug(output)
    mean_volume_matches = re.findall(r"mean_volume: ([\-\d\.]+) dB", output)
    if (mean_volume_matches):
        mean_volume = float(mean_volume_matches[0])
    else:
        logger.error("could not get mean volume for " + input_file)
        raise SystemExit

    max_volume_matches = re.findall(r"max_volume: ([\-\d\.]+) dB", output)
    if (max_volume_matches):
        max_volume = float(max_volume_matches[0])
    else:
        logger.error("could not get max volume for " + input_file)
        raise SystemExit

    return mean_volume, max_volume


def ffmpeg_adjust_volume(input_file, gain, output):
    global args
    if not args['--force'] and os.path.exists(output):
        logger.warning("output file " + output + " already exists, skipping. Use -f to force overwriting.")
        return

    cmd = FFMPEG_CMD + ' -y -i "' + input_file + '" -vn -sn -filter:a "volume=' + str(gain) + 'dB" -c:a pcm_s16le "' + output + '"'
    output = run_command(cmd, True, args['--dry-run'])


# -------------------------------------------------------------------------------------------------

def main():

    global args

    args = docopt(__doc__, version=str(__version__), options_first=False)

    if args['--debug']:
        ch.setLevel(logging.DEBUG)
    elif args['--verbose']:
        ch.setLevel(logging.INFO)

    logger.debug(args)

    for input_file in args['<input-file>']:
        if not os.path.exists(input_file):
            logger.error("file " + input_file + " does not exist")
            continue

        path, filename = os.path.split(input_file)
        basename = os.path.splitext(filename)[0]
        output_file = os.path.join(path, args['--prefix'] + "-" + basename + ".wav")

        if 'ffmpeg' in FFMPEG_CMD:
            logger.info("reading file " + input_file)

            mean, maximum = ffmpeg_get_mean(input_file)
            logger.warning("mean volume: " + str(mean))
            logger.warning("max volume: " + str(maximum))

            target_level = float(args['--level'])
            if args['--max']:
                adjustment = target_level - maximum
            else:
                adjustment = target_level - mean

            logger.warning("file needs " + str(adjustment) + " dB gain to reach " + str(args['--level']) + " dB")

            if maximum + adjustment > 0:
                logger.warning("adjusting " + input_file + " will lead to clipping of " + str(maximum + adjustment) + "dB")

            ffmpeg_adjust_volume(input_file, adjustment, output_file)

        else:
            # avconv doesn't seem to have a way to measure volume level, so
            # instead we use it to convert to wav, then use a separate programme
            # and then convert back to the desired format.
            # http://askubuntu.com/questions/247961/normalizing-video-volume-using-avconv
            cmd = FFMPEG_CMD + ' -i ' + input_file + ' -c:a pcm_s16le -vn "' + output_file + '"'
            output = run_command(cmd, True, args['--dry-run'])
            cmd = NORMALIZE_CMD + ' "' + output_file + '"'
            output = run_command(cmd, True, args['--dry-run'])
            logger.info(output)


if __name__ == '__main__':
    main()
