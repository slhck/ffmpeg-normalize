"""Regression tests for preset precedence and safe album processing."""

import array
import math
import os
from pathlib import Path
import subprocess
import sys
import wave

import pytest

from ffmpeg_normalize import FFmpegNormalize
from ffmpeg_normalize._errors import FFmpegNormalizeError


def write_tone(path: Path, peak_db: float) -> None:
    """Write a one-second mono tone with a known sample peak."""
    amplitude = 32767 * 10 ** (peak_db / 20)
    samples = array.array(
        "h", (round(amplitude * math.sin(2 * math.pi * i / 48)) for i in range(48000))
    )
    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(str(path), "wb") as output:
        output.setparams((1, 2, 48000, 0, "NONE", "not compressed"))
        output.writeframes(samples.tobytes())


def peak_db(path: Path) -> float:
    """Measure the actual sample peak in an encoded PCM output."""
    with wave.open(str(path), "rb") as source:
        samples = array.array("h", source.readframes(source.getnframes()))
    if sys.byteorder != "little":
        samples.byteswap()
    return 20 * math.log10(max(abs(sample) for sample in samples) / 32768)


@pytest.mark.parametrize(
    "mode,target,lower_only,expected_gain",
    [
        ("peak", -1, False, 0),
        ("peak", -6, False, -5),
        ("peak", -1, True, 0),
        ("peak", -6, True, -5),
        ("rms", -1, False, 1),
        ("rms", -20, False, -10.99),
        ("rms", -20, True, -10.99),
        ("rms", -1, True, 0),
    ],
)
def test_album_gain_preserves_levels_without_clipping(
    tmp_path, mode, target, lower_only, expected_gain
):
    normalizer = FFmpegNormalize(
        normalization_type=mode,
        target_level=target,
        batch=True,
        lower_only=lower_only,
        audio_codec="pcm_s16le",
    )
    inputs, outputs = [], []
    for index, peak in enumerate([-1, -11]):
        source = tmp_path / f"input{index}.wav"
        destination = tmp_path / f"output{index}.wav"
        write_tone(source, peak)
        normalizer.add_media_file(str(source), str(destination))
        inputs.append(source)
        outputs.append(destination)
    normalizer.run_normalization()
    assert all(file.status == "normalized" for file in normalizer.media_files)
    gains = [
        peak_db(output) - peak_db(source) for source, output in zip(inputs, outputs)
    ]
    assert gains == pytest.approx([expected_gain] * 2, abs=0.03)
    assert max(peak_db(output) for output in outputs) <= 0
    if mode == "peak":
        assert max(peak_db(output) for output in outputs) == pytest.approx(
            target, abs=0.03
        )


@pytest.mark.parametrize("arguments", [["-t", "-23"], ["--target-level=-23"]])
def test_explicit_default_target_overrides_preset(tmp_path, arguments):
    source = tmp_path / "input.wav"
    write_tone(source, -10)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ffmpeg_normalize",
            str(source),
            "--preset",
            "podcast",
            *arguments,
            "--dry-run",
            "--debug",
            "-o",
            str(tmp_path / "output.wav"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "i=-23.0" in result.stderr
    assert "Applied preset option 'target-level'" not in result.stderr


@pytest.mark.parametrize("force", [False, True])
def test_cli_rejects_duplicate_basenames_before_writing(tmp_path, force):
    inputs = []
    for directory in ["disc1", "disc2"]:
        folder = tmp_path / directory
        folder.mkdir()
        source = folder / "track.wav"
        write_tone(source, -10)
        inputs.append(str(source))
    output = tmp_path / "normalized"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ffmpeg_normalize",
            *inputs,
            "-of",
            str(output),
            *(["--force"] if force else []),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "Output collision" in result.stderr
    assert not output.exists()


def test_output_cannot_overwrite_another_input(tmp_path):
    first, second = tmp_path / "first.wav", tmp_path / "second.wav"
    for path in [first, second]:
        write_tone(path, -10)
    original = second.read_bytes()
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ffmpeg_normalize",
            str(first),
            str(second),
            "-o",
            str(second),
            str(tmp_path / "third.wav"),
            "--force",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "would overwrite another input" in result.stderr
    assert second.read_bytes() == original


@pytest.mark.parametrize("link_type", ["symlink", "hardlink", "relative"])
def test_output_aliases_are_rejected(tmp_path, link_type):
    destination = tmp_path / "output.wav"
    destination.touch()
    alias = tmp_path / "alias.wav"
    if link_type == "symlink":
        alias.symlink_to(destination)
    elif link_type == "hardlink":
        os.link(destination, alias)
    else:
        alias = tmp_path / "subdirectory" / ".." / "output.wav"
    with pytest.raises(FFmpegNormalizeError, match="Output collision"):
        FFmpegNormalize.validate_output_files(
            [str(tmp_path / "a.wav"), str(tmp_path / "b.wav")],
            [str(destination), str(alias)],
        )


def test_in_place_and_null_outputs_are_allowed(tmp_path):
    source = str(tmp_path / "source.wav")
    FFmpegNormalize.validate_output_files([source], [source])
    FFmpegNormalize.validate_output_files(["a.wav", "b.wav"], [os.devnull, os.devnull])


def test_api_rejects_collisions_before_processing(tmp_path):
    source = tmp_path / "source.wav"
    write_tone(source, -10)
    destination = tmp_path / "output.wav"
    normalizer = FFmpegNormalize()
    for _ in range(2):
        normalizer.add_media_file(str(source), str(destination))
    with pytest.raises(FFmpegNormalizeError, match="Output collision"):
        normalizer.run_normalization()
    assert not destination.exists()


def test_explicit_string_and_boolean_defaults_override_presets():
    from ffmpeg_normalize.__main__ import create_parser
    from ffmpeg_normalize._presets import PresetManager

    explicit = create_parser(suppress_defaults=True).parse_args(
        ["-nt", "ebu", "--no-keep-bit-depth", "--metadata-disable", "-of", "normalized"]
    )
    arguments = create_parser().parse_args([])
    vars(arguments).update(vars(explicit))
    PresetManager().merge_preset_with_args(
        {
            "normalization-type": "rms",
            "keep-bit-depth": True,
            "metadata-disable": False,
            "output-folder": "elsewhere",
        },
        arguments,
        set(vars(explicit)),
    )
    assert arguments.normalization_type == "ebu"
    assert arguments.keep_bit_depth is False
    assert arguments.metadata_disable is True
    assert arguments.output_folder == "normalized"
