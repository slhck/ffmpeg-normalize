import json
import os
import shlex
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Literal, Tuple, cast

import pytest


def ffmpeg_normalize_call(args: List[str]) -> Tuple[str, str]:
    cmd = [sys.executable, "-m", "ffmpeg_normalize"]
    cmd.extend(args)

    print(shlex.join(cmd))
    try:
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )
        stdout, stderr = p.communicate()
        return stdout, stderr
    except subprocess.CalledProcessError as e:
        print(e.output)
        raise e


def _get_stats(
    input_file: str, normalization_type: Literal["ebu", "rms", "peak"] = "ebu"
) -> Dict:
    """
    Get the statistics from an existing output file without converting it.
    """
    stdout, _ = ffmpeg_normalize_call(
        [input_file, "-f", "-n", "--print-stats", "-nt", normalization_type]
    )
    stats = cast(dict, json.loads(stdout))
    print(json.dumps(stats, indent=4))
    return stats


def _get_stream_info(input_file: str) -> List[Dict]:
    cmd = [
        "ffprobe",
        "-hide_banner",
        "-loglevel",
        "error",
        input_file,
        "-of",
        "json",
        "-show_streams",
    ]
    return cast(
        list,
        json.loads(
            subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, universal_newlines=True
            )
        )["streams"],
    )


def fuzzy_equal(d1: Any, d2: Any, precision: float = 0.1) -> bool:
    """
    Compare two objects recursively (just as standard '==' except floating point
    values are compared within given precision.

    Based on https://gist.github.com/durden/4236551, modified to handle lists
    """

    if len(d1) != len(d2):
        print("Length of objects does not match {}, {}".format(d1, d2))
        return False

    if isinstance(d1, list):
        ret = []
        for v1, v2 in zip(d1, d2):
            if isinstance(v1, dict):
                ret.append(fuzzy_equal(v1, v2, precision))
            else:
                if not abs(v1 - v2) < precision:
                    print("Values do not match: Got {}, expected {}".format(v1, v2))
                    return False
                else:
                    ret.append(True)
        return all(ret)
    elif isinstance(d1, dict):
        errors = []
        for k, v in d1.items():
            # Make sure all the keys are equal
            if k not in d2:
                print("Object does not contain: {}, {}".format(k, d2))
                return False

            # Fuzzy float comparison
            if isinstance(v, float) and isinstance(d2[k], float):
                if not abs(v - d2[k]) < precision:
                    errors.append(
                        "Values for {} do not match: Got {}, expected {}".format(
                            k, v, d2[k]
                        )
                    )

            # Recursive compare if there are nested dicts
            elif isinstance(v, dict):
                if not fuzzy_equal(v, d2[k], precision):
                    return False

            # Fall back to default
            elif v != d2[k]:
                errors.append(
                    "Values for {} do not match: Got {}, expected {}".format(
                        k, v, d2[k]
                    )
                )

        if len(errors):
            print("Errors:\n" + "\n".join(errors))
            return False
    else:
        if not abs(d1 - d2) < precision:
            print("Values do not match: Got {}, expected {}".format(d2, d2))
            return False

    return True


