from __future__ import annotations

import json
import logging
import os
import sys
from itertools import chain
from typing import TYPE_CHECKING, Literal

from tqdm import tqdm

from ._cmd_utils import ffmpeg_has_loudnorm, get_ffmpeg_exe, validate_input_file
from ._errors import FFmpegNormalizeError
from ._media_file import MediaFile

if TYPE_CHECKING:
    from ._streams import LoudnessStatisticsWithMetadata

_logger = logging.getLogger(__name__)

NORMALIZATION_TYPES = ("ebu", "rms", "peak")
PCM_INCOMPATIBLE_FORMATS = {"flac", "mp3", "mp4", "ogg", "oga", "opus", "webm"}
PCM_INCOMPATIBLE_EXTS = {"flac", "mp3", "mp4", "m4a", "ogg", "oga", "opus", "webm"}


def check_range(number: object, min_r: float, max_r: float, name: str = "") -> float:
    """
    Checks if "number" is an int or float and is between min_r (inclusive)
    and max_r (inclusive).

    Args:
        number (object): Number to check
        min_r (float): Minimum range
        max_r (float): Maximum range
        name (str): Name of object being checked

    Returns:
        float: within given range

    Raises:
        FFmpegNormalizeError: If number is wrong type or not within range
    """
    if not isinstance(number, (float, int)):
        raise FFmpegNormalizeError(f"{name} must be an int or float")
    if number < min_r or number > max_r:
        raise FFmpegNormalizeError(f"{name} must be within [{min_r},{max_r}]")
    return number


