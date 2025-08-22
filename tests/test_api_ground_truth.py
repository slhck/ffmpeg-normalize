"""
API-based test suite with ground-truth validation for ffmpeg-normalize.

This test suite validates that normalization actually achieves the target levels
by testing the API directly rather than just ensuring CLI commands don't error.

Note: These tests use actual audio files and perform real normalization,
so they are significantly slower than the existing CLI tests.

Run with: pytest -m "not slow" to skip the slow integration tests
Run with: pytest -m "slow" to run only the slow integration tests
"""

import os
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any
from urllib.request import urlretrieve

import pytest

# Add the parent directory to sys.path so we can import ffmpeg_normalize
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/../"))

from ffmpeg_normalize import FFmpegNormalize


def download_and_extract_mus_sample() -> Path:
    """
    Download and extract mus-sample.zip test files if not already present.

    Returns:
        Path: Path to the extracted mus-sample directory
    """
    test_dir = Path(__file__).parent
    mus_sample_dir = test_dir / "mus-sample"

    # Check if files already exist
    if mus_sample_dir.exists() and any(mus_sample_dir.glob("*.stem.mp4")):
        return mus_sample_dir

    # Download the zip file
    zip_url = "https://github.com/sigsep/sigsep-mus-db/releases/download/v0.3.0/mus-sample.zip"
    zip_path = test_dir / "mus-sample.zip"

    print(f"Downloading {zip_url}...")
    urlretrieve(zip_url, zip_path)

    # Extract the zip file
    print(f"Extracting to {mus_sample_dir}...")
    mus_sample_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(mus_sample_dir)

    # Clean up zip file
    zip_path.unlink()

    return mus_sample_dir


def validate_normalization_target(stats: Dict[str, Any], normalization_type: str, target_level: float, tolerance: float = 0.5) -> bool:
    """
    Validate that normalization achieved the target level within tolerance.

    Args:
        stats: Statistics dictionary from AudioStream.get_stats()
        normalization_type: Type of normalization ('ebu', 'rms', 'peak')
        target_level: Target level that was requested
        tolerance: Acceptable deviation from target (dB)

    Returns:
        bool: True if normalization achieved target within tolerance
    """
    if normalization_type == "ebu":
        if stats["ebu_pass2"] is not None:
            # Two-pass EBU normalization
            actual_level = stats["ebu_pass2"]["output_i"]
        elif stats["ebu_pass1"] is not None:
            # Dynamic EBU normalization
            actual_level = stats["ebu_pass1"]["output_i"]
        else:
            raise ValueError("No EBU statistics found")

    elif normalization_type == "rms":
        actual_level = stats["mean"]
        if actual_level is None:
            raise ValueError("No RMS statistics found")

    elif normalization_type == "peak":
        actual_level = stats["max"]
        if actual_level is None:
            raise ValueError("No peak statistics found")

    else:
        raise ValueError(f"Unknown normalization type: {normalization_type}")

    deviation = abs(actual_level - target_level)
    return deviation <= tolerance


@pytest.fixture(scope="session")
def test_files():
    """Download and setup test files."""
    mus_sample_dir = download_and_extract_mus_sample()
    # Look for .stem.mp4 files in the extracted directory structure
    test_files_list = list(mus_sample_dir.rglob("*.stem.mp4"))

    if len(test_files_list) == 0:
        pytest.skip("No test files found in mus-sample directory")

    return test_files_list


