# ffmpeg-normalize

[![Build Status](https://travis-ci.org/slhck/ffmpeg-normalize.svg?branch=master)](https://travis-ci.org/slhck/ffmpeg-normalize)
[![PyPI version](https://img.shields.io/pypi/v/ffmpeg-normalize.svg)](https://img.shields.io/pypi/v/ffmpeg-normalize)

A utility for batch-normalizing audio using ffmpeg.

This program normalizes media files to a certain loudness level using the EBU R128 loudness normalization procedure. It can also perform RMS-based normalization (where the mean is lifted or attenuated), or peak normalization to a certain target level.

Batch processing of several input files is possible, including video files.

Contents:

- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Description](#description)
- [Examples](#examples)
- [Detailed Options](#detailed-options)
    - [File Input/Output](#file-inputoutput)
    - [General](#general)
    - [Normalization](#normalization)
    - [EBU R128 Normalization](#ebu-r128-normalization)
    - [Audio Encoding](#audio-encoding)
    - [Other Encoding Options](#other-encoding-options)
    - [Output Format](#output-format)
    - [Environment Variables](#environment-variables)
- [FAQ](#faq)

-------------

## Requirements

-   Python 3.x
-   ffmpeg v3.1 or above from <http://ffmpeg.org/> installed in your \$PATH

## Installation

    pip3 install ffmpeg-normalize

Or download this repository, then run `pip install .`.

## Usage

    ffmpeg-normalize input [input ...]
                [-h]
                [-o OUTPUT [OUTPUT ...]] [-of OUTPUT_FOLDER]
                [-f] [-d] [-v] [-q] [-n] [-pr]
                [--version]
                [-nt {ebu,rms,peak}] [-t TARGET_LEVEL] [-p]
                [-lrt LOUDNESS_RANGE_TARGET] [-tp TRUE_PEAK] [--offset OFFSET] [--dual-mono]
                [-c:a AUDIO_CODEC] [-b:a AUDIO_BITRATE] [-ar SAMPLE_RATE] [-koa]
                [-prf PRE_FILTER] [-pof POST_FILTER]
                [-vn] [-c:v VIDEO_CODEC]
                [-sn] [-mn] [-cn]
                [-ei EXTRA_INPUT_OPTIONS] [-e EXTRA_OUTPUT_OPTIONS]
                [-ofmt OUTPUT_FORMAT]
                [-ext EXTENSION]

For more information, run `ffmpeg-normalize -h`, or read on.

## Description

Please read this section for a high level introduction.

**What does the program do?**

The program takes one or more input files and, by default, writes them to a folder called `normalized`, using an `.mkv` container. All audio streams will be normalized so that they have the same (perceived) volume.

**How do I specify the input?**

Just give the program one or more input files as arguments. It works with most media files.

**How do I specify the output?**

You can specify one output file name for each input file with the `-o` option. In this case, the container format (e.g. `.wav`) will be inferred from the file name extension that you've given.

Example:

```
ffmpeg-normalize 1.wav 2.wav -o 1n.wav 2n.wav
```

If you don't specify the output file name for an input file, the container format will be MKV, and the output will be written to `normalized/<input>.mkv`.

Using the `-ext` option, you can supply a different output extension common to all output files, e.g. `-ext m4a`.

**What will get normalized?**

By default, all streams from the input file will be written to the output file. For example, if your input is a video with two language tracks and a subtitle track, both audio tracks will be normalized independently. The video and subtitle tracks will be copied over to the output file.

**How will the normalization be done?**

The normalization will be performed with the [`loudnorm` filter](http://ffmpeg.org/ffmpeg-filters.html#loudnorm) from FFmpeg, which was [originally written by Kyle Swanson](https://k.ylo.ph/2016/04/04/loudnorm.html). It will bring the audio to a specified target level. This ensures that multiple files normalized with this filter will have the same perceived loudness.

**What codec is chosen?**

The default audio encoding method is uncompressed PCM (`pcm_s16le`) to avoid introducing compression artifacts. This will result in a much higher bitrate than you might want, for example if your input files are MP3s.

Some containers (like MP4) also cannot handle PCM audio. If you want to use such containers and/or keep the file size down, use `-c:a` and specify an audio codec (e.g., `-c:a aac` for ffmpeg's built-in AAC encoder).

## Examples

Normalize two WAV files and write them to the specified output files with uncompressed PCM WAV as audio codec:

    ffmpeg-normalize file1.wav file2.wav -o file1-normalized.wav file2-normalized.wav

Normalize a number of videos in the current folder and write them to a folder called `normalized`, converting all audio streams to AAC with 192 kBit/s.

    ffmpeg-normalize *.mkv -c:a aac -b:a 192k

For Windows, the above would be written as a loop:

    for %%f in ("*.mkv") do ffmpeg-normalize "%%f" -c:a aac -b:a 192k

Normalize an MP3 file and write an MP3 file (you have to explicitly specify the encoder):

    ffmpeg-normalize input.mp3 -c:a libmp3lame -b:a 320k -o output.mp3

Normalize many files, keeping PCM audio, but choosing a different container:

    ffmpeg-normalize *.wav -c:a pcm_s16le -ext aif

Instead of EBU R128, one might just want to use simple peak normalization to 0 dB:

    ffmpeg-normalize test.wav --normalization-type peak --target-level 0 --output normalized.wav
    ffmpeg-normalize test.wav -nt peak -t 0 -o normalized.wav

You can (if you really need to!) also overwrite your input file. Warning, this will destroy data:

    ffmpeg-normalize input.mp4 -o input.mp4 -f

If you need some fancy extra options, such as setting `vbr` for the `libfdk_aac` encoder, pass them to the `-e`/`--extra-options` argument:

    ffmpeg-normalize input.m4a -c:a libfdk_aac -e='-vbr 3' -o output.m4a

You can check the statistics of a file to verify the levels — pass `-n` to avoid running the normalization:

    ffmpeg-normalize input.wav -p -n -f
    [
        {
            "input_file": "input.wav",
            "output_file": "normalized/input.mkv",
            "stream_id": 0,
            "ebu": {
                "input_i": "-6.74",
                "input_tp": "0.45",
                "input_lra": "6.30",
                "input_thresh": "-16.98",
                "output_i": "-22.20",
                "output_tp": "-11.27",
                "output_lra": "5.60",
                "output_thresh": "-32.34",
                "normalization_type": "dynamic",
                "target_offset": "-0.80"
            },
            "mean": null,
            "max": null
        }
    ]

Further examples? [Add them to the wiki.](https://github.com/slhck/ffmpeg-normalize/wiki/examples)

## Detailed Options

### File Input/Output

- `input`: Input media file(s)

- `-o OUTPUT [OUTPUT ...], --output OUTPUT [OUTPUT ...]`: Output file names.

    Will be applied per input file.

    If no output file name is specified for an input file, the output files
    will be written to the default output folder with the name `<input>.<ext>`, where `<ext>` is the output extension (see `-ext` option).

    Example: `ffmpeg-normalize 1.wav 2.wav -o 1n.wav 2n.wav`

- `-of OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER`: Output folder (default: `normalized`)

    This folder will be used for input files that have no explicit output name specified.

### General

- `-f, --force`: Force overwrite existing files

- `-d, --debug`: Print debugging output

- `-v, --verbose`: Print verbose output

- `-q, --quiet`: Only print errors

- `-n, --dry-run`: Do not run normalization, only print what would be done

- `-pr`, `--progress`: Show progress bar for files and streams

- `--version`: Print version and exit

### Normalization

- `-nt {ebu,rms,peak}, --normalization-type {ebu,rms,peak}`: Normalization type (default: `ebu`).

    EBU normalization performs two passes and normalizes according to EBU R128.

    RMS-based normalization brings the input file to the specified RMS level.

    Peak normalization brings the signal to the specified peak level.

- `-t TARGET_LEVEL, --target-level TARGET_LEVEL`: Normalization target level in dB/LUFS (default: -23).

    For EBU normalization, it corresponds to Integrated Loudness Target in LUFS. The range is -70.0 - -5.0.

    Otherwise, the range is -99 to 0.

- `-p, --print-stats`: Print first pass loudness statistics formatted as JSON to stdout.

### EBU R128 Normalization

- `-lrt LOUDNESS_RANGE_TARGET, --loudness-range-target LOUDNESS_RANGE_TARGET`: EBU Loudness Range Target in LUFS (default: 7.0).

    Range is 1.0 - 20.0.

- `-tp TRUE_PEAK, --true-peak TRUE_PEAK`: EBU Maximum True Peak in dBTP (default: -2.0).

    Range is -9.0 - +0.0.

- `--offset OFFSET`: EBU Offset Gain (default: 0.0).

    The gain is applied before the true-peak limiter in the first pass only. The offset for the second pass will be automatically determined based on the first pass statistics.

    Range is -99.0 - +99.0.

- `--dual-mono`: Treat mono input files as "dual-mono".

    If a mono file is intended for playback on a stereo system, its EBU R128 measurement will be perceptually incorrect. If set, this option will compensate for this effect. Multi-channel input files are not affected by this option.

### Audio Encoding

- `-c:a AUDIO_CODEC, --audio-codec AUDIO_CODEC`: Audio codec to use for output files.

    See `ffmpeg -encoders` for a list.

    Will use PCM audio with input stream bit depth by default.

- `-b:a AUDIO_BITRATE, --audio-bitrate AUDIO_BITRATE`: Audio bitrate in bits/s, or with K suffix.

    If not specified, will use codec default.

- `-ar SAMPLE_RATE, --sample-rate SAMPLE_RATE`: Audio sample rate to use for output files in Hz.

    Will use input sample rate by default, except for EBU normalization, which will change the input sample rate to 192 kHz.

- `-koa, --keep-original-audio`: Copy original, non-normalized audio streams to output file

- `-prf PRE_FILTER, --pre-filter PRE_FILTER`: Add an audio filter chain before applying normalization.

    Multiple filters can be specified by comma-separating them.

- `-pof POST_FILTER, --post-filter POST_FILTER`: Add an audio filter chain after applying normalization.

    Multiple filters can be specified by comma-separating them.

    For EBU, the filter will be applied during the second pass.

### Other Encoding Options

- `-vn, --video-disable`: Do not write video streams to output

- `-c:v VIDEO_CODEC, --video-codec VIDEO_CODEC`: Video codec to use for output files (default: 'copy').

    See `ffmpeg -encoders` for a list.

    Will attempt to copy video codec by default.

- `-sn, --subtitle-disable`: Do not write subtitle streams to output

- `-mn, --metadata-disable`: Do not write metadata to output

- `-cn, --chapters-disable`: Do not write chapters to output


### Input/Output Format

- `-ei EXTRA_INPUT_OPTIONS, --extra-input-options EXTRA_INPUT_OPTIONS`: Extra input options list.

    A list of extra ffmpeg command line arguments valid for the input, applied before ffmpeg's `-i`.

    You can either use a JSON-formatted list (i.e., a list of comma-separated, quoted elements within square brackets), or a simple string of space-separated arguments.

    If JSON is used, you need to wrap the whole argument in quotes to prevent shell expansion and to preserve literal quotes inside the string. If a simple string is used, you need to specify the argument with `-e=`.

    Examples: `-e '[ "-f", "mpegts" ]'` or `-e="-f mpegts"`

- `-e EXTRA_OUTPUT_OPTIONS, --extra-output-options EXTRA_OUTPUT_OPTIONS`: Extra output options list.

    A list of extra ffmpeg command line arguments valid for the output.

    You can either use a JSON-formatted list (i.e., a list of comma-separated, quoted elements within square brackets), or a simple string of space-separated arguments.

    If JSON is used, you need to wrap the whole argument in quotes to prevent shell expansion and to preserve literal quotes inside the string. If a simple string is used, you need to specify the argument with `-e=`.

    Examples: `-e '[ "-vbr", "3" ]'` or `-e="-vbr 3"`

- `-ofmt OUTPUT_FORMAT, --output-format OUTPUT_FORMAT`: Media format to use for output file(s).

    See `ffmpeg -formats` for a list.

    If not specified, the format will be inferred by ffmpeg from the output file name. If the output file name is not explicitly specified, the extension will govern the format (see '--extension' option).

- `-ext EXTENSION, --extension EXTENSION`: Output file extension to use for output files that were not explicitly specified. (Default: `mkv`)

### Environment Variables

The program additionally respects environment variables:

- `TMP` / `TEMP` / `TMPDIR`

    Sets the path to the temporary directory in which files are
    stored before being moved to the final output directory.
    Note: You need to use full paths.

- `FFMPEG_PATH`

    Sets the full path to an `ffmpeg` executable other than
    the system default or you can provide a file name available on $PATH


## FAQ

### The program doesn't work because the "loudnorm" filter can't be found

Make sure you run ffmpeg v3.1 or higher and that `loudnorm` is part of the output when you run `ffmpeg -filters`. Many distributions package outdated ffmpeg 2.x versions, or (even worse), Libav's `ffmpeg` disguising as a real `ffmpeg` from the FFmpeg project.

Some ffmpeg builds also do not have the `loudnorm` filter enabled.

You can always download a static build from [their website](http://ffmpeg.org/download.html) and use that.

If you have to use an outdated ffmpeg version, you can only use `rms` or `peak` as normalization types, but I can't promise that the program will work correctly.

### Should I use this to normalize my music collection?

When you run `ffmpeg-normalize` and re-encode files with MP3 or AAC, you will inevitably introduce [generation loss](https://en.wikipedia.org/wiki/Generation_loss). Therefore, I do not recommend running this on your precious music collection, unless you have a backup of the originals or accept potential quality reduction. If you just want to normalize the subjective volume of the files without changing the actual content, consider using [MP3Gain](http://mp3gain.sourceforge.net/) and [aacgain](http://aacgain.altosdesign.com/).

### Why are my output files MKV?

I chose MKV as a default output container since it handles almost every possible combination of audio, video, and subtitle codecs. If you know which audio/video codec you want, and which container is supported, use the output options to specify the encoder and output file name manually.

### The conversion does not work and I get a cryptic ffmpeg error!

One possible reason is that the input file contains some streams that cannot be mapped to the output file. Examples:

- You are trying to normalize a movie file, writing to a `.wav` or `.mp3` file. WAV/MP3 files only support audio, not video. Disable video and subtitles with `-vn` and `-sn`, or choose a container that supports video (e.g. `.mkv`).

- You are trying to normalize a file, writing to an `.mp4` container. This program defaults to PCM audio, but MP4 does not support PCM audio. Make sure that your audio codec is set to something MP4 containers support (e.g. `-c:a aac).

The default output container is `.mkv` as it will support most input stream types. If you want a different output container, [make sure that it supports](https://en.wikipedia.org/wiki/Comparison_of_container_file_formats) your input file's video, audio, and subtitle streams (if any).

Also, if there is some other broken metadata, you can try to disable copying over of metadata with `-mn`.

### What are the different normalization algorithms?

- **EBU R128** is an EBU standard that is commonly used in the broadcasting world. The normalization is performed using a psychoacoustic model that targets a subjective loudness level measured in LUFS (Loudness Unit Full Scale). R128 is subjectively more accurate than any peak or RMS-based normalization. More info on R128 can be found in the [official document](https://tech.ebu.ch/docs/r/r128.pdf) and [the `loudnorm` filter description](http://k.ylo.ph/2016/04/04/loudnorm.html) by its original author.

- **Peak Normalization** analyzes the peak signal level in dBFS and increases the volume of the input signal such that the maximum in the output is 0 dB (or any other chosen threshold). Since spikes in the signal can cause high volume peaks, peak normalization might still result in files that are subjectively quieter than other, non-peak-normalized files.

- **RMS-based Normalization** analyzes the [RMS power](https://en.wikipedia.org/wiki/Root_mean_square#Average_power) of the signal and changes the volume such that a new RMS target is reached. Otherwise it works similar to peak normalization.

### Couldn't I just run `loudnorm` with ffmpeg?

You absolutely can. However, you can get better accuracy and linear normalization with two passes of the filter. Since ffmpeg does not allow you to automatically run these two passes, you have to do it yourself and parse the output values from the first run. If this program is too over-engineered for you, you could also use an approach such as featured [in this Ruby script](https://gist.github.com/kylophone/84ba07f6205895e65c9634a956bf6d54) that performs the two `loudnorm` passes.

### After updating, this program does not work as expected anymore!

You are probably using a 0.x version of this program. There are significant changes to the command line arguments and inner workings of this program, so please  adapt your scripts to the new one. Those changes were necessary to address a few issues that kept piling up; leaving the program as-is would have made it hard to extend it. You can continue using the old version (find it under *Releases* on GitHub or request the specific version from PyPi), but it will not be supported anymore.

### Can I buy you a beer / coffee / random drink?

If you found this program useful and feel like giving back, feel free to send a donation [via PayPal](https://paypal.me/WernerRobitza).

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
