# Basic Usage

Supply one or more input files, and optionally, output file names:

```bash
ffmpeg-normalize input [input ...][-h][-o OUTPUT [OUTPUT ...]] [options]
```

A very simple normalization command looks like this:

```bash
ffmpeg-normalize input.mp3
```

This creates `normalized/input.mkv` with EBU R128 normalization (target: -23 LUFS) using PCM audio.

You can customize the normalization and output format with various options, as described below.

```bash
ffmpeg-normalize input.mp3 -c:a aac -b:a 192k
```

This uses the AAC codec at 192 kbps bitrate instead of PCM to keep file size manageable.

To process multiple files, just list them all as input using wildcards (Linux):

```bash
ffmpeg-normalize *.mp3 -c:a libmp3lame -b:a 320k -ext mp3
```

This normalizes all MP3 files in the current directory, outputs as MP3 at 320 kbps.

For the complete list of options, run `ffmpeg-normalize -h` or read the [detailed options page](options.md).
You can also find more examples in the [examples page](examples.md).