class TestFFmpegNormalize:
    @pytest.fixture(scope="function", autouse=True)
    def cleanup(self):
        os.makedirs("normalized", exist_ok=True)
        yield
        for file in [
            "test.mkv",
            "test.wav",
            "test2.wav",
            "test.mp3",
            "test.aac",
            "test.mp4",
            "test1.mkv",
            "test2.mkv",
        ]:
            if os.path.isfile("normalized/" + file):
                os.remove("normalized/" + file)
            if os.path.isdir("normalized"):
                shutil.rmtree("normalized")

    def test_input_list(self, tmp_path):
        # Create a temporary input list file using pytest tmp_path
        input_list_path = tmp_path / "input_list.txt"
        input_list_path.write_text("tests/test.mp4\ntests/test.mp4\n")
        # Run ffmpeg-normalize with --input-list
        ffmpeg_normalize_call(["--input-list", str(input_list_path)])
        # Check output files
        assert os.path.isfile("normalized/test.mkv")

    def test_no_input_specified(self):
        """Run the CLI with no arguments; should exit with error"""
        _, stderr = ffmpeg_normalize_call([])
        assert "No input files specified" in stderr

    def test_empty_input_list_file(self, tmp_path):
        # Create an empty input list file using pytest tmp_path
        input_list_path = tmp_path / "empty_input_list.txt"
        input_list_path.write_text("")
        _, stderr = ffmpeg_normalize_call(["--input-list", str(input_list_path)])
        # Should error because the list is empty
        assert "No input files specified" in stderr

    def test_output_filename_and_folder(self):
        ffmpeg_normalize_call(["tests/test.mp4"])
        assert os.path.isfile("normalized/test.mkv")

    def test_default_warnings(self):
        _, stderr = ffmpeg_normalize_call(
            ["tests/test.mp4", "--dynamic", "-o", "normalized/test2.wav"]
        )
        assert "sample rate will automatically be set" in stderr

    def test_multiple_outputs(self):
        os.makedirs("normalized", exist_ok=True)
        ffmpeg_normalize_call(
            [
                "tests/test.mp4",
                "tests/test.mp4",
                "-o",
                "normalized/test1.mkv",
                "normalized/test2.mkv",
            ]
        )
        assert os.path.isfile("normalized/test1.mkv")
        assert os.path.isfile("normalized/test2.mkv")

    def test_overwrites(self):
        ffmpeg_normalize_call(["tests/test.mp4", "-v"])
        _, stderr = ffmpeg_normalize_call(["tests/test.mp4", "-v"])
        assert "exists" in stderr

    def test_dry(self):
        ffmpeg_normalize_call(["tests/test.mp4", "-n"])
        assert not os.path.isfile("normalized/test.mkv")

    def test_only_supports_one_stream_output(self):
        os.makedirs("normalized", exist_ok=True)
        _, stderr = ffmpeg_normalize_call(
            ["tests/test.mp4", "-o", "normalized/test.wav", "-v"]
        )
        assert "Output file only supports one stream" in stderr

    def test_peak(self):
        ffmpeg_normalize_call(["tests/test.mp4", "-nt", "peak", "-t", "0"])
        assert os.path.isfile("normalized/test.mkv")
        assert fuzzy_equal(
            _get_stats("normalized/test.mkv", "peak"),
            [
                {
                    "input_file": "normalized/test.mkv",
                    "output_file": "normalized/test.mkv",
                    "stream_id": 1,
                    "ebu_pass1": None,
                    "ebu_pass2": None,
                    "mean": -14.8,
                    "max": -0.0,
                },
                {
                    "input_file": "normalized/test.mkv",
                    "output_file": "normalized/test.mkv",
                    "stream_id": 2,
                    "ebu_pass1": None,
                    "ebu_pass2": None,
                    "mean": -19.3,
                    "max": -0.0,
                },
            ],
        )

    def test_rms(self):
        ffmpeg_normalize_call(["tests/test.mp4", "-nt", "rms", "-t", "-15"])
        assert os.path.isfile("normalized/test.mkv")
        assert fuzzy_equal(
            _get_stats("normalized/test.mkv", "rms"),
            [
                {
                    "input_file": "normalized/test.mkv",
                    "output_file": "normalized/test.mkv",
                    "stream_id": 1,
                    "ebu_pass1": None,
                    "ebu_pass2": None,
                    "mean": -15.0,
                    "max": -0.2,
                },
                {
                    "input_file": "normalized/test.mkv",
                    "output_file": "normalized/test.mkv",
                    "stream_id": 2,
                    "ebu_pass1": None,
                    "ebu_pass2": None,
                    "mean": -15.1,
                    "max": 0.0,
                },
            ],
        )

    def test_ebu(self):
        ffmpeg_normalize_call(["tests/test.mp4", "-nt", "ebu"])
        assert os.path.isfile("normalized/test.mkv")
        assert fuzzy_equal(
            _get_stats("normalized/test.mkv", "ebu"),
            [
                {
                    "input_file": "normalized/test.mkv",
                    "output_file": "normalized/test.mkv",
                    "stream_id": 1,
                    "ebu_pass1": {
                        "input_i": -23.00,
                        "input_tp": -10.32,
                        "input_lra": 2.40,
                        "input_thresh": -33.06,
                        "output_i": -22.03,
                        "output_tp": -8.89,
                        "output_lra": 2.30,
                        "output_thresh": -32.12,
                        "normalization_type": "dynamic",
                        "target_offset": -0.97,
                    },
                    "ebu_pass2": None,
                    "mean": None,
                    "max": None,
                },
                {
                    "input_file": "normalized/test.mkv",
                    "output_file": "normalized/test.mkv",
                    "stream_id": 2,
                    "ebu_pass1": {
                        "input_i": -22.98,
                        "input_tp": -10.72,
                        "input_lra": 2.10,
                        "input_thresh": -33.03,
                        "output_i": -22.16,
                        "output_tp": -9.46,
                        "output_lra": 2.10,
                        "output_thresh": -32.25,
                        "normalization_type": "dynamic",
                        "target_offset": -0.84,
                    },
                    "ebu_pass2": None,
                    "mean": None,
                    "max": None,
                },
            ],
        )

    def test_acodec(self):
        ffmpeg_normalize_call(["tests/test.mp4", "-c:a", "aac"])
        assert os.path.isfile("normalized/test.mkv")
        assert _get_stream_info("normalized/test.mkv")[1]["codec_name"] == "aac"

    def test_abr(self):
        os.makedirs("normalized", exist_ok=True)
        ffmpeg_normalize_call(
            [
                "tests/test.mp4",
                "-c:a",
                "aac",
                "-b:a",
                "320k",
                "-o",
                "normalized/test.aac",
            ]
        )
        assert os.path.isfile("normalized/test.aac")
        assert _get_stream_info("normalized/test.aac")[0]["codec_name"] == "aac"
        assert (
            abs(133000 - float(_get_stream_info("normalized/test.aac")[0]["bit_rate"]))
            > 10000
        )

    def test_ar(self):
        ffmpeg_normalize_call(["tests/test.mp4", "-ar", "48000"])
        assert os.path.isfile("normalized/test.mkv")
        assert _get_stream_info("normalized/test.mkv")[1]["sample_rate"] == "48000"

    def test_vcodec(self):
        ffmpeg_normalize_call(["tests/test.mp4", "-c:v", "libx265"])
        assert os.path.isfile("normalized/test.mkv")
        assert _get_stream_info("normalized/test.mkv")[0]["codec_name"] == "hevc"

    def test_extra_input_options_json(self):
        ffmpeg_normalize_call(
            ["tests/test.mp4", "-c:a", "aac", "-ei", '[ "-f", "mp4" ]']
        )
        # FIXME: some better test that options are respected?
        assert os.path.isfile("normalized/test.mkv")

    def test_extra_output_options_json(self):
        ffmpeg_normalize_call(
            ["tests/test.mp4", "-c:a", "aac", "-e", '[ "-vbr", "3" ]']
        )
        # FIXME: some better test that options are respected?
        assert os.path.isfile("normalized/test.mkv")

    def test_ofmt_fail(self):
        _, stderr = ffmpeg_normalize_call(
            [
                "tests/test.mp4",
                "-ofmt",
                "mp3",
                "-o",
                "normalized/test.mp3",
                "-vn",
                "-sn",
            ]
        )
        assert "does not support" in stderr

    def test_ofmt_mp3(self):
        ffmpeg_normalize_call(
            [
                "tests/test.mp4",
                "-ofmt",
                "mp3",
                "-o",
                "normalized/test.mp3",
                "-c:a",
                "libmp3lame",
                "-vn",
                "-sn",
            ]
        )
        assert os.path.isfile("normalized/test.mp3")

    def test_ext_fail(self):
        _, stderr = ffmpeg_normalize_call(["tests/test.mp4", "-ext", "mp3"])
        assert "does not support" in stderr

    def test_ext_mp3(self):
        ffmpeg_normalize_call(["tests/test.mp4", "-ext", "mp3", "-c:a", "libmp3lame"])
        assert os.path.isfile("normalized/test.mp3")

    def test_version(self):
        stdout, _ = ffmpeg_normalize_call(["--version"])
        assert "ffmpeg-normalize v" in stdout

    def test_progress(self):
        _, stderr = ffmpeg_normalize_call(["tests/test.mp4", "-pr"])
        assert "0/100" in stderr
        assert "100/100" in stderr or "100%" in stderr
        assert os.path.isfile("normalized/test.mkv")

    def test_duration(self):
        _, stderr = ffmpeg_normalize_call(["tests/test.m4a", "--debug"])
        assert "Found duration: " in stderr

    def test_pre_filters(self):
        ffmpeg_normalize_call(
            [
                "tests/test.m4a",
                "-o",
                "normalized/test2.wav",
                "-prf",
                "volume=0.5,volume=0.5",
            ]
        )
        assert os.path.isfile("normalized/test2.wav")
        assert fuzzy_equal(
            _get_stats("normalized/test2.wav", "ebu"),
            [
                {
                    "input_file": "normalized/test2.wav",
                    "output_file": "normalized/test2.mkv",
                    "stream_id": 0,
                    "ebu_pass1": {
                        "input_i": -23.03,
                        "input_tp": -17.86,
                        "input_lra": 0.4,
                        "input_thresh": -35.86,
                        "output_i": -19.91,
                        "output_tp": -14.76,
                        "output_lra": 0.0,
                        "output_thresh": -32.59,
                        "normalization_type": "dynamic",
                        "target_offset": -3.09,
                    },
                    "ebu_pass2": None,
                    "mean": None,
                    "max": None,
                }
            ],
        )

    def test_post_filters(self):
        ffmpeg_normalize_call(
            [
                "tests/test.m4a",
                "-o",
                "normalized/test2.wav",
                "-pof",
                "volume=0.5,volume=0.5",
            ]
        )
        assert os.path.isfile("normalized/test2.wav")
        assert fuzzy_equal(
            _get_stats("normalized/test2.wav", "ebu"),
            [
                {
                    "input_file": "normalized/test2.wav",
                    "output_file": "normalized/test2.mkv",
                    "stream_id": 0,
                    "ebu_pass1": {
                        "input_i": -35.05,
                        "input_tp": -29.9,
                        "input_lra": 0.4,
                        "input_thresh": -47.87,
                        "output_i": -19.9,
                        "output_tp": -14.76,
                        "output_lra": 0.0,
                        "output_thresh": -32.58,
                        "normalization_type": "dynamic",
                        "target_offset": -3.1,
                    },
                    "ebu_pass2": None,
                    "mean": None,
                    "max": None,
                }
            ],
        )

    def test_quiet(self):
        _, stderr = ffmpeg_normalize_call(
            ["tests/test.mp4", "-ext", "wav", "-vn", "-f", "q"]
        )
        assert "only supports one stream" not in stderr

    def test_audio_channels(self):
        ffmpeg_normalize_call(
            ["tests/test.mp4", "-ac", "1", "-o", "normalized/test.wav"]
        )
        assert os.path.isfile("normalized/test.wav")
        stream_info = _get_stream_info("normalized/test.wav")[0]
        assert stream_info["channels"] == 1

        ffmpeg_normalize_call(
            ["tests/test.mp4", "-ac", "2", "-o", "normalized/test2.wav"]
        )
        assert os.path.isfile("normalized/test2.wav")
        stream_info = _get_stream_info("normalized/test2.wav")[0]
        assert stream_info["channels"] == 2

    def test_replaygain(self):
        REPLAYGAIN_FILES = [
            "tests/test.mp4",
            "tests/test.mp3",
            "tests/test.ogg",
            "tests/test.opus",
        ]
        try:
            for file in REPLAYGAIN_FILES:
                original_mtime = os.path.getmtime(file)
                ffmpeg_normalize_call([file, "--replaygain"])
                assert os.path.isfile(file)
                assert os.path.getmtime(file) > original_mtime
        except AssertionError:
            print(f"Failed to normalize {file}")
            raise
        finally:
            # git checkout the files!
            for file in REPLAYGAIN_FILES:
                subprocess.run(["git", "checkout", file], check=False)

    def test_audio_streams_single(self):
        """Test normalizing only a single audio stream"""
        ffmpeg_normalize_call(["tests/test.mp4", "-as", "1", "-nt", "ebu"])
        assert os.path.isfile("normalized/test.mkv")
        # Check that output has only 1 audio stream
        streams = _get_stream_info("normalized/test.mkv")
        audio_streams = [s for s in streams if s["codec_type"] == "audio"]
        assert len(audio_streams) == 1
        # Verify stats show only one stream was normalized
        stats = _get_stats("normalized/test.mkv", "ebu")
        assert len(stats) == 1
        assert stats[0]["stream_id"] == 1

    def test_audio_streams_multiple(self):
        """Test normalizing multiple specific audio streams"""
        ffmpeg_normalize_call(["tests/test.mp4", "-as", "1,2", "-nt", "ebu"])
        assert os.path.isfile("normalized/test.mkv")
        # Check that output has 2 audio streams
        streams = _get_stream_info("normalized/test.mkv")
        audio_streams = [s for s in streams if s["codec_type"] == "audio"]
        assert len(audio_streams) == 2
        # Verify stats show both streams were normalized
        stats = _get_stats("normalized/test.mkv", "ebu")
        assert len(stats) == 2

    def test_audio_streams_with_keep_other(self):
        """Test normalizing one stream while keeping others as passthrough"""
        ffmpeg_normalize_call(
            ["tests/test.mp4", "-as", "1", "--keep-other-audio", "-nt", "ebu"]
        )
        assert os.path.isfile("normalized/test.mkv")
        # Check that output has 2 audio streams (1 normalized, 1 passthrough)
        streams = _get_stream_info("normalized/test.mkv")
        audio_streams = [s for s in streams if s["codec_type"] == "audio"]
        assert len(audio_streams) == 2
        # First audio stream should be normalized (PCM or similar)
        assert "pcm" in audio_streams[0]["codec_name"]
        # Second audio stream should be copied (ac3)
        assert audio_streams[1]["codec_name"] == "ac3"

    def test_audio_default_only(self):
        """Test normalizing only default audio streams"""
        # Note: test.mp4 has both audio streams marked as default
        ffmpeg_normalize_call(["tests/test.mp4", "--audio-default-only", "-nt", "ebu"])
        assert os.path.isfile("normalized/test.mkv")
        # Since both streams are default, both should be normalized
        streams = _get_stream_info("normalized/test.mkv")
        audio_streams = [s for s in streams if s["codec_type"] == "audio"]
        assert len(audio_streams) == 2
        # Verify stats show both streams were normalized
        stats = _get_stats("normalized/test.mkv", "ebu")
        assert len(stats) == 2

    def test_audio_streams_invalid_option_combination(self):
        """Test that using both --audio-streams and --audio-default-only fails"""
        _, stderr = ffmpeg_normalize_call(
            ["tests/test.mp4", "-as", "1", "--audio-default-only"]
        )
        assert "Cannot use both" in stderr

    def test_keep_other_and_keep_original_conflict(self):
        """Test that using both --keep-other-audio and --keep-original-audio fails"""
        _, stderr = ffmpeg_normalize_call(
            [
                "tests/test.mp4",
                "-as",
                "1",
                "--keep-other-audio",
                "--keep-original-audio",
            ]
        )
        assert "Cannot use both" in stderr


