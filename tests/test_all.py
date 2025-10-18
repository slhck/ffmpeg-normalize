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
        _, stderr = ffmpeg_normalize_call(["tests/test.wav", "--debug"])
        assert "Found duration: " in stderr

    def test_pre_filters(self):
        ffmpeg_normalize_call(
            [
                "tests/test.wav",
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
                        "input_i": -23.01,
                        "input_tp": -10.75,
                        "input_lra": 2.20,
                        "input_thresh": -33.06,
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
                }
            ],
        )

    def test_post_filters(self):
        ffmpeg_normalize_call(
            [
                "tests/test.wav",
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
                        "input_i": -35.02,
                        "input_tp": -22.76,
                        "input_lra": 2.20,
                        "input_thresh": -45.07,
                        "output_i": -22.16,
                        "output_tp": -9.46,
                        "output_lra": 2.10,
                        "output_thresh": -32.24,
                        "normalization_type": "dynamic",
                        "target_offset": -0.84,
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
