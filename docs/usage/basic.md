# Basic Usage

Supply one or more input files, and optionally, output file names:

```bash
ffmpeg-normalize input [input ...][-h][-o OUTPUT [OUTPUT ...]] [options]
```

Example:

```bash
ffmpeg-normalize 1.wav 2.wav -o 1-normalized.m4a 2-normalized.m4a -c:a aac -b:a 192k
```

For more information on the options (`[options]`) available, run `ffmpeg-normalize -h`, or read the [Options](options.md) page.

