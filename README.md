# ffmpeg-normalize

ffmpeg script for normalizing audio.

This program normalizes media files to a certain dB level. The default
is an RMS-based normalization where the mean is lifted or attenuated.
Peak normalization is possible with the `-m` option. EBU R128
normalization is possible with the `-b` option.

It takes any audio or video file as input, and writes the audio part as
output WAV file. The normalized audio can also be merged with the
original.

# Requirements

-   Python
-   ffmpeg from <http://ffmpeg.org/> installed in your \$PATH (3.x or
    above recommended)

# Installation

    pip install ffmpeg-normalize

# Usage

    ffmpeg-normalize [options] <input-file> ...

# Options

Normalization:

- `-l`, `--level <level>`: dB level to normalize to [default: -26]
- `-m`, `--max`: Normalize to the maximum (peak) volume instead of RMS
- `-b`, `--ebu`: Normalize according to EBU R128 (ffmpeg `loudnorm` filter). Note that the sample rate of the input file will be changed, which some players do not support. If you want to set the sample rate to a normal value, use the `-e "-ar 44100"` option.
- `-t`, `--threshold <threshold>`: dB threshold below which the audio will be not adjusted, set to 0 to always normalize file [default: 0.5]

Encoding / Format:

- `-a`, `--acodec <acodec>`: Set audio codec for ffmpeg (see `ffmpeg -encoders`) to use for output (will be chosen based on format, default pcm_s16le for WAV)
- `-r`, `--format <format>`: Set format / file extension for ffmpeg (see `ffmpeg -formats`) to use for output file [default: `wav`]
- `-e`, `--extra-options <extra-options>` Set extra options passed to ffmpeg (e.g. `-b:a 192k` to set audio bitrate)

File Handling:

- `-f`, `--force`: Force overwriting existing files
- `-p`, `--prefix <prefix>`: Prefix for normalized files or output folder name [default: normalized]
- `-x`, `--no-prefix`: Write output file without prefix (cannot be used when `--dir` is used)
- `-o`, `--dir`: Create an output folder under the input file's directory with the prefix instead of prefixing the file (does not work if `--no-prefix` is chosen)
- `-u`, `--merge`: Take original file's streams and merge the normalized audio. Note: This will not overwrite the input file, but output to `normalized-<input>`.

General:

- `-v`, `--verbose`: Enable verbose output
- `-n`, `--dry-run`: Show what would be done, do not convert
- `-d`, `--debug`: Show debug output

# Examples

Normalize a file and write to `normalized-file.wav`:

    ffmpeg-normalize -v file.mp3
    ffmpeg-normalize --verbose *.avi

Normalize a number of AVI files and write to
`normalized-<file>.wav`:

    ffmpeg-normalize -v *.avi
    ffmpeg-normalize --verbose *.avi

Normalize a number of MP4 files to -5 dB peak volume and merge the audio
stream back into the MP4 files, in a new directory called
`normalized`:

    ffmpeg-normalize -vuofm -l -5 *.mp4
    ffmpeg-normalize --verbose --merge --dir --force --max --level -5 *.mp4

Normalize the input file and irrevocably overwrite it:

    ffmpeg-normalize -vuxf input.wav
    ffmpeg-normalize --verbose --merge --no-prefix --force input.wav

Normalize a number of MKV files and merge the audio back in using the
`libfdk_aac` encoder with 192 kBit/s CBR:

    ffmpeg-normalize -vu -a libfdk_aac -e "-b:a 192k" *.mkv
    ffmpeg-normalize --verbose --merge --acodec libfdk_aac --extra-options "-b:a 192k" *.mkv

One user (@pannal) suggested this for an old series with bad sound mixing:

    ffmpeg-normalize --verbose --merge --force --acodec libfdk_aac --ebu \
    --extra-options "-threads 4 -b:a 224k -filter:a 'compand=0|0:1|1:-90/-900|-70/-70|-30/-9|0/-3:6:0:0:0'" *.mkv

# License

The MIT License (MIT)

Copyright (c) 2015-2017 Werner Robitza

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
