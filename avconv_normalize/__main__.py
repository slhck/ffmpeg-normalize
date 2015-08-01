#!/usr/bin/env python
#
# Audio normalization script, normalizing media files to WAV output
#
# Requirements: Recent ffmpeg installed on your system (above 2.0 would suffice)
#
# The MIT License (MIT)
#
# Copyright (c) 2014 Werner Robitza
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

import argparse
import subprocess
import os
import re
import logging

logger = logging.getLogger('avconv_normalize')
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
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
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

AVCONV_CMD = which('avconv') or which('ffmpeg') or None

if not AVCONV_CMD:
    raise SystemExit("Could not find ffmpeg or avconv")


def run_command(cmd, raw=False, dry=False):
    cmd = cmd.replace("  ", " ")
    cmd = cmd.replace("  ", " ")
    logger.debug("[command] {0}".format(cmd))

    if dry:
        return

    if raw:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    else:
        p = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE)

    p.communicate()

    if p.returncode == 0:
        return p.stdout.read()
    else:
        return "ERROR!" + p.stderr.read()


def ffmpeg_get_mean(input_file):
    cmd = AVCONV_CMD + ' -i "' + input_file + '" -filter:a "volumedetect" -vn -sn -f null /dev/null'
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
    if not args.force and os.path.exists(output):
        logger.warning("output file " + output + " already exists, skipping. Use -f to force overwriting.")
        return

    cmd = AVCONV_CMD + ' -y -i "' + input_file + '" -vn -sn -filter:a "volume=' + str(gain) + 'dB" -c:a pcm_s16le "' + output + '"'
    output = run_command(cmd, True, args.dry_run)


def print_verbose(message):
    global args
    if args.verbose:
        print(message)

# -------------------------------------------------------------------------------------------------

def main():

    global args

    parser = argparse.ArgumentParser(
        description="""This program normalizes audio to a certain dB level.
                       The default is an RMS-based normalization where the mean is lifted. Peak normalization is
                       possible with the -m/--max option.
                       It takes any audio or video file as input, and writes the audio part as output WAV file."""
        )
    parser.add_argument('-i', '--input', nargs='+', help='Input files to convert', required=True)
    parser.add_argument('-f', '--force', default=False, action="store_true",
                        help='Force overwriting existing files')
    parser.add_argument('-l', '--level', default=-26, help="dB level to normalize to, default: -26 dB")
    parser.add_argument('-p', '--prefix', default="normalized", help="Normalized file prefix, default: normalized")
    parser.add_argument('-m', '--max', default=False, action="store_true", help="Normalize to the maximum (peak) volume instead of RMS")
    parser.add_argument('-v', '--verbose', default=False, action="store_true", help="Enable verbose output")
    parser.add_argument('-n', '--dry-run', default=False, action="store_true", help="Show what would be done, do not convert")
    parser.add_argument('-d', '--debug', default=False, action="store_true", help="Show debug output")

    args = parser.parse_args()

    if args.debug:
        ch.setLevel(logging.DEBUG)
    elif args.debug:
        ch.setLevel(logging.INFO)

    for input_file in args.input:
        if not os.path.exists(input_file):
            logger.error("file " + input_file + " does not exist")
            continue

        path, filename = os.path.split(input_file)
        basename = os.path.splitext(filename)[0]
        output_file = os.path.join(path, args.prefix + "-" + basename + ".wav")

        if 'ffmpeg' in AVCONV_CMD:
            logger.info("reading file " + input_file)

            mean, maximum = ffmpeg_get_mean(input_file)
            logger.warning("mean volume: " + str(mean))
            logger.warning("max volume: " + str(maximum))

            target_level = float(args.level)
            if args.max:
                adjustment = target_level - maximum
            else:
                adjustment = target_level - mean

            logger.warning("file needs " + str(adjustment) + " dB gain to reach " + str(args.level) + " dB")

            if maximum + adjustment > 0:
                logger.warning("adjusting " + input_file + " will lead to clipping of " + str(maximum + adjustment) + "dB")

            ffmpeg_adjust_volume(input_file, adjustment, output_file)

        else:
            # avconv
            # VIDEO_FILE=$1
            # VIDEO_FILE_FIXED=${VIDEO_FILE%.*}-fixed.${VIDEO_FILE##*.}
            # avconv -i $VIDEO_FILE -c:a pcm_s16le -vn audio.wav
            # normalize-audio audio.wav

            cmd = AVCONV_CMD + ' -i ' + input_file + ' -c:a pcm_s16le -vn "' + output_file + '"'
            output = run_command(cmd, True, args.dry_run)
            logger.info(output)


if __name__ == '__main__':
    main()
