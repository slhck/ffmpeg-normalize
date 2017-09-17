#!/usr/bin/env python
"""
ffmpeg-normalize 0.7.2

ffmpeg script for normalizing audio.

This program normalizes media files to a certain dB level. The default is an
RMS-based normalization where the mean is lifted or attenuated. Peak normalization
is possible with the -m option.

It takes any audio or video file as input, and writes the audio part as
output WAV file. The normalized audio can also be merged with the
original.

Usage:
  ffmpeg-normalize [options] <input-file>...

Options:

Normalization:
  -l --level <level>                 dB level to normalize to [default: -26]
  -m --max                           Normalize to the maximum (peak) volume instead of RMS
  -b --ebu                           Normalize according to EBU R128 (ffmpeg `loudnorm` filter).
                                     Note that the sample rate of the input file will be changed,
                                     which some players do not support. If you want to set the
                                     sample rate to a normal value, use the `-e "-ar 44100"`
                                     option.
  -t --threshold <threshold>         dB threshold below which the audio will be not adjusted, set
                                     to 0 to always normalize file [default: 0.5]

Encoding / Format:
  -a --acodec <acodec>               Set audio codec for ffmpeg (see `ffmpeg -encoders`) to use for
                                     output (will be chosen based on format, default pcm_s16le for
                                     WAV)
  -r --format <format>               Set format for ffmpeg (see `ffmpeg -formats`) to use for output
                                     file [default: wav]
  -e --extra-options <extra-options> Set extra options passed to ffmpeg (e.g. `-b:a 192k` to set
                                     audio bitrate)

File Handling:
  -f --force                         Force overwriting existing files
  -p --prefix <prefix>               Prefix for normalized files or output folder name
                                     [default: normalized]
  -x --no-prefix                     Write output file without prefix (cannot be used when `--dir`
                                     is used)
  -o --dir                           Create an output folder under the input file's directory with
                                     the prefix instead of prefixing the file (does not work if
                                     `--no-prefix` is chosen)
  -u --merge                         Take original file's streams and merge the normalized audio.
                                     Note: This will not overwrite the input file, but output to
                                     `normalized-<input>`.

General:
  -v --verbose                       Enable verbose output
  -n --dry-run                       Show what would be done, do not convert
  -d --debug                         Show debug output

Examples:
  ffmpeg-normalize -v file.mp3
  ffmpeg-normalize -v *.avi
  ffmpeg-normalize -vuofm -l -5 *.mp4
  ffmpeg-normalize -vu -a libfdk_aac -e "-b:v 192k" *.mkv

"""
#
# The MIT License (MIT)
#
# Copyright (c) 2015-2017 Werner Robitza
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
import tempfile
import shlex

from docopt import docopt

from . import __version__

# -------------------------------------------------------------------------------------------------

