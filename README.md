audio-normalize
===============

Audio Normalization Script for Python/ffmpeg. I've only tested it with Python 2.6, not Python 3.

The script normalizes media files to -26 dB RMS. It outputs PCM WAV files named as `normalized-<input>.wav`.

Usage
=====

Very simple:

    ./normalize.py -i <input-file> -v

The `-v` option turns on info messages. Check out `./normalize.py -h` for more options.


What's with the MATLAB Code?
============================

This is the reference I've used for testing whether the Python script does the same thing. You can of course use it too, if you want.
