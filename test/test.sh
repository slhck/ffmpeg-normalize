#!/usr/bin/env bash
# Simple test suite
set -e
set -x

# Audio
python -m ffmpeg_normalize "test/test.wav"
python -m ffmpeg_normalize "test/test.wav" -f
python -m ffmpeg_normalize "test/test.wav" -f -m
python -m ffmpeg_normalize "test/test.wav" -f -b
python -m ffmpeg_normalize "test/test.wav" -f -b -m || true
python -m ffmpeg_normalize "test/test.wav" -f -t 80 -v 2>&1 | grep "will not"
python -m ffmpeg_normalize "test/test.wav" -f -a "pcm_s24le"
python -m ffmpeg_normalize "test/test.wav" -f -a "aac" -e "-b:a 192k -filter:a 'acompressor'"
[ -f "test/normalized-test.wav" ]

# General handling
python -m ffmpeg_normalize "test/test.wav" -f -o
[ -f "test/normalized/test.wav" ]
python -m ffmpeg_normalize "test/test.wav" -f -p "foo"
[ -f "test/foo-test.wav" ]
python -m ffmpeg_normalize "test/test.wav" -f -o -p "foo"
[ -f "test/foo/test.wav" ]
python -m ffmpeg_normalize "test/test.wav" -f -r "mkv"
[ -f "test/normalized-test.mkv" ]

# Overwriting
cp "test/test.wav" "test/test2.wav"
python -m ffmpeg_normalize "test/test.wav" -fx
mv "test/test2.wav" "test/test.wav"

# Video
python -m ffmpeg_normalize "test/test.mp4"
python -m ffmpeg_normalize "test/test.mp4" -f
python -m ffmpeg_normalize "test/test.mp4" -u
[ -f "test/normalized-test.mp4" ]

# Cleanup
rm -rvf "test/normalized"
rm -rvf "test/foo"
rm -fv "test/"normalized*
rm -fv "test/"foo*

echo "All checks passed!"