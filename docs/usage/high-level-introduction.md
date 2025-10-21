# High-Level Introduction

## What does the program do?

The program takes one or more input files and, by default, writes them to a folder called `normalized`, using an `.mkv` container. The reason for choosing the MKV container is that it can handle almost any codec combination without any additional configuration.

All audio streams will be normalized so that they have the same (perceived) volume according to the [EBU R128](https://tech.ebu.ch/docs/r/r128.pdf) standard. This is done by analyzing the audio streams and applying a filter to bring them to a target level. This ensures that multiple files normalized with this filter will have the same perceived loudness.

Under the hood, the `ffmpeg-normalize` program uses [ffmpeg's `loudnorm` filter](https://ffmpeg.org/ffmpeg-filters.html#loudnorm) to do this; the filter was [originally written by Kyle Swanson](https://k.ylo.ph/2016/04/04/loudnorm.html).

## How do I specify the input?

Just give the program one or more input files as arguments. It works with most media files, including video files:

```bash
ffmpeg-normalize input1.mp3
```

This will create a file called `normalized/input1.mkv` in the current directory.

## What codec is chosen?

The default audio encoding method is uncompressed PCM (`pcm_s16le`) to avoid introducing compression artifacts.

!!! note

    This default keeps the quality high, but will result in a much higher bitrate than you might want, for example if your input files are MP3s, and now your output is much larger.

If you want to keep the file size down, use `-c:a` and specify an audio codec (e.g., `-c:a aac` for ffmpeg's built-in AAC encoder):

```bash
ffmpeg-normalize input1.mp3 -c:a aac
```

This will create a file called `normalized/input1.mkv` in the current directory, now using the AAC codec.

## How do I specify the output file name or extension?

You don't have to specify an output file name (the default is `normalized/<input>.mkv`), but if you want to override it, you can specify one output file name for each input file with the `-o` option. In this case, the container format (e.g. `.wav`) will be inferred from the file name extension that you've given.

Example:

```bash
ffmpeg-normalize 1.wav 2.wav -o 1-normalized.wav 2-normalized.wav
```

Using the `-ext` option, you can supply a different output extension common to all output files, e.g. `-ext m4a`. Example:

```bash
ffmpeg-normalize input.mp3 -c:a aac -ext m4a
```

This will create a file called `normalized/input.m4a`.

!!! warning

    You need to make sure that the container supports the codecs used for the output. For example, you cannot place AAC audio in a WAV container.

## What will get normalized?

By default, all streams from the input file will be written to the output file. For example, if your input is a video with two language tracks and a subtitle track, both audio tracks will be normalized independently. Any video and subtitle tracks will be copied over to the output file.

You additionally have several options for controlling which audio streams get normalized. By default, all audio streams are normalized:

```bash
ffmpeg-normalize input.mkv
```

Use `-as/--audio-streams` to select specific streams by their index (comma-separated):

```bash
# Normalize only stream 1
ffmpeg-normalize input.mkv -as 1

# Normalize streams 1 and 2
ffmpeg-normalize input.mkv -as 1,2
```

!!! tip

    You can use `ffmpeg -i input.mkv` to see all streams and their indices before normalizing.

Use `--audio-default-only` to normalize only streams marked with the "default" disposition (useful for files with multiple language tracks where you only want to normalize the main track):

```bash
ffmpeg-normalize input.mkv --audio-default-only
```

By default, if you select specific streams, only those streams will be in the output. Use `--keep-other-audio` to copy all other audio streams unchanged:

```bash
# Normalize stream 1, keep all other audio streams as-is
ffmpeg-normalize input.mkv -as 1 --keep-other-audio
```