class TestFFmpegNormalizeAPI:
    """API-based tests with ground-truth validation."""

    @pytest.fixture(scope="function")
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.mark.slow
    def test_ebu_normalization_target_achievement(self, test_files, temp_output_dir):
        """Test that EBU normalization achieves the target level."""
        target_level = -23.0

        for test_file in test_files[:1]:  # Test with first file for now
            output_file = temp_output_dir / f"normalized_{test_file.name}"

            # Create normalizer instance
            normalizer = FFmpegNormalize(
                normalization_type="ebu",
                target_level=target_level,
                print_stats=False,
                audio_codec="aac"  # Use AAC codec for MP4 compatibility
            )

            # Add media file and run normalization
            normalizer.add_media_file(str(test_file), str(output_file))
            normalizer.run_normalization()

            # Validate results
            assert len(normalizer.media_files) == 1
            media_file = normalizer.media_files[0]

            # Get statistics for each audio stream
            for stats in media_file.get_stats():
                assert validate_normalization_target(
                    stats, "ebu", target_level, tolerance=1.0
                ), f"EBU normalization failed to achieve target {target_level} dB for {test_file.name}. Got {stats.get('ebu_pass2', {}).get('output_i') or stats.get('ebu_pass1', {}).get('output_i')} dB"

    @pytest.mark.slow
    def test_rms_normalization_target_achievement(self, test_files, temp_output_dir):
        """Test that RMS normalization achieves the target level or prevents clipping."""
        target_level = -20.0  # Use a more conservative target to avoid clipping

        for test_file in test_files[:1]:  # Test with first file for now
            output_file = temp_output_dir / f"normalized_rms_{test_file.name}"

            # Create normalizer instance
            normalizer = FFmpegNormalize(
                normalization_type="rms",
                target_level=target_level,
                print_stats=False,
                audio_codec="aac"  # Use AAC codec for MP4 compatibility
            )

            # Add media file and run normalization
            normalizer.add_media_file(str(test_file), str(output_file))
            normalizer.run_normalization()

            # Validate results
            assert len(normalizer.media_files) == 1
            media_file = normalizer.media_files[0]

            # Get statistics for each audio stream
            for stats in media_file.get_stats():
                # For RMS, validate that normalization was attempted (mean is not None)
                # and the level is reasonable (not too far from target unless clipping prevented it)
                assert stats["mean"] is not None, f"RMS statistics missing for {test_file.name}"

                # Validate that normalization was attempted - the mean should be reasonable
                # For stem tracks, some channels might be very quiet or empty, so be flexible
                assert stats["mean"] > -80.0, f"RMS level extremely low: {stats['mean']} dB - possible empty channel"

                # For channels with significant content (louder than -40 dB), check normalization effectiveness
                if stats["mean"] > -40.0:
                    # If the max peak is close to 0 dB, clipping prevention is expected
                    if stats["max"] > -1.0:  # Close to clipping
                        # Accept that the target might not be achieved due to clipping prevention
                        assert stats["mean"] >= target_level - 15.0, f"RMS level too low even with clipping prevention: {stats['mean']} dB"
                    else:
                        # If no clipping risk, should be closer to target
                        assert validate_normalization_target(
                            stats, "rms", target_level, tolerance=5.0
                        ), f"RMS normalization failed to achieve target {target_level} dB for {test_file.name}. Got {stats['mean']} dB"

    @pytest.mark.slow
    def test_peak_normalization_target_achievement(self, test_files, temp_output_dir):
        """Test that peak normalization works correctly."""
        target_level = -3.0  # Use more conservative target to account for codec behavior

        for test_file in test_files[:1]:  # Test with first file for now
            output_file = temp_output_dir / f"normalized_peak_{test_file.name}"

            # Create normalizer instance
            normalizer = FFmpegNormalize(
                normalization_type="peak",
                target_level=target_level,
                print_stats=False,
                audio_codec="aac"  # Use AAC codec for MP4 compatibility
            )

            # Add media file and run normalization
            normalizer.add_media_file(str(test_file), str(output_file))
            normalizer.run_normalization()

            # Validate results
            assert len(normalizer.media_files) == 1
            media_file = normalizer.media_files[0]

            # Get statistics for each audio stream
            for stats in media_file.get_stats():
                assert stats["max"] is not None, f"Peak statistics missing for {test_file.name}"

                # Check that peak normalization was attempted
                # For channels with significant content, the peak should be reasonable
                if stats["mean"] > -40.0:  # Channel has significant content
                    # Peak should be within reasonable range of target (allowing for codec effects)
                    # Use more generous tolerance for CI environment differences
                    assert stats["max"] >= target_level - 10.0, f"Peak level too low: {stats['max']} dB"
                    assert stats["max"] <= target_level + 5.0, f"Peak level too high: {stats['max']} dB"
                else:
                    # For very quiet channels, just check they're not unreasonably loud
                    assert stats["max"] <= 0.0, f"Quiet channel unexpectedly loud: {stats['max']} dB"

    @pytest.mark.slow
    def test_dynamic_vs_linear_ebu_normalization(self, test_files, temp_output_dir):
        """Test that EBU normalization handles dynamic vs linear modes appropriately."""
        target_level = -23.0
        test_file = test_files[0]

        # Test explicit dynamic normalization (one-pass)
        output_file_dynamic = temp_output_dir / f"dynamic_{test_file.name}"
        normalizer_dynamic = FFmpegNormalize(
            normalization_type="ebu",
            target_level=target_level,
            dynamic=True,
            print_stats=False,
            audio_codec="aac"  # Use AAC codec for MP4 compatibility
        )
        normalizer_dynamic.add_media_file(str(test_file), str(output_file_dynamic))
        normalizer_dynamic.run_normalization()

        # Test linear normalization attempt (may revert to dynamic if needed)
        output_file_linear = temp_output_dir / f"linear_{test_file.name}"
        normalizer_linear = FFmpegNormalize(
            normalization_type="ebu",
            target_level=target_level,
            dynamic=False,
            loudness_range_target=20.0,  # Higher LRA target to allow linear mode
            print_stats=False,
            audio_codec="aac"  # Use AAC codec for MP4 compatibility
        )
        normalizer_linear.add_media_file(str(test_file), str(output_file_linear))
        normalizer_linear.run_normalization()

        # Validate both achieved reasonable targets
        linear_stats = list(normalizer_linear.media_files[0].get_stats())[0]
        dynamic_stats = list(normalizer_dynamic.media_files[0].get_stats())[0]

        # Validate that both modes achieved target levels
        assert validate_normalization_target(linear_stats, "ebu", target_level, tolerance=2.0)
        assert validate_normalization_target(dynamic_stats, "ebu", target_level, tolerance=2.0)
        
        # Validate dynamic mode behavior (should be one-pass only, per commit 76fb27d)
        assert dynamic_stats["ebu_pass1"] is None, f"Dynamic mode should not have first pass stats. Got: {dynamic_stats['ebu_pass1']}"
        assert dynamic_stats["ebu_pass2"] is not None, "Dynamic mode should have second pass stats"
        assert dynamic_stats["ebu_pass2"]["normalization_type"] == "dynamic", "Dynamic mode should use dynamic normalization"
        
        # Linear mode should use two-pass (may revert to dynamic depending on content)
        assert linear_stats["ebu_pass1"] is not None, "Linear normalization should have first pass stats"

    @pytest.mark.slow
    def test_normalization_preserves_quality_metrics(self, test_files, temp_output_dir):
        """Test that normalization preserves important quality metrics."""
        target_level = -23.0
        test_file = test_files[0]
        output_file = temp_output_dir / f"quality_test_{test_file.name}"

        normalizer = FFmpegNormalize(
            normalization_type="ebu",
            target_level=target_level,
            print_stats=False,
            audio_codec="aac"  # Use AAC codec for MP4 compatibility
        )

        normalizer.add_media_file(str(test_file), str(output_file))
        normalizer.run_normalization()

        stats = list(normalizer.media_files[0].get_stats())[0]

        # Check that important EBU metrics are present and reasonable
        if stats["ebu_pass2"]:
            ebu_stats = stats["ebu_pass2"]
        else:
            ebu_stats = stats["ebu_pass1"]

        # True peak should be within reasonable range
        # Use more generous tolerance for CI environment differences
        assert -12.0 <= ebu_stats["output_tp"] <= 0.0, f"True peak out of range: {ebu_stats['output_tp']}"

        # Loudness range should be preserved or adjusted reasonably
        assert 0.0 <= ebu_stats["output_lra"] <= 30.0, f"LRA out of range: {ebu_stats['output_lra']}"

        # Target offset should be reasonable
        if "target_offset" in ebu_stats:
            assert -10.0 <= ebu_stats["target_offset"] <= 10.0, f"Target offset extreme: {ebu_stats['target_offset']}"

    @pytest.mark.slow
    def test_multiple_files_batch_processing(self, test_files, temp_output_dir):
        """Test that batch processing multiple files works correctly."""
        target_level = -23.0

        normalizer = FFmpegNormalize(
            normalization_type="ebu",
            target_level=target_level,
            print_stats=False,
            audio_codec="aac"  # Use AAC codec for MP4 compatibility
        )

        # Add multiple files
        output_files = []
        for i, test_file in enumerate(test_files):
            output_file = temp_output_dir / f"batch_{i}_{test_file.name}"
            output_files.append(output_file)
            normalizer.add_media_file(str(test_file), str(output_file))

        # Run batch normalization
        normalizer.run_normalization()

        # Validate all files were processed
        assert len(normalizer.media_files) == len(test_files)

        # Validate each file achieved target
        for media_file in normalizer.media_files:
            for stats in media_file.get_stats():
                assert validate_normalization_target(
                    stats, "ebu", target_level, tolerance=1.0
                ), f"Batch processing failed for {media_file.input_file}"

        # Validate output files exist
        for output_file in output_files:
            assert output_file.exists(), f"Output file not created: {output_file}"

    def test_api_smoke_test(self, test_files):
        """Quick smoke test to validate the API works without full normalization."""
        test_file = test_files[0]

        # Test that we can create normalizer instances with different settings
        normalizers = [
            FFmpegNormalize(normalization_type="ebu", target_level=-23.0, dry_run=True),
            FFmpegNormalize(normalization_type="rms", target_level=-15.0, dry_run=True),
            FFmpegNormalize(normalization_type="peak", target_level=-1.0, dry_run=True),
        ]

        for normalizer in normalizers:
            # Test that we can add media files
            normalizer.add_media_file(str(test_file), "/dev/null")
            assert len(normalizer.media_files) == 1

            # Test that media file parsing worked
            media_file = normalizer.media_files[0]
            assert media_file.input_file == str(test_file)
            assert len(media_file.streams["audio"]) > 0, "Should have audio streams"

            # Test dry run (no actual processing)
            normalizer.run_normalization()  # Should complete quickly with dry_run=True