def setup_custom_logger(name, debug=False):
    """
    Create a logger with a certain name and level
    """
    formatter = logging.Formatter(
        fmt='%(levelname)s: %(message)s'
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logging.addLevelName(logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
    logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
    logging.addLevelName(logging.INFO, "\033[1;34m%s\033[1;0m" % logging.getLevelName(logging.INFO))
    logging.addLevelName(logging.DEBUG, "\033[1;35m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))

    logger = logging.getLogger(name)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)
    logger.addHandler(handler)

    return logger


logger = setup_custom_logger('ffmpeg_normalize')

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


def run_command(cmd, raw=False, dry=False):
    """
    Generic function to run a command.
    Set raw to pass the actual command.
    Set dry to just print and don't actually run.

    Returns stdout + stderr.
    """
    logger.debug("Running command: {0}".format(cmd))

    if dry:
        logger.warn("Dry mode specified, not actually running command")
        return

    if raw:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
    else:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    stdout, stderr = p.communicate()

    if p.returncode == 0:
        return (stdout + stderr)
    else:
        logger.error("error running command: {}".format(cmd))
        logger.error(str(stderr))
        sys.exit(1)

# -------------------------------------------------------------------------------------------------

class InputFile(object):
    """
    Class that holds a file, its streams and adjustments
    """

    def __init__(self, path, ffmpeg_normalize):
        self.ffmpeg_normalize = ffmpeg_normalize
        self.uses_tmp_file = False

        if self.ffmpeg_normalize.ebu and ((self.ffmpeg_normalize.target_level > -5.0) or
           (self.ffmpeg_normalize.target_level < -70.0)):
            logger.error("Target levels for EBU R128 must lie between -70 and -5")
            sys.exit(1)

        self.skip = False  # whether the file should be skipped

        self.mean_volume = None
        self.max_volume = None
        self.adjustment = None

        self.input_file = path
        self.dir, self.filename = os.path.split(self.input_file)
        self.basename = os.path.splitext(self.filename)[0]

        # by default, the output path is the same as the input file's one
        self.output_file = None
        self.output_filename = None
        self.output_dir = self.dir

        self.set_output_filename()

    def set_output_filename(self):
        """
        Set all the required output filenames and paths
        """

        if self.ffmpeg_normalize.merge:
            # when merging, output file is the same as input file
            self.output_filename = self.filename
        else:
            # by default, output filename is the input filename, plus the format chosen (default: WAV)
            self.output_filename = os.path.splitext(self.filename)[0] + "." + self.ffmpeg_normalize.output_format

        # prefix is disabled, so we need to make sure we're not writing ot a directory
        if self.ffmpeg_normalize.no_prefix:
            if self.ffmpeg_normalize.write_to_dir:
                logger.error("Cannot write to a directory if '--no-prefix' is set.")
                sys.exit(1)
        else:
            # if writing to a directory, change the output path by using the prefix
            if self.ffmpeg_normalize.write_to_dir:
                self.output_dir = os.path.join(self.dir, self.ffmpeg_normalize.prefix)
            else:
                # if not, the output filename is prefixed (this is the default behavior)
                self.output_filename = self.ffmpeg_normalize.prefix + "-" + self.output_filename

        # create the output dir if necessary
        if self.output_dir and not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        # create the actual file path for the output file
        self.output_file = os.path.join(self.output_dir, self.output_filename)

        logger.debug("writing result in " + self.output_file)

        # if the same file should be used, create temporary file instead
        if self.output_file == self.input_file:
            if not self.ffmpeg_normalize.force:
                logger.warning("Your input file will be overwritten and cannot be recovered. Use -f to force overwriting.")
                self.skip = True
            else:
                self.output_file = tempfile.NamedTemporaryFile(delete=False).name
                self.output_file += os.path.splitext(self.input_file)[1]
                self.uses_tmp_file = True

        # some checks
        if not self.ffmpeg_normalize.force and os.path.exists(self.output_file):
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

        cmd = [self.ffmpeg_normalize.ffmpeg_exe, "-nostdin", "-y", "-i", self.input_file,
               "-filter:a", "volumedetect", "-vn", "-sn", "-f", "null", nul]

        output = run_command(cmd)

        logger.debug("Output from ffmpeg: ")
        logger.debug(output)

        mean_volume_matches = re.findall(r"mean_volume: ([\-\d\.]+) dB", output)
        if mean_volume_matches:
            self.mean_volume = float(mean_volume_matches[0])
        else:
            logger.error("could not get mean volume for " + self.input_file)
            sys.exit(1)

        max_volume_matches = re.findall(r"max_volume: ([\-\d\.]+) dB", output)
        if max_volume_matches:
            self.max_volume = float(max_volume_matches[0])
        else:
            logger.error("could not get max volume for " + self.input_file)
            sys.exit(1)

        logger.info("mean volume: " + str(self.mean_volume))
        logger.info("max volume: " + str(self.max_volume))

    def set_adjustment(self):
        """
        Set the adjustment gain based on chosen option and mean/max volume
        """
        if self.ffmpeg_normalize.use_max:
            self.adjustment = 0 + self.ffmpeg_normalize.target_level - self.max_volume
            logger.info("file needs " + str(self.adjustment) + " dB gain to reach maximum")
        else:
            self.adjustment = self.ffmpeg_normalize.target_level - self.mean_volume
            logger.info("file needs " + str(self.adjustment) + " dB gain to reach " + str(self.ffmpeg_normalize.target_level) + " dB")

        if self.max_volume + self.adjustment > 0:
            logger.info("adjusting " + self.filename + " will lead to clipping of " + str(self.max_volume + self.adjustment) + "dB")

        if self.ffmpeg_normalize.threshold > 0 and abs(self.adjustment) <= self.ffmpeg_normalize.threshold:
            logger.info("gain of " + str(self.adjustment) + " is below threshold, will not adjust file")
            self.skip = True

    def adjust_volume(self):
        """
        Apply gain to the input file and write to the output file or folder.
        """
        if self.skip:
            logger.error("Cannot run adjustment, file should be skipped")
            return

        cmd = [self.ffmpeg_normalize.ffmpeg_exe, "-nostdin", "-y", "-i", self.input_file]

        if self.ffmpeg_normalize.ebu:
            chosen_filter = 'loudnorm=' + str(self.ffmpeg_normalize.target_level)
        else:
            chosen_filter = 'volume=' + str(self.adjustment) + 'dB'

        if self.ffmpeg_normalize.merge:
            # when merging, copy the video and subtitle stream over and apply the audio filter
            cmd.extend(["-strict", "-2", "-c:v", "copy", "-c:s", "copy",
                        "-map_metadata", "0", "-map", "0", "-filter:a", chosen_filter])
            if not self.ffmpeg_normalize.acodec:
                logger.warn("Merging audio with the original file, but encoder was automatically chosen. Set '--acodec' to overwrite.")
        else:
            # when outputting a file, disable video and subtitles
            cmd.extend(["-vn", "-sn", "-filter:a", chosen_filter])

        # set codec
        if self.ffmpeg_normalize.acodec:
            cmd.extend(["-c:a", self.ffmpeg_normalize.acodec])

        # any extra options passed to ffmpeg
        if self.ffmpeg_normalize.extra_options:
            cmd.extend(shlex.split(self.ffmpeg_normalize.extra_options))

        cmd.extend([self.output_file])

        run_command(cmd, dry=self.ffmpeg_normalize.dry_run)

    def move_tmp_file(self):
        """
        Move back the temporary file to the original, overwriting it
        """
        logger.debug("Moving " + str(self.output_file) + " to " + str(self.input_file))
        os.rename(self.output_file, self.input_file)

class FFmpegNormalize(object):
    """
    ffmpeg-normalize class.
    """

    def __init__(self, input_files, acodec, write_to_dir, dry_run, extra_options, force, output_format,
                 use_max, ebu, merge, no_prefix, prefix, target_level, threshold):
        self.acodec = acodec
        self.write_to_dir = write_to_dir
        self.dry_run = dry_run
        self.extra_options = extra_options
        self.force = force
        self.output_format = output_format
        self.use_max = use_max
        self.ebu = ebu
        self.merge = merge
        self.no_prefix = no_prefix
        self.prefix = prefix
        self.target_level = target_level
        self.threshold = threshold

        # Checks
        # Find ffmpeg command in PATH
        self.ffmpeg_exe = which('ffmpeg')
        if not self.ffmpeg_exe:
            if which('avconv'):
                logger.error("avconv is not supported anymore. Please install ffmpeg from http://ffmpeg.org instead.")
                logger.error("No ffmpeg installed")
                sys.exit(1)
            else:
                logger.error("Could not find ffmpeg in your $PATH. Please install ffmpeg from http://ffmpeg.org")
                sys.exit(1)

        if self.use_max and self.ebu:
            logger.error("--max and --ebu are mutually exclusive.")
            sys.exit(1)

        self.input_files = []
        self.create_input_files(input_files)

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
            self.input_files.append(InputFile(input_file, self))

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

            if not self.ebu:
                input_file.get_mean()
                input_file.set_adjustment()

            if input_file.skip:
                return

            input_file.adjust_volume()

            if input_file.uses_tmp_file:
                input_file.move_tmp_file()
                logger.info("normalized file written to " + input_file.input_file)
            else:
                logger.info("normalized file written to " + input_file.output_file)

# -------------------------------------------------------------------------------------------------

def main():
    args = docopt(__doc__, version=str(__version__), options_first=False)

    if args['--debug']:
        logger.setLevel(logging.DEBUG)
    elif args['--verbose']:
        logger.setLevel(logging.INFO)

    ffmpeg_normalize = FFmpegNormalize(
        input_files=args['<input-file>'],
        acodec=args['--acodec'],
        write_to_dir=args['--dir'],
        dry_run=args['--dry-run'],
        extra_options=args['--extra-options'],
        force=args['--force'],
        output_format=args['--format'],
        use_max=args['--max'],
        ebu=args['--ebu'],
        merge=args['--merge'],
        no_prefix=args['--no-prefix'],
        prefix=args['--prefix'],
        target_level=float(args['--level']),
        threshold=float(args['--threshold']),
    )
    ffmpeg_normalize.run()


if __name__ == '__main__':
    main()
