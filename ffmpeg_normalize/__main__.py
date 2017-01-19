#!/usr/bin/env python
"""
ffmpeg-normalize 0.2.5

ffmpeg script for normalizing audio.

This program normalizes media files to a certain dB level. The default is an
RMS-based normalization where the mean is lifted. Peak normalization is
possible with the -m option.

It takes any audio or video file as input, and writes the audio part as
output WAV file. The normalized audio can also be merged with the
original.

Usage:
  ffmpeg-normalize [options] <input-file>...

Options:
  -f --force                         Force overwriting existing files
  -l --level <level>                 dB level to normalize to [default: -26]
  -p --prefix <prefix>               Normalized file prefix [default: normalized]
  -np --no-prefix                    Write output file without prefix
  -t --threshold <threshold>         dB threshold below which the audio will be not adjusted [default: 0.5]
  -o --dir                           Create an output folder in stead of prefixing the file
  -m --max                           Normalize to the maximum (peak) volume instead of RMS
  -v --verbose                       Enable verbose output
  -n --dry-run                       Show what would be done, do not convert
  -d --debug                         Show debug output
  -u --merge                         Don't create a separate WAV file but update the original file. Use in combination with -p to create a copy
  -a --acodec <acodec>               Set audio codec for ffmpeg (see "ffmpeg -encoders") when merging. If not set, default from ffmpeg will be used.
  -e --extra-options <extra-options> Set extra options passed to ffmpeg (e.g. "-b:a 192k" to set audio bitrate)

Examples:
  ffmpeg-normalize -v file.mp3
  ffmpeg-normalize -v *.avi
  ffmpeg-normalize -u -v -o -f -m -l -5 *.mp4
  ffmpeg-normalize -u -v -a libfdk_aac -e "-b:v 192k" *.mkv

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

import subprocess
import os
import re
import sys
import logging

from docopt import docopt

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
    logger.debug("[command] {0}".format(cmd))

    if dry:
        return

    if raw:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    else:
        p = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = p.communicate()

    if p.returncode == 0:
        return stdout + stderr
    else:
        logger.error("error running command: {}".format(cmd))
        logger.error(str(stderr))
        raise StandardError


def ffmpeg_get_mean(input_file):
    cmd = '"' + FFMPEG_CMD + '" -i "' + input_file + '" -filter:a "volumedetect" -vn -sn -f null /dev/null'
    try:
        output = run_command(cmd, True)
    except Exception as e:
        raise e
    logger.debug(output)
    mean_volume_matches = re.findall(r"mean_volume: ([\-\d\.]+) dB", output)
    if (mean_volume_matches):
        mean_volume = float(mean_volume_matches[0])
    else:
        logger.error("could not get mean volume for " + input_file)
        raise ValueError("could not get mean volume for " + input_file)

    max_volume_matches = re.findall(r"max_volume: ([\-\d\.]+) dB", output)
    if (max_volume_matches):
        max_volume = float(max_volume_matches[0])
    else:
        logger.error("could not get max volume for " + input_file)
        raise ValueError("could not get max volume for " + input_file)

    return mean_volume, max_volume


def ffmpeg_adjust_volume(input_file, gain, output):
    global args

    if args['--merge']:
        cmd = '"' + FFMPEG_CMD + '" -y -i "' + input_file + '" -strict -2 -vcodec copy -af "volume=' + str(gain) + 'dB"'
        if args['--acodec']:
            cmd += ' -codec:a ' + args['--acodec'] + ' '
        if args['--extra-options']:
            cmd += ' ' + args['--extra-options'] + ' '
        cmd += ' "' + output + '"'
    else:
        cmd = FFMPEG_CMD + ' -y -i "' + input_file + '" -vn -sn -filter:a "volume=' + str(gain) + 'dB" -c:a pcm_s16le "' + output + '"'

    try:
        output = run_command(cmd, True, args['--dry-run'])
    except:
        logger.error("Couldn't convert " + input_file)
        raise StandardError


# -------------------------------------------------------------------------------------------------

def main():
    global args

    args = docopt(__doc__, version=str(__version__), options_first=False)

    if args['--debug']:
        ch.setLevel(logging.DEBUG)
    elif args['--verbose']:
        ch.setLevel(logging.INFO)

    logger.debug(args)

    count = 0
    for input_file in args['<input-file>']:
        count = count + 1
        if not os.path.exists(input_file):
            logger.error("file " + input_file + " does not exist")
            continue

        path, filename = os.path.split(input_file)
        basename = os.path.splitext(filename)[0]

        output_path = path

        if args['--merge']:
            output_filename = filename
        else:
            output_filename = basename + ".wav"

        if args['--no-prefix']:
            if args['--dir']:
                logger.error("Cannot write to directory if '--no-prefix' is set.")
                raise StandardError
        else:
            if args['--dir']:
                output_path = os.path.join(path, args['--prefix'])
            else:
                output_filename = args['--prefix'] + "-" + output_filename

        if output_path and not os.path.exists(output_path):
            os.makedirs(output_path)

        output_file = os.path.join(output_path, output_filename)

        logger.debug("writing result in " + output_file)

        if not args['--force'] and os.path.exists(output_file):
            logger.warning("output file " + output_file + " already exists, skipping. Use -f to force overwriting.")
            continue

        if 'ffmpeg' in FFMPEG_CMD:
            logger.info("reading file " + str(count) + " of " + str(len(args['<input-file>'])) + " - " + input_file)

            try:
                mean, maximum = ffmpeg_get_mean(input_file)
            except Exception as e:
                continue # with next file

            logger.info("mean volume: " + str(mean))
            logger.info("max volume: " + str(maximum))

            target_level = float(args['--level'])
            if args['--max']:
                adjustment = 0 + target_level - maximum
                logger.info("file needs " + str(adjustment) + " dB gain to reach maximum")
            else:
                adjustment = target_level - mean
                logger.info("file needs " + str(adjustment) + " dB gain to reach " + str(args['--level']) + " dB")

            if maximum + adjustment > 0:
                logger.info("adjusting " + input_file + " will lead to clipping of " + str(maximum + adjustment) + "dB")

            if abs(adjustment) <= float(args['--threshold']):
                logger.info("gain = " + str(adjustment) + ", will not adjust file")
                continue

            try:
                ffmpeg_adjust_volume(input_file, adjustment, output_file)
            except Exception as e:
                continue

            logger.info("normalized file written to " + output_file)


        else:
            # avconv doesn't seem to have a way to measure volume level, so
            # instead we use it to convert to wav, then use a separate programme
            # and then convert back to the desired format.
            # http://askubuntu.com/questions/247961/normalizing-video-volume-using-avconv

            logger.warning("avconv support is limited. Install ffmpeg from http://ffmpeg.org/download.html instead!")

            cmd = FFMPEG_CMD + ' -i ' + input_file + ' -c:a pcm_s16le -vn "' + output_file + '"'
            output = run_command(cmd, True, args['--dry-run'])
            cmd = NORMALIZE_CMD + ' "' + output_file + '"'
            output = run_command(cmd, True, args['--dry-run'])
            logger.info(output)


if __name__ == '__main__':
    main()
