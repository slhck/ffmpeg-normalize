#!/usr/bin/env python
"""
ffmpeg-normalize 0.4.1

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
  -p --prefix <prefix>               Prefix for normalized files or output folder name [default: normalized]
  -np --no-prefix                    Write output file without prefix (cannot be used when `--dir` is used)
  -t --threshold <threshold>         dB threshold below which the audio will be not adjusted [default: 0.5]
  -o --dir                           Create an output folder under the input file's directory with the prefix
                                     instead of prefixing the file (does not work if `--no-prefix` is chosen)
  -m --max                           Normalize to the maximum (peak) volume instead of RMS
  -v --verbose                       Enable verbose output
  -n --dry-run                       Show what would be done, do not convert
  -d --debug                         Show debug output
  -u --merge                         Don't create a separate WAV file but update the original file. Use in combination with -p to create a copy
  -a --acodec <acodec>               Set audio codec for ffmpeg (see `ffmpeg -encoders`) to use for output (will be chosen based on format, default pcm_s16le for WAV)
  -r --format <format>               Set format for ffmpeg (see `ffmpeg -formats`) to use for output file [default: wav]
  -e --extra-options <extra-options> Set extra options passed to ffmpeg (e.g. "-b:a 192k" to set audio bitrate)

Examples:
  ffmpeg-normalize -v file.mp3
  ffmpeg-normalize -v *.avi
  ffmpeg-normalize -vuofm -l -5 *.mp4
  ffmpeg-normalize -vu -a libfdk_aac -e "-b:v 192k" *.mkv

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

# -------------------------------------------------------------------------------------------------

logger = logging.getLogger('ffmpeg_normalize')
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# -------------------------------------------------------------------------------------------------

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
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def run_command(cmd, raw=True, dry=False):
    """
    Generic function to run a command.
    Set raw to pass the actual command.
    Set dry to just print and don't actually run.

    Returns stdout + stderr.
    """
    logger.debug("[command] {0}".format(cmd))

    if dry:
        return

    if raw:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
    else:
        p = subprocess.Popen(cmd.split(" "), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    stdout, stderr = p.communicate()

    if p.returncode == 0:
        return (stdout + stderr)
    else:
        logger.error("error running command: {}".format(cmd))
        logger.error(str(stderr))
        raise SystemExit("Failed running a command")

# -------------------------------------------------------------------------------------------------

class InputFile(object):
    """
    Class that holds a file, its streams and adjustments
    """

    def __init__(self, path, args):
        self.args          = args
        self.acodec        = self.args['--acodec']
        self.write_to_dir  = self.args['--dir']
        self.dry_run       = self.args['--dry-run']
        self.extra_options = self.args['--extra-options']
        self.force         = self.args['--force']
        self.format        = self.args['--format']
        self.max           = self.args['--max']
        self.merge         = self.args['--merge']
        self.no_prefix     = self.args['--no-prefix']
        self.prefix        = self.args['--prefix']
        self.target_level  = float(self.args['--level'])
        self.threshold     = float(self.args['--threshold'])

        # Find ffmpeg command in PATH
        self.ffmpeg_cmd = which('ffmpeg')
        if not self.ffmpeg_cmd:
            if which('avconv'):
                logger.error("avconv is not supported anymore. Please install ffmpeg from http://ffmpeg.org instead.")
                raise SystemExit("No ffmpeg installed")
            else:
                raise SystemExit("Could not find ffmpeg in your $PATH")

        self.skip = False # whether the file should be skipped

        self.mean_volume = None
        self.max_volume  = None
        self.adjustment  = None

        self.input_file = path
        self.dir, self.filename = os.path.split(self.input_file)
        self.basename = os.path.splitext(self.filename)[0]

        # by default, the output path is the same as the input file's one
        self.output_file     = None
        self.output_filename = None
        self.output_dir     = self.dir

        self.set_output_filename()

    def set_output_filename(self):
        """
        Set all the required output filenames and paths
        """

        # if merging is enabled, the output filename is the same as the filename
        if self.merge:
            self.output_filename = self.filename
        else:
            # if not merging, we need to create a separate file with a different format
            self.output_filename = self.basename + '.' + self.format

        # prefix is disabled, so we need to make sure we're not writing ot a directory
        if self.no_prefix:
            if self.write_to_dir:
                raise SystemExit("Cannot write to a directory if '--no-prefix' is set.")
        else:
            # if writing to a directory, change the output path by using the prefix
            if self.write_to_dir:
                self.output_dir = os.path.join(self.dir, self.prefix)
            else:
                # if not, the output filename is prefixed (this is the default behavior)
                self.output_filename = self.prefix + "-" + self.output_filename

        # create the output dir if necessary
        if self.output_dir and not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # create the actual file path for the output file
        self.output_file = os.path.join(self.output_dir, self.output_filename)

        logger.debug("writing result in " + self.output_file)

        # some checks
        if not self.force and os.path.exists(self.output_file):
            logger.warning("output file " + self.output_file + " already exists, skipping. Use -f to force overwriting.")
            self.skip = True


    def get_mean(self):
        """
        Use ffmpeg with volumedetect filter to get the mean volume of the input file.
        """
        if sys.platform == 'win32':
            nul = "NUL"
        else:
            nul = "/dev/null"

        cmd = '"' + self.ffmpeg_cmd + '" -i "' + self.input_file + '" -filter:a "volumedetect" -vn -sn -f null ' + nul

        output = run_command(cmd)

        logger.debug(output)

        mean_volume_matches = re.findall(r"mean_volume: ([\-\d\.]+) dB", output)
        if mean_volume_matches:
            self.mean_volume = float(mean_volume_matches[0])
        else:
            raise ValueError("could not get mean volume for " + self.input_file)

        max_volume_matches = re.findall(r"max_volume: ([\-\d\.]+) dB", output)
        if max_volume_matches:
            self.max_volume = float(max_volume_matches[0])
        else:
            raise ValueError("could not get max volume for " + self.input_file)

        logger.info("mean volume: " + str(self.mean_volume))
        logger.info("max volume: " + str(self.max_volume))


    def set_adjustment(self):
        """
        Set the adjustment gain based on chosen option and mean/max volume
        """
        if self.max:
            self.adjustment = 0 + self.target_level - self.max_volume
            logger.info("file needs " + str(self.adjustment) + " dB gain to reach maximum")
        else:
            self.adjustment = self.target_level - self.mean_volume
            logger.info("file needs " + str(self.adjustment) + " dB gain to reach " + str(self.target_level) + " dB")

        if self.max_volume + self.adjustment > 0:
            logger.info("adjusting " + self.filename + " will lead to clipping of " + str(self.max_volume + self.adjustment) + "dB")

        if abs(self.adjustment) <= self.threshold:
            logger.info("gain of " + str(self.adjustment) + " is below threshold, will not adjust file")
            self.skip = True


    def adjust_volume(self):
        """
        Apply gain to the input file and write to the output file or folder.
        """
        if self.skip:
            logger.error("Cannot run adjustment, file should be skipped")

        cmd = '"' + self.ffmpeg_cmd + '" -y -i "' + self.input_file + '" '

        if self.merge:
            # when merging, copy the video and subtitle stream over and apply the audio filter
            cmd += '-strict -2 -c:v copy -c:s copy -filter:a "volume=' + str(self.adjustment) + 'dB" '
            if not self.acodec:
                logger.warn("Merging audio back into original file, but encoder was automatically chosen. Set '--acodec' to overwrite.")
        else:
            # when outputting a file, disable video and subtitles
            cmd += '-vn -sn -filter:a "volume=' + str(self.adjustment) + 'dB" '

        # set codec
        if self.acodec:
            cmd += '-c:a ' + self.acodec + ' '

        # any extra options passed to ffmpeg
        if self.extra_options:
            cmd += self.extra_options + ' '

        cmd += '"' + self.output_file + '"'

        run_command(cmd, dry=self.dry_run)


class FFmpegNormalize(object):
    """
    ffmpeg-normalize class.
    """

    def __init__(self, args):
        # Set arguments
        self.args          = args
        self.debug         = self.args['--debug']
        self.verbose       = self.args['--verbose']

        if self.debug:
            stream_handler.setLevel(logging.DEBUG)
        elif self.verbose:
            stream_handler.setLevel(logging.INFO)

        logger.debug(self.args)

        # Checks
        self.input_files = []
        self.create_input_files(self.args['<input-file>'])


    def create_input_files(self, input_files):
        """
        Remove nonexisting input files
        """
        to_remove = []

        for input_file in input_files:
            if not os.path.exists(input_file):
                logger.error("file " + input_file + " does not exist, will skip")
                to_remove.append(input_file)

        for input_file in to_remove:
            input_files = [f for f in self.input_files if f != input_file]

        self.file_count = len(input_files)

        for input_file in input_files:
            self.input_files.append(InputFile(input_file, self.args))


    def run(self):
        """
        Run the normalization procedures
        """
        count = 0
        for input_file in self.input_files:
            count = count + 1

            if input_file.skip:
                continue

            logger.info("reading file " + str(count) + " of " + str(self.file_count) + " - " + input_file.filename)

            input_file.get_mean()
            input_file.set_adjustment()

            input_file.adjust_volume()
            logger.info("normalized file written to " + input_file.output_file)

# -------------------------------------------------------------------------------------------------

def main():
    args = docopt(__doc__, version=str(__version__), options_first=False)

    ffmpeg_normalize = FFmpegNormalize(args)
    ffmpeg_normalize.run()


if __name__ == '__main__':
    main()
