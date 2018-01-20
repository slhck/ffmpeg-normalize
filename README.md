# ffmpeg-normalize

A utility for batch-normalizing audio using ffmpeg.

This program normalizes media files to a certain LUFS level using the EBU R128 loudness normalization procedure. It can also perform RMS-based normalization (where the mean is lifted or attenuated), or peak normalization to a certain target level.

Batch processing of several input files is possible, including video files.

# Requirements

-   Python 2.7 or 3
-   ffmpeg v3.1 or above from <http://ffmpeg.org/> installed in your \$PATH

# Installation

    pip3 install ffmpeg-normalize

# Usage

    ffmpeg-normalize [-h] [-o OUTPUT [OUTPUT ...]] [-of OUTPUT_FOLDER] [-f]
                    [-d] [-v] [-n] [-nt {ebu,rms,peak}] [-t TARGET_LEVEL]
                    [-lrt LOUDNESS_RANGE_TARGET] [-tp TRUE_PEAK]
                    [--offset OFFSET] [--dual-mono] [-c:a AUDIO_CODEC]
                    [-b:a AUDIO_BITRATE] [-ar SAMPLE_RATE] [-vn]
                    [-c:v VIDEO_CODEC] [-sn] [-mn]
                    [-e EXTRA_OUTPUT_OPTIONS] [-ofmt OUTPUT_FORMAT]
                    [-ext EXTENSION]
                    input [input ...]

The program takes a number of input files and, by default, writes them to a folder called `normalized`, using an `.mkv` container. You can specify an output file name for each input file with the `-o` option. In this case, the container format will be inferred from the file name extension.

By default, all streams from the input file will be written to the output file. For example, if your input is a video with two language tracks and a subtitle track, both audio tracks will be normalized independently. The video and subtitle tracks will be copied over to the output file.

**Important Note:** The default audio encoding method is uncompressed PCM to avoid introducing compression artifacts. This will result in a much higher bitrate than you might want, for example if your input files are MP3s. Some containers (like MP4) also cannot handle PCM audio. If you want to use such containers and/or keep the file size down, use `-c:a` and specify an audio codec (e.g., `-c:a aac` for ffmpeg's built-in AAC encoder).

# Examples

Normalize a bunch of WAV files and write them to the specified output files with uncompressed PCM WAV as audio codec:

    ffmpeg-normalize file1.wav file2.wav -o file1-normalized.wav -o file2-normalized.wav

Normalize a number of videos in the current folder and write them to a folder called `normalized`, converting all audio streams to AAC with 192 kBit/s.

    ffmpeg-normalize *.mkv -c:a aac -b:a 192k

Instead of EBU R128, one might just want to use simple peak normalization to 0 dB:

    ffmpeg-normalize test.wav --normalization-type peak --target-level 0 -o normalized.wav

You can (if you really want) also overwrite your input file:

    ffmpeg-normalize input.mp4 -o input.mp4 -f

If you need some fancy extra options, such as `vbr` for the `libfdk_aac` encoder:

    ffmpeg-normalize input.m4a -c:a libfdk_aac -e '["vbr": "3"]' -o output.m4a

Further examples? Please submit a PR so I can collect them.

# FAQ

### This program does not work like expected anymore!

You are probably using a 0.x version of this program. There are significant changes to the command line arguments and inner workings of this program, so please either continue using the old version (find it under *Releases* on GitHub or request the specific version from PyPi) or adapt your scripts to the new one.

### The program doesn't work because the "loudnorm" filter can't be found

Make sure you run ffmpeg v3.1 or higher. Many distributions package outdated ffmpeg 2.x versions. You can always download a static build from [their website](http://ffmpeg.org/download.html) and use that.

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

### Can I buy you a beer / coffee / random drink?

If you found this script useful and feel like giving back, feel free to send a donation [via PayPal](https://paypal.me/slhck).

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
