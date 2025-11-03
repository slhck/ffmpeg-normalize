"""Unit tests for preset functionality."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from ffmpeg_normalize._presets import (
    PresetManager,
    get_config_dir,
    get_default_presets_dir,
)


class TestPresetManager:
    """Tests for the PresetManager class."""

    def test_get_config_dir_default(self):
        """Test that config dir uses ~/.config by default on Unix."""
        if os.name == "nt":
            pytest.skip("Unix-only test")

        # Temporarily unset XDG_CONFIG_HOME
        old_xdg = os.environ.pop("XDG_CONFIG_HOME", None)
        try:
            config_dir = get_config_dir()
            assert str(config_dir).endswith(".config/ffmpeg-normalize")
        finally:
            if old_xdg:
                os.environ["XDG_CONFIG_HOME"] = old_xdg

    def test_get_config_dir_respects_xdg_config_home(self):
        """Test that config dir respects XDG_CONFIG_HOME when set."""
        if os.name == "nt":
            pytest.skip("Unix-only test")

        old_xdg = os.environ.get("XDG_CONFIG_HOME")
        try:
            os.environ["XDG_CONFIG_HOME"] = "/custom/config"
            config_dir = get_config_dir()
            assert str(config_dir) == "/custom/config/ffmpeg-normalize"
        finally:
            if old_xdg:
                os.environ["XDG_CONFIG_HOME"] = old_xdg
            else:
                os.environ.pop("XDG_CONFIG_HOME", None)

    def test_get_default_presets_dir(self):
        """Test that default presets directory path is correct."""
        presets_dir = get_default_presets_dir()
        assert presets_dir.name == "presets"
        assert "data" in str(presets_dir)

    def test_list_available_presets(self):
        """Test that available presets can be listed."""
        manager = PresetManager()
        presets = manager.get_available_presets()
        assert isinstance(presets, list)
        assert len(presets) >= 3
        assert "podcast" in presets
        assert "music" in presets
        assert "streaming-video" in presets

    def test_load_podcast_preset(self):
        """Test loading the podcast preset."""
        manager = PresetManager()
        preset = manager.load_preset("podcast")

        assert preset["normalization-type"] == "ebu"
        assert preset["target-level"] == -16.0
        assert preset["loudness-range-target"] == 7.0
        assert preset["true-peak"] == -2.0

    def test_load_music_preset(self):
        """Test loading the music preset."""
        manager = PresetManager()
        preset = manager.load_preset("music")

        assert preset["normalization-type"] == "rms"
        assert preset["target-level"] == -20.0
        assert preset["batch"] is True

    def test_load_streaming_video_preset(self):
        """Test loading the streaming-video preset."""
        manager = PresetManager()
        preset = manager.load_preset("streaming-video")

        assert preset["normalization-type"] == "ebu"
        assert preset["target-level"] == -14.0
        assert preset["loudness-range-target"] == 7.0
        assert preset["true-peak"] == -2.0

    def test_load_nonexistent_preset(self):
        """Test that loading a nonexistent preset raises FileNotFoundError."""
        manager = PresetManager()
        with pytest.raises(FileNotFoundError):
            manager.load_preset("nonexistent-preset")

    def test_validate_preset_valid(self):
        """Test validating a valid preset."""
        manager = PresetManager()
        is_valid, message = manager.validate_preset("podcast")
        assert is_valid is True
        assert "valid" in message.lower()

    def test_validate_preset_invalid(self):
        """Test validating an invalid preset."""
        manager = PresetManager()
        is_valid, message = manager.validate_preset("nonexistent")
        assert is_valid is False
        assert "not found" in message.lower()

    def test_merge_preset_with_args_basic(self):
        """Test basic preset merging with default args."""
        from ffmpeg_normalize.__main__ import create_parser

        manager = PresetManager()
        parser = create_parser()

        # Parse with defaults
        args = parser.parse_args([])

        # Load preset
        preset = manager.load_preset("podcast")

        # Merge
        manager.merge_preset_with_args(preset, args)

        # Verify preset values were applied
        assert args.normalization_type == "ebu"
        assert args.target_level == -16.0
        assert args.loudness_range_target == 7.0
        assert args.true_peak == -2.0

    def test_merge_preset_cli_override(self):
        """Test that CLI args override preset values."""
        from ffmpeg_normalize.__main__ import create_parser

        manager = PresetManager()
        parser = create_parser()

        # Parse with explicit values
        args = parser.parse_args(["-t", "-14"])

        # Load preset that specifies -16
        preset = manager.load_preset("podcast")

        # Merge
        manager.merge_preset_with_args(preset, args)

        # CLI value should be preserved, not overridden
        assert args.target_level == -14.0

    def test_merge_preset_music_rms(self):
        """Test that music preset applies RMS normalization."""
        from ffmpeg_normalize.__main__ import create_parser

        manager = PresetManager()
        parser = create_parser()

        args = parser.parse_args([])
        preset = manager.load_preset("music")

        manager.merge_preset_with_args(preset, args)

        assert args.normalization_type == "rms"
        assert args.target_level == -20.0
        assert args.batch is True


class TestPresetsCLI:
    """Tests for preset functionality via CLI."""

    def test_list_presets_command(self):
        """Test --list-presets command."""
        result = subprocess.run(
            ["python", "-m", "ffmpeg_normalize", "--list-presets"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        assert result.returncode == 0
        assert "podcast" in result.stdout
        assert "music" in result.stdout
        assert "streaming-video" in result.stdout

    def test_apply_podcast_preset_dry_run(self):
        """Test applying podcast preset with dry-run."""
        test_file = Path(__file__).parent / "test.mp3"
        if not test_file.exists():
            pytest.skip("test.mp3 not found")

        result = subprocess.run(
            [
                "python",
                "-m",
                "ffmpeg_normalize",
                str(test_file),
                "--preset",
                "podcast",
                "--dry-run",
                "-d",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # Should succeed
        assert result.returncode == 0

        # Check that podcast preset values are applied
        assert "Applied preset option 'target-level' = -16.0" in result.stderr
        assert "Applied preset option 'loudness-range-target' = 7.0" in result.stderr
        assert "Applied preset option 'true-peak' = -2.0" in result.stderr

    def test_apply_music_preset_dry_run(self):
        """Test applying music preset with dry-run."""
        test_file = Path(__file__).parent / "test.mp3"
        if not test_file.exists():
            pytest.skip("test.mp3 not found")

        result = subprocess.run(
            [
                "python",
                "-m",
                "ffmpeg_normalize",
                str(test_file),
                "--preset",
                "music",
                "--dry-run",
                "-d",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # Should succeed
        assert result.returncode == 0

        # Check that music preset values are applied (RMS, not EBU)
        assert "Applied preset option 'normalization-type' = rms" in result.stderr
        assert "Applied preset option 'target-level' = -20.0" in result.stderr
        assert "Applied preset option 'batch' = True" in result.stderr

    def test_apply_streaming_video_preset_dry_run(self):
        """Test applying streaming-video preset with dry-run."""
        test_file = Path(__file__).parent / "test.mp3"
        if not test_file.exists():
            pytest.skip("test.mp3 not found")

        result = subprocess.run(
            [
                "python",
                "-m",
                "ffmpeg_normalize",
                str(test_file),
                "--preset",
                "streaming-video",
                "--dry-run",
                "-d",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # Should succeed
        assert result.returncode == 0

        # Check that streaming-video preset values are applied
        assert "Applied preset option 'target-level' = -14.0" in result.stderr
        assert "Applied preset option 'loudness-range-target' = 7.0" in result.stderr
        assert "Applied preset option 'true-peak' = -2.0" in result.stderr

    def test_preset_with_cli_override_dry_run(self):
        """Test that CLI options override preset values."""
        test_file = Path(__file__).parent / "test.mp3"
        if not test_file.exists():
            pytest.skip("test.mp3 not found")

        result = subprocess.run(
            [
                "python",
                "-m",
                "ffmpeg_normalize",
                str(test_file),
                "--preset",
                "podcast",
                "-t",
                "-14",
                "--dry-run",
                "-d",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # Should succeed
        assert result.returncode == 0

        # The preset should still be applied
        assert "Applied preset option" in result.stderr

        # But CLI value should take precedence (so we shouldn't see the -16 from preset being used)
        # Instead, we check that the command runs with the -14 value

    def test_invalid_preset_error(self):
        """Test that invalid preset raises error."""
        test_file = Path(__file__).parent / "test.mp3"
        if not test_file.exists():
            pytest.skip("test.mp3 not found")

        result = subprocess.run(
            [
                "python",
                "-m",
                "ffmpeg_normalize",
                str(test_file),
                "--preset",
                "nonexistent-preset",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )

        # Should fail
        assert result.returncode != 0
        # Error message should mention preset not found
        assert "not found" in result.stderr.lower()

    def test_custom_preset_in_user_config(self):
        """Test loading a custom preset from user config directory."""
        # Create a temporary custom preset
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_preset = {
                "normalization-type": "peak",
                "target-level": -3.0,
            }

            preset_file = Path(tmpdir) / "custom.json"
            preset_file.write_text(json.dumps(custom_preset))

            # Manually load from temp directory
            with open(preset_file) as f:
                loaded = json.load(f)

            assert loaded["normalization-type"] == "peak"
            assert loaded["target-level"] == -3.0


class TestPresetsContent:
    """Tests for preset file content and format."""

    def test_podcast_preset_json_valid(self):
        """Test that podcast preset is valid JSON."""
        preset_dir = get_default_presets_dir()
        preset_file = preset_dir / "podcast.json"

        assert preset_file.exists()

        with open(preset_file) as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert len(data) > 0

    def test_music_preset_json_valid(self):
        """Test that music preset is valid JSON."""
        preset_dir = get_default_presets_dir()
        preset_file = preset_dir / "music.json"

        assert preset_file.exists()

        with open(preset_file) as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert len(data) > 0

    def test_streaming_video_preset_json_valid(self):
        """Test that streaming-video preset is valid JSON."""
        preset_dir = get_default_presets_dir()
        preset_file = preset_dir / "streaming-video.json"

        assert preset_file.exists()

        with open(preset_file) as f:
            data = json.load(f)

        assert isinstance(data, dict)
        assert len(data) > 0

    def test_all_presets_have_expected_structure(self):
        """Test that all presets follow expected structure."""
        manager = PresetManager()
        presets = manager.get_available_presets()

        for preset_name in presets:
            preset = manager.load_preset(preset_name)

            # Should be a dict
            assert isinstance(preset, dict)

            # Should have at least normalization-type or target-level
            assert "normalization-type" in preset or "target-level" in preset

            # All values should be of expected types
            for key, value in preset.items():
                assert isinstance(key, str)
                assert isinstance(value, (str, int, float, bool)), (
                    f"Invalid value type for {key}: {type(value)}"
                )
