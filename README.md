# ffmpeg-normalize

[![Build Status](https://travis-ci.org/slhck/ffmpeg-normalize.svg?branch=master)](https://travis-ci.org/slhck/ffmpeg-normalize)

A utility for batch-normalizing audio using ffmpeg.

This program normalizes media files to a certain LUFS level using the EBU R128 loudness normalization procedure. It can also perform RMS-based normalization (where the mean is lifted or attenuated), or peak normalization to a certain target level.

Batch processing of several input files is possible, including video files.

## Requirements

-   Python 2.7 or 3
-   ffmpeg v3.1 or above from <http://ffmpeg.org/> installed in your \$PATH

## Installation

    pip3 install ffmpeg-normalize

## Usage

    ffmpeg-normalize [-h] [-o OUTPUT [OUTPUT ...]] [-of OUTPUT_FOLDER] [-f]
                    [-d] [-v] [-n] [--version] [-nt {ebu,rms,peak}]
                    [-t TARGET_LEVEL] [-lrt LOUDNESS_RANGE_TARGET]
                    [-tp TRUE_PEAK] [--offset OFFSET] [--dual-mono]
                    [-c:a AUDIO_CODEC] [-b:a AUDIO_BITRATE]
                    [-ar SAMPLE_RATE] [-vn] [-c:v VIDEO_CODEC] [-sn] [-mn]
                    [-e EXTRA_OUTPUT_OPTIONS] [-ofmt OUTPUT_FORMAT]
                    [-ext EXTENSION]
                    input [input ...]

For more information, run `ffmpeg-normalize -h`, or read on.

## Description

The program takes a number of input files and, by default, writes them to a folder called `normalized`, using an `.mkv` container. You can specify an output file name for each input file with the `-o` option. In this case, the container format will be inferred from the file name extension.

By default, all streams from the input file will be written to the output file. For example, if your input is a video with two language tracks and a subtitle track, both audio tracks will be normalized independently. The video and subtitle tracks will be copied over to the output file.

**Important Note:** The default audio encoding method is uncompressed PCM to avoid introducing compression artifacts. This will result in a much higher bitrate than you might want, for example if your input files are MP3s. Some containers (like MP4) also cannot handle PCM audio. If you want to use such containers and/or keep the file size down, use `-c:a` and specify an audio codec (e.g., `-c:a aac` for ffmpeg's built-in AAC encoder).

## Examples

Normalize two WAV files and write them to the specified output files with uncompressed PCM WAV as audio codec:

    ffmpeg-normalize file1.wav file2.wav -o file1-normalized.wav -o file2-normalized.wav

Normalize a number of videos in the current folder and write them to a folder called `normalized`, converting all audio streams to AAC with 192 kBit/s.

    ffmpeg-normalize *.mkv -c:a aac -b:a 192k

Instead of EBU R128, one might just want to use simple peak normalization to 0 dB:

    ffmpeg-normalize test.wav --normalization-type peak --target-level 0 --output normalized.wav
    ffmpeg-normalize test.wav -nt peak -t 0 -o normalized.wav

You can (if you really need to!) also overwrite your input file. Warning, this will destroy data:

    ffmpeg-normalize input.mp4 -o input.mp4 -f

If you need some fancy extra options, such as setting `vbr` for the `libfdk_aac` encoder, pass them to the `-e`/`--extra-options` argument:

    ffmpeg-normalize input.m4a -c:a libfdk_aac -e '["vbr": "3"]' -o output.m4a

Further examples? Please submit a PR so I can collect them.

## Detailed Options

File Input/output:

- `input`: Input media file(s)

- `-o OUTPUT [OUTPUT ...], --output OUTPUT [OUTPUT ...]`: Output file names.

    Will be applied per input file.

    If no output file name is specified for an input file, the output files
    will be written to the default output folder with the name `<input>.wav`.

- `-of OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER`: Output folder (default: `normalized`)

    This folder will be used for input files that have no explicit output name specified.

File Input/Output:

- `-f, --force`: Force overwrite existing files

- `-d, --debug`: Print debugging output

- `-v, --verbose`: Print verbose output

- `-n, --dry-run`: Do not run normalization, only print what would be done

- `--version`: Print version and exit

Normalization:

- `-nt {ebu,rms,peak}, --normalization-type {ebu,rms,peak}`: Normalization type (default: `ebu`).

    EBU normalization performs two passes and normalizes according to EBU R128.

    RMS-based normalization brings the input file to the specified RMS level.

    Peak normalization brings the signal to the specified peak level.

- `-t TARGET_LEVEL, --target-level TARGET_LEVEL`: Normalization target level in dB/LUFS (default: -23).

    For EBU normalization, it corresponds to Integrated Loudness Target in LUFS. The range is -70.0 - -5.0.

    Otherwise, the range is -99 to 0.

Ebu R128 Normalization:

- `-lrt LOUDNESS_RANGE_TARGET, --loudness-range-target LOUDNESS_RANGE_TARGET`: EBU Loudness Range Target in LUFS (default: 7.0).

    Range is 1.0 - 20.0.

- `-tp TRUE_PEAK, --true-peak TRUE_PEAK`: EBU Maximum True Peak in dBTP (default: -2.0).

    Range is -9.0 - +0.0.

- `--offset OFFSET`: EBU Offset Gain (default: 0.0).

    The gain is applied before the true-peak limiter.
    Range is -99.0 - +99.0.

- `--dual-mono`: Treat mono input files as "dual-mono".

    If a mono file is intended for playback on a stereo system, its EBU R128 measurement will be perceptually incorrect. If set, this option will compensate for this effect. Multi-channel input files are not affected by this option.

Audio Encoding:

- `-c:a AUDIO_CODEC, --audio-codec AUDIO_CODEC`: Audio codec to use for output files.

    See `ffmpeg -encoders` for a list.

    Will use PCM audio with input stream bit depth by default.

- `-b:a AUDIO_BITRATE, --audio-bitrate AUDIO_BITRATE`: Audio bitrate in bits/s, or with K suffix.

    If not specified, will use codec default.

- `-ar SAMPLE_RATE, --sample-rate SAMPLE_RATE`: Audio sample rate to use for output files in Hz.

    Will use input sample rate by default.

Other Encoding Options:

- `-vn, --video-disable`: Do not write video streams to output

- `-c:v VIDEO_CODEC, --video-codec VIDEO_CODEC`: Video codec to use for output files (default: 'copy').

    See `ffmpeg -encoders` for a list.

    Will attempt to copy video codec by default.

- `-sn, --subtitle-disable`: Do not write subtitle streams to output

- `-mn, --metadata-disable`: Do not write metadata to output

Output Format:

- `-e EXTRA_OUTPUT_OPTIONS, --extra-output-options EXTRA_OUTPUT_OPTIONS`: Extra output options list.

    Must be a list of ffmpeg command line arguments without leading dashes. Wrap in quotes to prevent shell expansion and to preserve literal quotes inside string.

    Example: `-e '[ "-vbr", "3" ]'`

- `-ofmt OUTPUT_FORMAT, --output-format OUTPUT_FORMAT`: Media format to use for output file(s).

    See `ffmpeg -formats` for a list.

    If not specified, the format will be inferred by ffmpeg from the output file name. If the output file name is not explicitly specified, the extension will govern the format (see '--extension' option).

- `-ext EXTENSION, --extension EXTENSION`: Output file extension to use for output files that were not explicitly specified. (Default: `mkv`)

The program additionally respects environment variables:

- `TMP` / `TEMP` / `TEMPDIR`

    Sets the path to the temporary directory in which files are
    stored before being moved to the final output directory.
    Note: You need to use full paths.

- `FFMPEG_PATH`

    Sets the full path to an `ffmpeg` executable other than
    the system default.


## FAQ

### After updating, this program does not work as expected anymore!

You are probably using a 0.x version of this program. There are significant changes to the command line arguments and inner workings of this program, so please  adapt your scripts to the new one. Those changes were necessary to address a few issues that kept piling up; leaving the program as-is would have made it hard to extend it. You can continue using the old version (find it under *Releases* on GitHub or request the specific version from PyPi), but it will not be supported anymore.

### The program doesn't work because the "loudnorm" filter can't be found

Make sure you run ffmpeg v3.1 or higher. Many distributions package outdated ffmpeg 2.x versions, or (even worse), Libav's `ffmpeg` disguising as a real `ffmpeg` from the FFmpeg project.

You can always download a static build from [their website](http://ffmpeg.org/download.html) and use that.

If you have to use an outdated ffmpeg version, you can only use `rms` or `peak` as normalization types, but I can't promise that the program will work correctly.

### Should I use this to normalize my music collection?

When you run `ffmpeg-normalize` and re-encode files with MP3 or AAC, you will inevitably introduce [generation loss](https://en.wikipedia.org/wiki/Generation_loss). Therefore, I do not recommend running this on your precious music collection, unless you have a backup of the originals or accept potential quality reduction. If you just want to normalize the subjective volume of the files without changing the actual content, consider using [MP3Gain](http://mp3gain.sourceforge.net/) and [aacgain](http://aacgain.altosdesign.com/).

### The conversion does not work and I get a cryptic ffmpeg error!

One possible reason is that the input file contains some streams that cannot be mapped to the output file. Examples:

- You are trying to normalize a movie file, writing to a `.wav` or `.mp3` file. WAV/MP3 files only support audio. Disable video and subtitles with `-vn` and `-sn`.

- You are trying to normalize a file, writing to an `.mp4` container. MP4 does not support PCM audio. Make sure that your audio codec is set (e.g. `-c:a aac`).

The default output container is `.mkv` as it will support most input stream types. If you want a different output container, make sure that it supports your input file's video, audio, and subtitle streams (if any).

Also, if there is some other broken metadata, you can try to disable copying over of metadata with `-mn`.

### What are the different normalization algorithms?

- **EBU R128** is an EBU standard that is commonly used in the broadcasting world. The normalization is performed using a psychoacoustic model that targets a subjective loudness level measured in LUFS (Loudness Unit Full Scale). R128 is subjectively more accurate than any peak or RMS-based normalization. More info on R128 can be found in the [official document](https://tech.ebu.ch/docs/r/r128.pdf) and [the `loudnorm` filter description](http://k.ylo.ph/2016/04/04/loudnorm.html) by its original author.

- **Peak Normalization** analyzes the peak signal level in dBFS and increases the volume of the input signal such that the maximum in the output is 0 dB (or any other chosen threshold). Since spikes in the signal can cause high volume peaks, peak normalization might still result in files that are subjectively quieter than other, non-peak-normalized files.

- **RMS-based Normalization** analyzes the [RMS power](https://en.wikipedia.org/wiki/Root_mean_square#Average_power) of the signal and changes the volume such that a new RMS target is reached. Otherwise it works similar to peak normalization.

### Couldn't I just run `loudnorm` with ffmpeg?

You absolutely can. However, you can get better accuracy and linear normalization with two passes of the filter. Since ffmpeg does not allow you to automatically run these two passes, you have to do it yourself and parse the output values from the first run. If this program is too over-engineered for you, you could also use an approach such as featured [in this Ruby script](https://gist.github.com/kylophone/84ba07f6205895e65c9634a956bf6d54) that performs the two `loudnorm` passes.

### Can I buy you a beer / coffee / random drink?

If you found this program useful and feel like giving back, feel free to send a donation [via PayPal](https://paypal.me/slhck).

# License

The MIT License (MIT)

Copyright (c) 2015-2018 Werner Robitza

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
