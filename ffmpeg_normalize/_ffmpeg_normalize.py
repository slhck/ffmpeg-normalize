from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING, Literal

from tqdm import tqdm

from ._cmd_utils import ffmpeg_has_loudnorm, get_ffmpeg_exe
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
        dual_mono (bool, optional): Dual mono. Defaults to False.
        dynamic (bool, optional): Dynamic. Defaults to False.
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
        dry_run (bool, optional): Dry run. Defaults to False.
        debug (bool, optional): Debug. Defaults to False.
        progress (bool, optional): Progress. Defaults to False.

    Raises:
        FFmpegNormalizeError: If the ffmpeg executable is not found or does not support the loudnorm filter.
    """

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
        dry_run: bool = False,
        debug: bool = False,
        progress: bool = False,
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
        self.dry_run = dry_run
        self.debug = debug
        self.progress = progress

        if (
            self.audio_codec is None or "pcm" in self.audio_codec
        ) and self.output_format in PCM_INCOMPATIBLE_FORMATS:
            raise FFmpegNormalizeError(
                f"Output format {self.output_format} does not support PCM audio. "
                "Please choose a suitable audio codec with the -c:a option."
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

    def run_normalization(self) -> None:
        """
        Run the normalization procedures
        """
        for index, media_file in enumerate(
            tqdm(self.media_files, desc="File", disable=not self.progress, position=0)
        ):
            _logger.info(
                f"Normalizing file {media_file} ({index + 1} of {self.file_count})"
            )

            try:
                media_file.run_normalization()
            except Exception as e:
                if len(self.media_files) > 1:
                    # simply warn and do not die
                    _logger.error(
                        f"Error processing input file {media_file}, will "
                        f"continue batch-processing. Error was: {e}"
                    )
                else:
                    # raise the error so the program will exit
                    raise e

            _logger.info(f"Normalized file written to {media_file.output_file}")

        if self.print_stats and self.stats:
            print(json.dumps(self.stats, indent=4))
