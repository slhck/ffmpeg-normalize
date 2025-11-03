"""Preset management for ffmpeg-normalize."""

from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any

from ._ffmpeg_normalize import FFmpegNormalize

_logger = logging.getLogger(__name__)


def get_config_dir() -> Path:
    """Get the platform-specific config directory for ffmpeg-normalize.

    Returns:
        Path: Configuration directory for presets

    On Linux/macOS:
        - XDG_CONFIG_HOME/ffmpeg-normalize (if XDG_CONFIG_HOME is set)
        - ~/.config/ffmpeg-normalize (otherwise)

    On Windows:
        - %APPDATA%/ffmpeg-normalize
    """
    if os.name == "nt":  # Windows
        appdata = os.getenv("APPDATA")
        if appdata:
            config_dir = Path(appdata) / "ffmpeg-normalize"
        else:
            config_dir = Path.home() / "AppData" / "Roaming" / "ffmpeg-normalize"
    else:  # Linux/macOS
        xdg_config = os.getenv("XDG_CONFIG_HOME")
        if xdg_config:
            config_dir = Path(xdg_config) / "ffmpeg-normalize"
        else:
            config_dir = Path.home() / ".config" / "ffmpeg-normalize"

    return config_dir


def get_presets_dir() -> Path:
    """Get the presets directory.

    Returns:
        Path: Directory containing preset files
    """
    return get_config_dir() / "presets"


def get_default_presets_dir() -> Path:
    """Get the package default presets directory.

    Returns:
        Path: Directory containing default preset files bundled with the package
    """
    # Get the directory where this module is located
    module_dir = Path(__file__).parent
    return module_dir / "data" / "presets"


class PresetManager:
    """Manages loading and merging of presets with CLI arguments."""

    def __init__(self) -> None:
        """Initialize the preset manager."""
        self.presets_dir = get_presets_dir()
        self.default_presets_dir = get_default_presets_dir()

    def get_available_presets(self) -> list[str]:
        """Get list of available preset names.

        Includes both user-installed presets and default presets from the package.
        User presets take precedence if they have the same name.

        Returns:
            list[str]: List of available preset names (without .json extension)
        """
        presets = set()

        # Get presets from user config directory
        if self.presets_dir.exists():
            for file in self.presets_dir.glob("*.json"):
                presets.add(file.stem)

        # Get default presets from package
        if self.default_presets_dir.exists():
            for file in self.default_presets_dir.glob("*.json"):
                presets.add(file.stem)

        return sorted(presets)

    def load_preset(self, preset_name: str) -> dict[str, Any]:
        """Load a preset file by name.

        Checks user config directory first, then falls back to package defaults.

        Args:
            preset_name: Name of the preset (without .json extension)

        Returns:
            dict[str, Any]: Preset configuration as a dictionary

        Raises:
            FileNotFoundError: If preset file doesn't exist
            json.JSONDecodeError: If preset file is invalid JSON
        """
        # Try user config directory first
        preset_path = self.presets_dir / f"{preset_name}.json"

        # Fall back to package default presets
        if not preset_path.exists():
            preset_path = self.default_presets_dir / f"{preset_name}.json"

        if not preset_path.exists():
            raise FileNotFoundError(
                f"Preset '{preset_name}' not found. "
                f"Available presets: {', '.join(self.get_available_presets()) or 'none'}"
            )

        try:
            with open(preset_path, "r") as f:
                preset_data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in preset '{preset_name}': {e.msg}",
                e.doc,
                e.pos,
            )

        if not isinstance(preset_data, dict):
            raise ValueError(
                f"Preset must be a JSON object, got {type(preset_data).__name__}"
            )

        return preset_data

    def merge_preset_with_args(
        self, preset_data: dict[str, Any], cli_args: Any
    ) -> None:
        """Merge preset data with CLI arguments, giving precedence to CLI args.

        Args:
            preset_data: Dictionary of preset configuration
            cli_args: Parsed CLI arguments (argparse Namespace object)

        The CLI arguments take precedence over preset values. This function modifies
        cli_args in place by setting attributes that were not explicitly provided
        on the command line.
        """
        for key, value in preset_data.items():
            # Convert hyphens to underscores to match argparse attribute names
            attr_name = key.replace("-", "_")

            # Check if this attribute exists in cli_args
            if not hasattr(cli_args, attr_name):
                _logger.warning(
                    f"Preset option '{key}' is not a valid ffmpeg-normalize option. Skipping."
                )
                continue

            # Get the current value
            current_value = getattr(cli_args, attr_name)

            # Check if this was explicitly set by the user
            # For most types, we can infer this by checking against the defaults:
            # - None values were not explicitly set
            # - Empty lists were not explicitly set
            # - False boolean flags were not explicitly set
            # - Default numeric values (specific to each option) need special handling

            should_apply = False

            if isinstance(value, bool):
                # For boolean flags, apply preset only if currently False (not set)
                should_apply = not current_value
            elif isinstance(current_value, list):
                # For lists (like output), apply preset only if empty
                should_apply = not current_value
            elif current_value is None:
                # For None values, always apply preset (not explicitly set)
                should_apply = True
            else:
                # For other values (numbers, strings), check if they match known defaults
                # This is conservative: only override if the value is a known default
                if (
                    attr_name in FFmpegNormalize.DEFAULTS
                    and current_value == FFmpegNormalize.DEFAULTS[attr_name]
                ):
                    should_apply = True

            if should_apply:
                setattr(cli_args, attr_name, value)
                _logger.debug(f"Applied preset option '{key}' = {value}")

    def validate_preset(self, preset_name: str) -> tuple[bool, str]:
        """Validate that a preset file exists and is valid.

        Args:
            preset_name: Name of the preset to validate

        Returns:
            tuple[bool, str]: (is_valid, message)
        """
        try:
            self.load_preset(preset_name)
            return True, f"Preset '{preset_name}' is valid"
        except FileNotFoundError as e:
            return False, str(e)
        except (json.JSONDecodeError, ValueError) as e:
            return False, f"Error loading preset '{preset_name}': {e}"

    def install_default_presets(self, force: bool = False) -> tuple[bool, str]:
        """Install default presets to user config directory.

        Args:
            force: If True, overwrite existing presets

        Returns:
            tuple[bool, str]: (success, message)
        """
        try:
            # Create presets directory if it doesn't exist
            self.presets_dir.mkdir(parents=True, exist_ok=True)

            if not self.default_presets_dir.exists():
                return (
                    False,
                    f"Default presets directory not found at {self.default_presets_dir}",
                )

            # Copy all default presets
            installed = []
            skipped = []

            for preset_file in self.default_presets_dir.glob("*.json"):
                dest_file = self.presets_dir / preset_file.name

                if dest_file.exists() and not force:
                    skipped.append(preset_file.name)
                else:
                    shutil.copy2(preset_file, dest_file)
                    installed.append(preset_file.name)

            message = f"Installed {len(installed)} preset(s) to {self.presets_dir}"
            if skipped:
                message += f" ({len(skipped)} skipped, use --force to overwrite)"

            return True, message

        except Exception as e:
            return False, f"Error installing default presets: {e}"