class FFmpegNormalize:
    """
    ffmpeg-normalize class.

    Args:
        normalization_type (str, optional): Normalization type. Defaults to "ebu".
        target_level (float, optional): Target level. Defaults to -23.0.
        print_stats (bool, optional): Print loudnorm stats. Defaults to False.
        loudness_range_target (float, optional): Loudness range target. Defaults to 7.0.
        keep_loudness_range_target (bool, optional): Keep loudness range target. Defaults to False.
        keep_lra_above_loudness_range_target (bool, optional): Keep input loudness range above loudness range target. Defaults to False.
        true_peak (float, optional): True peak. Defaults to -2.0.
        offset (float, optional): Offset. Defaults to 0.0.
        lower_only (bool, optional): Whether the audio should not increase in loudness. Defaults to False.
        auto_lower_loudness_target (bool, optional): Automatically lower EBU Integrated Loudness Target.
        dual_mono (bool, optional): Dual mono. Defaults to False.
        dynamic (bool, optional): Use dynamic EBU R128 normalization. This is a one-pass algorithm and skips the initial media scan. Defaults to False.
        audio_codec (str, optional): Audio codec. Defaults to "pcm_s16le".
        audio_bitrate (float, optional): Audio bitrate. Defaults to None.
        sample_rate (int, optional): Sample rate. Defaults to None.
        audio_channels (int | None, optional): Audio channels. Defaults to None.
        keep_original_audio (bool, optional): Keep original audio. Defaults to False.
        pre_filter (str, optional): Pre filter. Defaults to None.
        post_filter (str, optional): Post filter. Defaults to None.
        video_codec (str, optional): Video codec. Defaults to "copy".
        video_disable (bool, optional): Disable video. Defaults to False.
        subtitle_disable (bool, optional): Disable subtitles. Defaults to False.
        metadata_disable (bool, optional): Disable metadata. Defaults to False.
        chapters_disable (bool, optional): Disable chapters. Defaults to False.
        extra_input_options (list, optional): Extra input options. Defaults to None.
        extra_output_options (list, optional): Extra output options. Defaults to None.
        output_format (str, optional): Output format. Defaults to None.
        extension (str, optional): Output file extension to use for output files that were not explicitly specified. Defaults to "mkv".
        dry_run (bool, optional): Dry run. Defaults to False.
        debug (bool, optional): Debug. Defaults to False.
        progress (bool, optional): Progress. Defaults to False.
        replaygain (bool, optional): Write ReplayGain tags without normalizing. Defaults to False.
        batch (bool, optional): Preserve relative loudness between files (album mode). Defaults to False.
        audio_streams (list[int] | None, optional): List of audio stream indices to normalize. Defaults to None (all streams).
        audio_default_only (bool, optional): Only normalize audio streams with default disposition. Defaults to False.
        keep_other_audio (bool, optional): Keep non-selected audio streams in output (copy without normalization). Defaults to False.

    Raises:
        FFmpegNormalizeError: If the ffmpeg executable is not found or does not support the loudnorm filter.
    """

    # Default parameter values - single source of truth for all defaults
    # Note: output_folder is a CLI-level option and not passed to FFmpegNormalize.__init__
    DEFAULTS = {
        "normalization_type": "ebu",
        "target_level": -23.0,
        "print_stats": False,
        "loudness_range_target": 7.0,
        "keep_loudness_range_target": False,
        "keep_lra_above_loudness_range_target": False,
        "true_peak": -2.0,
        "offset": 0.0,
        "lower_only": False,
        "auto_lower_loudness_target": False,
        "dual_mono": False,
        "dynamic": False,
        "audio_codec": "pcm_s16le",
        "audio_bitrate": None,
        "sample_rate": None,
        "audio_channels": None,
        "keep_original_audio": False,
        "pre_filter": None,
        "post_filter": None,
        "video_codec": "copy",
        "video_disable": False,
        "subtitle_disable": False,
        "metadata_disable": False,
        "chapters_disable": False,
        "extra_input_options": None,
        "extra_output_options": None,
        "output_format": None,
        "output_folder": "normalized",
        "extension": "mkv",
        "dry_run": False,
        "debug": False,
        "progress": False,
        "replaygain": False,
        "batch": False,
        "audio_streams": None,
        "audio_default_only": False,
        "keep_other_audio": False,
    }

    def __init__(
        self,
        normalization_type: Literal["ebu", "rms", "peak"] = "ebu",
        target_level: float = -23.0,
        print_stats: bool = False,
        # threshold=0.5,
        loudness_range_target: float = 7.0,
        keep_loudness_range_target: bool = False,
        keep_lra_above_loudness_range_target: bool = False,
        true_peak: float = -2.0,
        offset: float = 0.0,
        lower_only: bool = False,
        auto_lower_loudness_target: bool = False,
        dual_mono: bool = False,
        dynamic: bool = False,
        audio_codec: str = "pcm_s16le",
        audio_bitrate: float | None = None,
        sample_rate: float | int | None = None,
        audio_channels: int | None = None,
        keep_original_audio: bool = False,
        pre_filter: str | None = None,
        post_filter: str | None = None,
        video_codec: str = "copy",
        video_disable: bool = False,
        subtitle_disable: bool = False,
        metadata_disable: bool = False,
        chapters_disable: bool = False,
        extra_input_options: list[str] | None = None,
        extra_output_options: list[str] | None = None,
        output_format: str | None = None,
        extension: str = "mkv",
        dry_run: bool = False,
        debug: bool = False,
        progress: bool = False,
        replaygain: bool = False,
        batch: bool = False,
        audio_streams: list[int] | None = None,
        audio_default_only: bool = False,
        keep_other_audio: bool = False,
    ):
        self.ffmpeg_exe = get_ffmpeg_exe()
        self.has_loudnorm_capabilities = ffmpeg_has_loudnorm()

        if normalization_type not in NORMALIZATION_TYPES:
            raise FFmpegNormalizeError(
                "Normalization type must be: 'ebu', 'rms', or 'peak'"
            )
        self.normalization_type = normalization_type

        if not self.has_loudnorm_capabilities and self.normalization_type == "ebu":
            raise FFmpegNormalizeError(
                "Your ffmpeg does not support the 'loudnorm' EBU R128 filter. "
                "Please install ffmpeg v4.2 or above, or choose another normalization type."
            )

        if self.normalization_type == "ebu":
            self.target_level = check_range(target_level, -70, -5, name="target_level")
        else:
            self.target_level = check_range(target_level, -99, 0, name="target_level")

        self.print_stats = print_stats

        # self.threshold = float(threshold)

        self.loudness_range_target = check_range(
            loudness_range_target, 1, 50, name="loudness_range_target"
        )

        self.keep_loudness_range_target = keep_loudness_range_target

        if self.keep_loudness_range_target and loudness_range_target != 7.0:
            _logger.warning(
                "Setting --keep-loudness-range-target will override your set loudness range target value! "
                "Remove --keep-loudness-range-target or remove the --lrt/--loudness-range-target option."
            )

        self.keep_lra_above_loudness_range_target = keep_lra_above_loudness_range_target

        if (
            self.keep_loudness_range_target
            and self.keep_lra_above_loudness_range_target
        ):
            raise FFmpegNormalizeError(
                "Options --keep-loudness-range-target and --keep-lra-above-loudness-range-target are mutually exclusive! "
                "Please choose just one of the two options."
            )

        self.true_peak = check_range(true_peak, -9, 0, name="true_peak")
        self.offset = check_range(offset, -99, 99, name="offset")
        self.lower_only = lower_only
        self.auto_lower_loudness_target = auto_lower_loudness_target

        # Ensure library user is passing correct types
        assert isinstance(dual_mono, bool), "dual_mono must be bool"
        assert isinstance(dynamic, bool), "dynamic must be bool"

        self.dual_mono = dual_mono
        self.dynamic = dynamic
        self.sample_rate = None if sample_rate is None else int(sample_rate)
        self.audio_channels = None if audio_channels is None else int(audio_channels)

        self.audio_codec = audio_codec
        self.audio_bitrate = audio_bitrate
        self.keep_original_audio = keep_original_audio
        self.video_codec = video_codec
        self.video_disable = video_disable
        self.subtitle_disable = subtitle_disable
        self.metadata_disable = metadata_disable
        self.chapters_disable = chapters_disable

        self.extra_input_options = extra_input_options
        self.extra_output_options = extra_output_options
        self.pre_filter = pre_filter
        self.post_filter = post_filter

        self.output_format = output_format
        self.extension = extension
        self.dry_run = dry_run
        self.debug = debug
        self.progress = progress
        self.replaygain = replaygain
        self.batch = batch

        # Stream selection options
        self.audio_streams = audio_streams
        self.audio_default_only = audio_default_only
        self.keep_other_audio = keep_other_audio

        if (
            self.audio_codec is None or "pcm" in self.audio_codec
        ) and self.output_format in PCM_INCOMPATIBLE_FORMATS:
            raise FFmpegNormalizeError(
                f"Output format {self.output_format} does not support PCM audio. "
                "Please choose a suitable audio codec with the -c:a option."
            )

        # replaygain only works for EBU for now
        if self.replaygain and self.normalization_type != "ebu":
            raise FFmpegNormalizeError(
                "ReplayGain only works for EBU normalization type for now."
            )

        # Validate stream selection options
        if self.audio_streams is not None and self.audio_default_only:
            raise FFmpegNormalizeError(
                "Cannot use both audio_streams and audio_default_only together."
            )

        if self.keep_other_audio and self.keep_original_audio:
            raise FFmpegNormalizeError(
                "Cannot use both --keep-other-audio and --keep-original-audio together. "
                "Use --keep-original-audio to keep all original streams alongside normalized ones, "
                "or --keep-other-audio to keep only non-selected streams as passthrough."
            )

        self.stats: list[LoudnessStatisticsWithMetadata] = []
        self.media_files: list[MediaFile] = []
        self.file_count = 0

    def add_media_file(self, input_file: str, output_file: str) -> None:
        """
        Add a media file to normalize

        Args:
            input_file (str): Path to input file
            output_file (str): Path to output file
        """
        if not os.path.exists(input_file):
            raise FFmpegNormalizeError(f"file {input_file} does not exist")

        ext = os.path.splitext(output_file)[1][1:]
        if (
            self.audio_codec is None or "pcm" in self.audio_codec
        ) and ext in PCM_INCOMPATIBLE_EXTS:
            raise FFmpegNormalizeError(
                f"Output extension {ext} does not support PCM audio. "
                "Please choose a suitable audio codec with the -c:a option."
            )

        self.media_files.append(MediaFile(self, input_file, output_file))
        self.file_count += 1

    @staticmethod
    def validate_input_files(input_files: list[str]) -> list[str]:
        """
        Validate all input files before processing.

        This method checks that each input file exists, is readable, and contains
        at least one audio stream. All files are validated upfront so that users
        can fix all issues before rerunning the batch.

        Args:
            input_files: List of input file paths to validate

        Returns:
            list: List of error messages for invalid files. Empty if all files are valid.
        """
        errors = []
        for input_file in input_files:
            is_valid, error_msg = validate_input_file(input_file)
            if not is_valid and error_msg:
                errors.append(error_msg)
        return errors

    def _calculate_batch_reference(self) -> float | None:
        """
        Calculate the batch reference loudness by averaging measurements across all files.

        Returns:
            float | None: The batch reference loudness value, or None if no measurements found.

        Note:
            TODO: Add option to specify different averaging methods (duration-weighted,
            use quietest/loudest track, etc.)
        """
        measurements: list[float] = []

        for media_file in self.media_files:
            # Access audio streams from the streams dict
            audio_streams = media_file.streams.get("audio", {})
            for stream in audio_streams.values():
                if self.normalization_type == "ebu":
                    # Get EBU integrated loudness from first pass
                    ebu_stats = stream.loudness_statistics.get("ebu_pass1")
                    if ebu_stats and "input_i" in ebu_stats:
                        measurements.append(float(ebu_stats["input_i"]))
                elif self.normalization_type == "rms":
                    # Get RMS mean value
                    mean = stream.loudness_statistics.get("mean")
                    if mean is not None:
                        measurements.append(float(mean))
                elif self.normalization_type == "peak":
                    # Get peak max value
                    max_val = stream.loudness_statistics.get("max")
                    if max_val is not None:
                        measurements.append(float(max_val))

        if not measurements:
            _logger.warning(
                "No loudness measurements found for batch reference calculation. "
                "Batch mode will not be applied."
            )
            return None

        # Simple average of all measurements
        batch_reference = sum(measurements) / len(measurements)
        _logger.debug(f"Batch mode: Measurements for batch reference: {measurements}")
        _logger.info(
            f"Batch mode: Calculated reference loudness = {batch_reference:.2f} "
            f"({self.normalization_type.upper()}, averaged from {len(measurements)} stream(s))"
        )

        return batch_reference

    def run_normalization(self) -> None:
        """
        Run the normalization procedures.

        In batch mode, all files are analyzed first (first pass), then a batch reference
        loudness is calculated, and finally all files are normalized (second pass) with
        adjustments relative to the batch reference to preserve relative loudness.

        In non-batch mode, each file is processed completely (both passes) before
        moving to the next file.
        """
        if self.batch:
            # Batch mode: analyze all files first, then normalize with relative adjustments
            _logger.info(
                f"Batch mode enabled: processing {self.file_count} file(s) while preserving relative loudness"
            )

            # Recommend RMS/Peak for album normalization instead of EBU
            if self.normalization_type == "ebu":
                _logger.warning(
                    "Using EBU R128 normalization with --batch. For true album normalization where "
                    "all tracks are shifted by the same amount, consider using --normalization-type rms "
                    "or --normalization-type peak instead. EBU normalization applies different processing "
                    "to each track based on its loudness characteristics, which may alter relative levels "
                    "slightly due to psychoacoustic adjustments."
                )

            # Warn if using dynamic EBU mode with batch
            if self.dynamic and self.normalization_type == "ebu":
                _logger.warning(
                    "ffmpeg uses dynamic EBU normalization. This may change relative "
                    "loudness within a file. Use linear mode for true album normalization, or "
                    "switch to --normalization-type peak or --normalization-type rms instead. "
                    "To force linear mode, use --keep-lra-above-loudness-range-target or "
                    "--keep-loudness-range-target."
                )

            # Phase 1: Run first pass on all files to collect measurements
            _logger.info("Phase 1: Analyzing all files...")
            for index, media_file in enumerate(
                tqdm(
                    self.media_files,
                    desc="Analysis",
                    disable=not self.progress,
                    position=0,
                )
            ):
                _logger.info(
                    f"Analyzing file {media_file} ({index + 1} of {self.file_count})"
                )

                try:
                    # Only run first pass if not in dynamic EBU mode
                    if not (self.dynamic and self.normalization_type == "ebu"):
                        media_file._first_pass()
                    else:
                        _logger.debug(
                            "Dynamic EBU mode: First pass skipped for this file."
                        )
                except Exception as e:
                    if len(self.media_files) > 1:
                        _logger.error(
                            f"Error analyzing input file {media_file}, will "
                            f"continue batch-processing. Error was: {e}"
                        )
                    else:
                        raise e

            # Phase 2: Calculate batch reference loudness
            batch_reference = self._calculate_batch_reference()

            # Phase 3: Run second pass on all files with batch reference
            _logger.info("Phase 2: Normalizing all files...")
            for index, media_file in enumerate(
                tqdm(
                    self.media_files,
                    desc="Normalization",
                    disable=not self.progress,
                    position=0,
                )
            ):
                _logger.info(
                    f"Normalizing file {media_file} ({index + 1} of {self.file_count})"
                )

                try:
                    media_file.run_normalization(batch_reference=batch_reference)
                except Exception as e:
                    if len(self.media_files) > 1:
                        _logger.error(
                            f"Error processing input file {media_file}, will "
                            f"continue batch-processing. Error was: {e}"
                        )
                    else:
                        raise e
        else:
            # Non-batch mode: process each file completely before moving to the next
            for index, media_file in enumerate(
                tqdm(
                    self.media_files, desc="File", disable=not self.progress, position=0
                )
            ):
                _logger.info(
                    f"Normalizing file {media_file} ({index + 1} of {self.file_count})"
                )

                try:
                    media_file.run_normalization()
                except Exception as e:
                    if len(self.media_files) > 1:
                        _logger.error(
                            f"Error processing input file {media_file}, will "
                            f"continue batch-processing. Error was: {e}"
                        )
                    else:
                        raise e

        if self.print_stats:
            json.dump(
                list(
                    chain.from_iterable(
                        media_file.get_stats() for media_file in self.media_files
                    )
                ),
                sys.stdout,
                indent=4,
            )
            print()
