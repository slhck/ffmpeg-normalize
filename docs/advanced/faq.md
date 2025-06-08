# FAQ

## My output file is too large?

This is because the default output codec is PCM, which is uncompressed. If you want to reduce the file size, you can specify an audio codec with `-c:a` (e.g., `-c:a aac` for ffmpeg's built-in AAC encoder), and optionally a bitrate with `-b:a`.

For example:

```bash
ffmpeg-normalize input.wav -o output.m4a -c:a aac -b:a 192k
```

## What options should I choose for the EBU R128 filter? What is linear and dynamic mode?

EBU R128 is a method for normalizing audio loudness across different tracks or programs. It works by analyzing the audio content and adjusting it to meet specific loudness targets. The main components are:

* Integrated Loudness (I): The overall loudness of the entire audio.
* Loudness Range (LRA): The variation in loudness over time.
* True Peak (TP): The maximum level of the audio signal.

The normalization process involves measuring these values (input) and then applying gain adjustments to meet target levels (output), typically -23 LUFS for integrated loudness. You can also specify a target loudness range (LRA) and true peak level (TP).

**Linear mode** applies a constant gain adjustment across the entire audio file. This is generally preferred because:

* It preserves the original dynamic range of the audio.
* It maintains the relative loudness between different parts of the audio.
* It avoids potential artifacts or pumping effects that can occur with dynamic processing.

**Dynamic mode**, on the other hand, can change the volume dynamically throughout the file. While this can achieve more consistent loudness, it may alter the original artistic intent. There were some bugs in older versions of the `loudnorm` filter that could cause artifacts, but these have been fixed in recent versions of ffmpeg.

For most cases, linear mode is recommended. Dynamic mode should only be used when linear mode is not suitable or when a specific effect is desired. In some cases, `loudnorm` will still fall back to dynamic mode, and a warning will be printed to the console. Here's when this can happen:

* When the input loudness range (LRA) is larger than the target loudness range: If the input file has a loudness range that exceeds the specified loudness range target, the loudnorm filter will automatically switch to dynamic mode. This is because linear normalization alone cannot reduce the loudness range without dynamic processing (limiting). The `--keep-loudness-range-target` option can be used to keep the input loudness range target above the specified target.

* When the required gain adjustment to meet the integrated loudness target would result in the true peak exceeding the specified true peak limit. This is because linear processing alone cannot reduce peaks without affecting the entire signal. For example, if a file needs to be amplified by 6 dB to reach the target integrated loudness, but doing so would push the true peak above the specified limit, the filter might switch to dynamic mode to handle this situation. If your content allows for it, you can increase the true peak target to give more headroom for linear processing. If you're consistently running into true peak issues, you might also consider lowering your target integrated loudness level.

At this time, the `loudnorm` filter in ffmpeg does not provide a way to force linear mode when the input loudness range exceeds the target or when the true peak would be exceeded. There are some options to mitigate this:

- The `--keep-lra-above-loudness-range-target` option can be used to keep the input loudness range above the specified target, but it will not force linear mode in all cases.
- Similarly, the `--keep-loudness-range-target` option can be used to keep the input loudness range target.
- The `--lower-only` option can be used to skip the normalization pass completely if the measured loudness is lower than the target loudness.

If instead you want to use dynamic mode, you can use the `--dynamic` option; this will also speed up the normalization process because only one pass is needed.

## The program doesn't work because the "loudnorm" filter can't be found

Make sure you run a recent ffmpeg version and that `loudnorm` is part of the output when you run `ffmpeg -filters`. Many distributions package outdated ffmpeg versions, or (even worse), Libav's `ffmpeg` disguising as a real `ffmpeg` from the FFmpeg project.

Some ffmpeg builds also do not have the `loudnorm` filter enabled.

You can always download a static build from [their website](http://ffmpeg.org/download.html) and use that.

If you have to use an outdated ffmpeg version, you can only use `rms` or `peak` as normalization types, but I can't promise that the program will work correctly.

## Should I use this to normalize my music collection?

You can use the `--replaygain` option to write ReplayGain tags to the original file without normalizing. This makes most music players understand the loudness difference and adjust the volume accordingly.

If you decide to run `ffmpeg-normalize` with the default options, it will encode the audio with PCM audio (the default), and the resulting files will be very large. You can also choose to re-encode the files with MP3 or AAC, but you will inevitably introduce [generation loss](https://en.wikipedia.org/wiki/Generation_loss). Therefore, I do not recommend running this kind of destructive operation on your precious music collection, unless you have a backup of the originals or accept potential quality reduction.

## Why are my output files MKV?

I chose MKV as a default output container since it handles almost every possible combination of audio, video, and subtitle codecs. If you know which audio/video codec you want, and which container is supported, use the output options to specify the encoder and output file name manually.

## I get a "Could not write header for output file" error

See the [next section](#the-conversion-does-not-work-and-i-get-a-cryptic-ffmpeg-error).

## The conversion does not work and I get a cryptic ffmpeg error!

Maybe ffmpeg says something like:

> Could not write header for output file #0 (incorrect codec parameters ?): Invalid argument

Or the program says:

> … Please choose a suitable audio codec with the `-c:a` option.

One possible reason is that the input file contains some streams that cannot be mapped to the output file, or that you are using a codec that does not work for the output file. Examples:

- You are trying to normalize a movie file, writing to a `.wav` or `.mp3` file. WAV/MP3 files only support audio, not video. Disable video and subtitles with `-vn` and `-sn`, or choose a container that supports video (e.g. `.mkv`).

- You are trying to normalize a file, writing to an `.mp4` container. This program defaults to PCM audio, but MP4 does not support PCM audio. Make sure that your audio codec is set to something MP4 containers support (e.g. `-c:a aac`).

The default output container is `.mkv` as it will support most input stream types. If you want a different output container, [make sure that it supports](https://en.wikipedia.org/wiki/Comparison_of_container_file_formats) your input file's video, audio, and subtitle streams (if any).

Also, if there is some other broken metadata, you can try to disable copying over of metadata with `-mn`.

Finally, make sure you use a recent version of ffmpeg. The [static builds](https://ffmpeg.org/download.html) are usually the best option.

## What are the different normalization algorithms?

- **EBU R128** is an EBU standard that is commonly used in the broadcasting world. The normalization is performed using a psychoacoustic model that targets a subjective loudness level measured in LUFS (Loudness Unit Full Scale). R128 is subjectively more accurate than any peak or RMS-based normalization. More info on R128 can be found in the [official document](https://tech.ebu.ch/docs/r/r128.pdf) and [the `loudnorm` filter description](http://k.ylo.ph/2016/04/04/loudnorm.html) by its original author.

- **Peak Normalization** analyzes the peak signal level in dBFS and increases the volume of the input signal such that the maximum in the output is 0 dB (or any other chosen threshold). Since spikes in the signal can cause high volume peaks, peak normalization might still result in files that are subjectively quieter than other, non-peak-normalized files.

- **RMS-based Normalization** analyzes the [RMS power](https://en.wikipedia.org/wiki/Root_mean_square#Average_power) of the signal and changes the volume such that a new RMS target is reached. Otherwise it works similar to peak normalization.

## Couldn't I just run `loudnorm` with ffmpeg?

You absolutely can. However, you can get better accuracy and linear normalization with two passes of the filter. Since ffmpeg does not allow you to automatically run these two passes, you have to do it yourself and parse the output values from the first run.

If ffmpeg-normalize is too over-engineered for you, you could also use an approach such as featured [in this Ruby script](https://gist.github.com/kylophone/84ba07f6205895e65c9634a956bf6d54) that performs the two `loudnorm` passes.

If you want dynamic normalization (the loudnorm default), simply use ffmpeg with one pass, e.g.:

```bash
ffmpeg -i input.mp3 -af loudnorm -c:a aac -b:a 192k output.m4a
```

## What about speech?

You should check out the `speechnorm` filter that is part of ffmpeg. It is a designed to be used in one pass, so you don't need this script at all.

See [the documentation](https://ffmpeg.org/ffmpeg-all.html#speechnorm) for more information.

## After updating, this program does not work as expected anymore!

You are probably using a 0.x version of this program. There are significant changes to the command line arguments and inner workings of this program, so please  adapt your scripts to the new one. Those changes were necessary to address a few issues that kept piling up; leaving the program as-is would have made it hard to extend it. You can continue using the old version (find it under *Releases* on GitHub or request the specific version from PyPi), but it will not be supported anymore.

## Can I buy you a beer / coffee / random drink?

If you found this program useful and feel like giving back, feel free to send a donation [via PayPal](https://paypal.me/WernerRobitza).
