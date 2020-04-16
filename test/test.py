#!/usr/bin/env python3
#
# Simple test suite

import os
import sys
import unittest
import subprocess
from pathlib import Path

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../'))

def ffmpeg_normalize_call(args, env=None, raw=False):
    if not raw:
        cmd = [sys.executable, '-m', 'ffmpeg_normalize']
        cmd.extend(args)
        print()
        print(" ".join(cmd))
    else:
        cmd = sys.executable + ' -m ffmpeg_normalize ' + args
        print(cmd)
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        env=env,
        shell=raw
    )
    stdout, stderr = p.communicate()

    return (stdout + stderr), p.returncode


class TestFFmpegNormalize(unittest.TestCase):
    def test_output_filename_and_folder(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'), msg=output)

    def test_multiple_output(self):
        os.makedirs("normalized", exist_ok=True)
        output, _ = ffmpeg_normalize_call(['test/test.mp4', 'test/test.mp4', '-o', 'normalized/test1.mkv', 'normalized/test2.mkv'])
        self.assertTrue(os.path.isfile('normalized/test1.mkv'), msg=output)
        self.assertTrue(os.path.isfile('normalized/test2.mkv'), msg=output)

    def test_no_overwrite(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-v'])
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-v'])
        self.assertTrue("exists" in output, msg=output)

    def test_dry(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-n'])
        self.assertFalse(os.path.isfile('normalized/test.mkv'), msg=output)

    def test_output(self):
        Path('normalized').mkdir(exist_ok=True)
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-o', 'normalized/test.wav', '-v'])
        self.assertTrue("Output file only supports one stream." in output, msg=output)

    def test_peak(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-nt', 'peak', '-t', '0'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'), msg=output)

    def test_rms(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-nt', 'rms', '-t', '-16'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'), msg=output)

    def test_lrt(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-lrt', '1'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'), msg=output)

    def test_tp(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-tp', '-3'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'), msg=output)

    def test_offset(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '--offset', '10'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'), msg=output)

    def test_acodec(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-c:a', 'aac'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'), msg=output)

    def test_abr(self):
        Path('normalized').mkdir(exist_ok=True)
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-c:a', 'aac', '-b:a', '192k', '-o', 'normalized/test.aac'])
        self.assertTrue(os.path.isfile('normalized/test.aac'), msg=output)

    def test_ar(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-ar', '48000'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'), msg=output)

    def test_vcodec(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-c:v', 'libx264'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'), msg=output)

    def test_extra_options_json(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-c:a', 'aac', '-e', '[ "-vbr", "3" ]'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'), msg=output)

    def test_extra_options_normal(self):
        output, _ = ffmpeg_normalize_call('test/test.mp4 -c:a aac -e="-vbr 3"', raw=True)
        self.assertTrue(os.path.isfile('normalized/test.mkv'), msg=output)

    def test_ofmt_fail(self):
        Path('normalized').mkdir(exist_ok=True)
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-ofmt', 'mp3', '-o', 'normalized/test.mp3', '-vn', '-sn'])
        self.assertTrue("does not support" in output, msg=output)

    def test_ofmt_mp3(self):
        Path('normalized').mkdir(exist_ok=True)
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-ofmt', 'mp3', '-o', 'normalized/test.mp3', '-c:a', 'libmp3lame', '-vn', '-sn'])
        self.assertTrue(os.path.isfile('normalized/test.mp3'), msg=output)

    def test_ext_fail(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-ext', 'mp3'])
        self.assertTrue("does not support" in output, msg=output)

    def test_ext_mp3(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-ext', 'mp3', '-c:a', 'libmp3lame'])
        self.assertTrue(os.path.isfile('normalized/test.mp3'), msg=output)

    def test_metadata_disable(self):
        Path('normalized').mkdir(exist_ok=True)
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-mn', '-c:a', 'aac', '-o', 'normalized/test.mp4'])
        self.assertTrue(os.path.isfile('normalized/test.mp4'), msg=output)

    def test_chapters_disable(self):
        Path('normalized').mkdir(exist_ok=True)
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-cn', '-c:a', 'aac', '-o', 'normalized/test.mp4'])
        self.assertTrue(os.path.isfile('normalized/test.mp4'), msg=output)

    def test_version(self):
        output, _ = ffmpeg_normalize_call(['--version'])
        self.assertTrue("ffmpeg-normalize v" in output, msg=output)

    def test_stats(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '--print-stats'])
        self.assertTrue('"ebu": {' in output, msg=output)

    def test_progress(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-pr'])
        self.assertTrue("100" in output, msg=output)
        self.assertTrue(os.path.isfile('normalized/test.mkv'), msg=output)

    def test_duration(self):
        output, _ = ffmpeg_normalize_call(['test/test.wav', '--debug'])
        self.assertTrue("Found duration: " in output, msg=output)

    def test_pre_filters(self):
        output, _ = ffmpeg_normalize_call(['test/test.wav', '-prf', 'volume=0,volume=0'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'), msg=output)

    def test_post_filters(self):
        output, _ = ffmpeg_normalize_call(['test/test.wav', '-pof', 'volume=0,volume=0'])
        self.assertTrue(os.path.isfile('normalized/test.mkv'), msg=output)

    def test_quiet(self):
        output, _ = ffmpeg_normalize_call(['test/test.mp4', '-ext', 'wav', '-vn', '-f', 'q'])
        self.assertTrue("only supports one stream" not in output, msg=output)

    def setUp(self):
        os.system("rm -rf normalized")

    def tearDown(self):
        for file in ['test.mkv', 'test.wav', 'test.mp3', 'test.aac', 'test.mp4', 'test1.mkv', 'test2.mkv']:
            if os.path.isfile('normalized/' + file):
                os.remove('normalized/' + file)
        if os.path.isdir('normalized'):
            os.rmdir('normalized')


if __name__ == '__main__':
    unittest.main()