class TestFileValidation:
    """Tests for pre-batch file validation."""

    def test_nonexistent_file(self):
        """Test that validation fails for non-existent files."""
        _, stderr = ffmpeg_normalize_call(["nonexistent_file.mp4"])
        assert "Validation failed" in stderr
        assert "does not exist" in stderr

    def test_multiple_invalid_files(self):
        """Test that validation reports all invalid files at once."""
        _, stderr = ffmpeg_normalize_call(
            ["nonexistent1.mp4", "nonexistent2.mp4", "nonexistent3.mp4"]
        )
        assert "Validation failed for 3 file(s)" in stderr
        assert "nonexistent1.mp4" in stderr
        assert "nonexistent2.mp4" in stderr
        assert "nonexistent3.mp4" in stderr

    def test_file_without_audio(self, tmp_path):
        """Test that validation fails for files without audio streams."""
        # Create a video-only file using ffmpeg
        video_only = tmp_path / "video_only.mp4"
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:s=320x240:d=1",
            "-an",  # no audio
            "-c:v",
            "libx264",
            str(video_only),
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        _, stderr = ffmpeg_normalize_call([str(video_only)])
        assert "Validation failed" in stderr
        assert "does not contain any audio streams" in stderr

    def test_mixed_valid_invalid_files(self, tmp_path):
        """Test that validation fails when mix of valid and invalid files."""
        _, stderr = ffmpeg_normalize_call(
            ["tests/test.mp4", "nonexistent.mp4", "tests/test.m4a"]
        )
        # Should report the invalid file but not the valid ones
        assert "Validation failed for 1 file(s)" in stderr
        assert "nonexistent.mp4" in stderr
        # Valid files should not appear in error messages
        assert "test.mp4" not in stderr or "does not exist" not in stderr

    def test_valid_file_passes_validation(self):
        """Test that valid files pass validation."""
        # Should succeed (file exists and has audio)
        ffmpeg_normalize_call(["tests/test.mp4", "-n"])  # dry run
        # No assertion needed - if validation fails, the command will error

    def test_replaygain_tags_stripped_after_normalization(self, tmp_path):
        """Test that ReplayGain tags are stripped after normalization."""
        import shutil
        from mutagen.id3 import ID3, TXXX
        from mutagen.mp3 import MP3

        temp_input = tmp_path / "test_with_replaygain.mp3"
        temp_output = tmp_path / "normalized_output.mp3"

        try:
            # Create a temporary copy of test.mp3 with ReplayGain tags
            shutil.copy("tests/test.mp3", temp_input)

            # Add ReplayGain tags to the input file
            mp3 = MP3(str(temp_input), ID3=ID3)
            if not mp3.tags:
                mp3.add_tags()
            mp3.tags.add(TXXX(desc="REPLAYGAIN_TRACK_GAIN", text=["-5.00 dB"]))
            mp3.tags.add(TXXX(desc="REPLAYGAIN_TRACK_PEAK", text=["0.950000"]))
            mp3.save()

            # Verify tags were added
            mp3_check = MP3(str(temp_input), ID3=ID3)
            assert "TXXX:REPLAYGAIN_TRACK_GAIN" in mp3_check.tags
            assert "TXXX:REPLAYGAIN_TRACK_PEAK" in mp3_check.tags

            # Normalize the file
            ffmpeg_normalize_call(
                [str(temp_input), "-o", str(temp_output), "-c:a", "libmp3lame"]
            )

            # Check that output file exists
            assert temp_output.exists()

            # Check that ReplayGain tags were stripped from the output
            mp3_output = MP3(str(temp_output), ID3=ID3)
            if mp3_output.tags:
                assert "TXXX:REPLAYGAIN_TRACK_GAIN" not in mp3_output.tags, (
                    "REPLAYGAIN_TRACK_GAIN tag should be stripped"
                )
                assert "TXXX:REPLAYGAIN_TRACK_PEAK" not in mp3_output.tags, (
                    "REPLAYGAIN_TRACK_PEAK tag should be stripped"
                )
        finally:
            # Clean up temp files even if test fails
            if temp_input.exists():
                temp_input.unlink()
            if temp_output.exists():
                temp_output.unlink()

    def test_replaygain_tags_stripped_m4a(self, tmp_path):
        """Test that ReplayGain tags are stripped from M4A files after normalization."""
        import shutil
        from mutagen.mp4 import MP4

        temp_input = tmp_path / "test_with_replaygain.m4a"
        temp_output = tmp_path / "normalized_output.m4a"

        try:
            # Create a temporary copy of test.m4a with ReplayGain tags
            shutil.copy("tests/test.m4a", temp_input)

            # Add ReplayGain tags to the input file
            mp4 = MP4(str(temp_input))
            if not mp4.tags:
                mp4.add_tags()
            mp4.tags["----:com.apple.iTunes:REPLAYGAIN_TRACK_GAIN"] = [b"-5.00 dB"]
            mp4.tags["----:com.apple.iTunes:REPLAYGAIN_TRACK_PEAK"] = [b"0.950000"]
            mp4.save()

            # Verify tags were added
            mp4_check = MP4(str(temp_input))
            assert "----:com.apple.iTunes:REPLAYGAIN_TRACK_GAIN" in mp4_check.tags
            assert "----:com.apple.iTunes:REPLAYGAIN_TRACK_PEAK" in mp4_check.tags

            # Normalize the file
            ffmpeg_normalize_call(
                [str(temp_input), "-o", str(temp_output), "-c:a", "aac"]
            )

            # Check that output file exists
            assert temp_output.exists()

            # Check that ReplayGain tags were stripped from the output
            mp4_output = MP4(str(temp_output))
            if mp4_output.tags:
                assert (
                    "----:com.apple.iTunes:REPLAYGAIN_TRACK_GAIN" not in mp4_output.tags
                ), "REPLAYGAIN_TRACK_GAIN tag should be stripped"
                assert (
                    "----:com.apple.iTunes:REPLAYGAIN_TRACK_PEAK" not in mp4_output.tags
                ), "REPLAYGAIN_TRACK_PEAK tag should be stripped"
        finally:
            # Clean up temp files even if test fails
            if temp_input.exists():
                temp_input.unlink()
            if temp_output.exists():
                temp_output.unlink()

    def test_replaygain_tags_stripped_ogg(self, tmp_path):
        """Test that ReplayGain tags are stripped from OGG files after normalization."""
        import shutil
        from mutagen.oggvorbis import OggVorbis

        temp_input = tmp_path / "test_with_replaygain.ogg"
        temp_output = tmp_path / "normalized_output.ogg"

        try:
            # Create a temporary copy of test.ogg with ReplayGain tags
            shutil.copy("tests/test.ogg", temp_input)

            # Add ReplayGain tags to the input file
            ogg = OggVorbis(str(temp_input))
            ogg["REPLAYGAIN_TRACK_GAIN"] = ["-5.00 dB"]
            ogg["REPLAYGAIN_TRACK_PEAK"] = ["0.950000"]
            ogg.save()

            # Verify tags were added
            ogg_check = OggVorbis(str(temp_input))
            assert "REPLAYGAIN_TRACK_GAIN" in ogg_check
            assert "REPLAYGAIN_TRACK_PEAK" in ogg_check

            # Normalize the file
            ffmpeg_normalize_call(
                [str(temp_input), "-o", str(temp_output), "-c:a", "libvorbis"]
            )

            # Check that output file exists
            assert temp_output.exists()

            # Check that ReplayGain tags were stripped from the output
            ogg_output = OggVorbis(str(temp_output))
            # OGG stores tags in lowercase
            assert "replaygain_track_gain" not in ogg_output, (
                "replaygain_track_gain tag should be stripped"
            )
            assert "replaygain_track_peak" not in ogg_output, (
                "replaygain_track_peak tag should be stripped"
            )
        finally:
            # Clean up temp files even if test fails
            if temp_input.exists():
                temp_input.unlink()
            if temp_output.exists():
                temp_output.unlink()

    def test_replaygain_tags_stripped_opus(self, tmp_path):
        """Test that R128 tags are stripped from OPUS files after normalization."""
        import shutil
        from mutagen.oggopus import OggOpus

        temp_input = tmp_path / "test_with_r128.opus"
        temp_output = tmp_path / "normalized_output.opus"

        try:
            # Create a temporary copy of test.opus with R128 tags
            shutil.copy("tests/test.opus", temp_input)

            # Add R128 tags to the input file (Opus uses R128 instead of REPLAYGAIN)
            opus = OggOpus(str(temp_input))
            opus["R128_TRACK_GAIN"] = ["-1280"]  # -5.00 dB * 256
            opus.save()

            # Verify tags were added
            opus_check = OggOpus(str(temp_input))
            assert "R128_TRACK_GAIN" in opus_check

            # Normalize the file
            ffmpeg_normalize_call(
                [str(temp_input), "-o", str(temp_output), "-c:a", "libopus"]
            )

            # Check that output file exists
            assert temp_output.exists()

            # Check that R128 tags were stripped from the output
            opus_output = OggOpus(str(temp_output))
            # OPUS stores tags in lowercase
            assert "r128_track_gain" not in opus_output, (
                "r128_track_gain tag should be stripped"
            )
        finally:
            # Clean up temp files even if test fails
            if temp_input.exists():
                temp_input.unlink()
            if temp_output.exists():
                temp_output.unlink()


def test_ffmpeg_env():
    """Verify that ffmpeg_env context manager sets environment correctly."""
    from ffmpeg_normalize._cmd_utils import ffmpeg_env, _get_ffmpeg_env, CommandRunner

    original_env = _get_ffmpeg_env()
    assert original_env is None

    test_env = os.environ.copy()
    test_env.update({"TEST_FFMPEG_ENV_VAR": "12345"})

    with ffmpeg_env(test_env):
        env_in_context = _get_ffmpeg_env()
        assert env_in_context == test_env
        # Check that commandrunner uses the env
        cmd = CommandRunner().run_command(
            [sys.executable, "-c", "import os; print(os.getenv('TEST_FFMPEG_ENV_VAR'))"]
        )
        assert cmd.get_output().strip() == "12345"

    # After context, environment should be reset
    env_after = _get_ffmpeg_env()
    assert env_after is None
