#!/usr/bin/env python3
#
# Simple test suite

import os
import sys
import unittest
import subprocess

try:
  from pathlib import Path
except ImportError:
  from pathlib2 import Path  # python2 backport

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

from ffmpeg_normalize import FFmpegNormalize
from ffmpeg_normalize import MediaFile
from ffmpeg_normalize._cmd_utils import run_command

def ffmpeg_normalize_call(args, env=None):
    cmd = [sys.executable, '-m', 'ffmpeg_normalize']
    cmd.extend(args)
    print()
    print(" ".join(cmd))
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env=env
    )
    stdout, stderr = p.communicate()

    return (stdout + stderr), p.returncode


class TestFFmpegNormalize(unittest.TestCase):
    def test_output_filename_and_folder(self):
        ffmpeg_normalize_call(['test/test.mp4'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'))

    def test_no_overwrite(self):
        ffmpeg_normalize_call(['test/test.mp4', '-v'])
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-v'])
        self.assertTrue("exists" in output)

    def test_dry(self):
        ffmpeg_normalize_call(['test/test.mp4', '-n'])
        self.assertFalse(os.path.isfile('normalized/test.mkv'))

    def test_output(self):
        Path('normalized').mkdir(exist_ok=True)
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-o', 'normalized/test.wav', '-v'])
        self.assertTrue("Output file only supports one stream." in output)

    def test_peak(self):
        ffmpeg_normalize_call(['test/test.mp4', '-nt', 'peak', '-t', '0'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'))

    def test_rms(self):
        ffmpeg_normalize_call(['test/test.mp4', '-nt', 'rms', '-t', '-16'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'))

    def test_lrt(self):
        ffmpeg_normalize_call(['test/test.mp4', '-lrt', '1'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'))

    def test_tp(self):
        ffmpeg_normalize_call(['test/test.mp4', '-tp', '-3'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'))

    def test_offset(self):
        ffmpeg_normalize_call(['test/test.mp4', '--offset', '10'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'))

    def test_acodec(self):
        ffmpeg_normalize_call(['test/test.mp4', '-c:a', 'aac'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'))

    def test_abr(self):
        Path('normalized').mkdir(exist_ok=True)
        ffmpeg_normalize_call(['test/test.mp4', '-c:a', 'aac', '-b:a', '192k', '-o', 'normalized/test.aac'])
        self.assertTrue(os.path.isfile('normalized/test.aac'))

    def test_ar(self):
        ffmpeg_normalize_call(['test/test.mp4', '-ar', '48000'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'))

    def test_vcodec(self):
        ffmpeg_normalize_call(['test/test.mp4', '-c:v', 'libx264'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'))

    def test_extra_options(self):
        ffmpeg_normalize_call(['test/test.mp4', '-c:a', 'aac', '-e', '[ "-vbr", "3" ]'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'))

    def test_ofmt(self):
        Path('normalized').mkdir(exist_ok=True)
        ffmpeg_normalize_call(['test/test.mp4', '-ofmt', 'mp3', '-o', 'normalized/test.mp3', '-vn', '-sn'])
        self.assertTrue(os.path.isfile('normalized/test.mp3'))

    def test_ext(self):
        ffmpeg_normalize_call(['test/test.mp4', '-ext', 'mp3'])
        self.assertTrue(os.path.isfile('normalized/test.mp3'))

    def test_version(self):
        output, _ = ffmpeg_normalize_call(['--version'])
        self.assertTrue("ffmpeg-normalize v" in output)

    def test_stats(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '--print-stats'])
        self.assertTrue('"ebu": {' in output)

    def tearDown(self):
        for file in ['test.mkv', 'test.wav', 'test.mp3', 'test.aac']:
            if os.path.isfile('normalized/' + file):
                os.remove('normalized/' + file)
        if os.path.isdir('normalized'):
            os.rmdir('normalized')


if __name__ == '__main__':
    unittest.main()
