ffmpeg-normalize
================

ffmpeg script for normalizing audio.

This program normalizes media files to a certain dB level. The default is an
RMS-based normalization where the mean is lifted. Peak normalization is
possible with the ``-m`` option.

It takes any audio or video file as input, and writes the audio part as
output WAV file. The normalized audio can also be merged with the
original.

Requirements:

- Python 2.7 (Python 3 is not supported yet)
- ffmpeg from http://ffmpeg.org/ installed in your $PATH

Installation::

    pip install ffmpeg-normalize

Usage::

    ffmpeg-normalize [options] <input-file>...

Options:

-  ``-f``, ``--force`` — Force overwriting existing files
-  ``-l``, ``--level <level>`` — dB level to normalize to [default: -26]
-  ``-p``, ``--prefix <prefix>`` — Normalized file prefix [default:
   normalized]
-  ``-t``, ``--threshold <threshold>`` — dB threshold below which the
   audio will be not adjusted [default: 0.5]
-  ``-o``, ``--dir`` — Create an output folder in stead of prefixing the
   file
-  ``-m``, ``--max`` — Normalize to the maximum (peak) volume instead of
   RMS
-  ``-v``, ``--verbose`` — Enable verbose output
-  ``-n``, ``--dry-run`` — Show what would be done, do not convert
-  ``-d``, ``--debug`` — Show debug output
-  ``-u``, ``--merge`` — Don’t create a separate WAV file but update the
   original file. Use in combination with -p to create a copy
-  ``-a``, ``--acodec <acodec>`` — Set audio codec for ffmpeg (see
   “ffmpeg -encoders”) when merging. If not set, default from ffmpeg
   will be used.
-  ``-e``, ``--extra-options <extra-options>`` — Set extra options
   passed to ffmpeg (e.g. “-b:a 192k” to set audio bitrate)

Examples::

    ffmpeg-normalize -v file.mp3
    ffmpeg-normalize -v *.avi
    ffmpeg-normalize -u -v -o -f -m -l -5 *.mp4
    ffmpeg-normalize -u -v -a libfdk_aac -e "-b:a 192k" *.mkv
