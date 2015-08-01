ffmpeg-normalize
================

Audio Normalization Script for Python/ffmpeg.
The script RMS-normalizes media files (video, audio) to -26 dB RMS. It outputs PCM WAV files named as `normalized-<input>.wav`. It can also do peak normalization.

Requirements
============

* Python 2.7 or 3
* Recent version of ffmpeg (use your distribution's package manager or download a static build from http://ffmpeg.org/download.html if you don't want to compile) in your `$PATH`

Usage
=====

Very simple, just install with pip and run it::

    pip install ffmpeg-normalize
    ffmpeg-normalize -i <input-file> -v


Or run it directly from source::

    python -m ffmpeg_normalize -i <input-file> -v


Options
=======

Type ``ffmpeg-normalize -h`` for usage::

  -f, --force                Force overwriting existing files
  -l  LEVEL, --level LEVEL   level to normalize to (default: -26 dB)
  -p PREFIX, --prefix PREFIX Normalized file prefix (default: "normalized")
  -m, --max                  Normalize to the maximum (peak) volume instead of RMS
  -v, --verbose              Enable verbose output
  -n, --dry-run              Show what would be done, do not convert
