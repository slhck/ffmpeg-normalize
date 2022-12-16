import os
import json
from numbers import Number
from typing import List, Literal, Union
from tqdm import tqdm

from ._cmd_utils import get_ffmpeg_exe, ffmpeg_has_loudnorm
from ._media_file import MediaFile
from ._errors import FFmpegNormalizeError
from ._logger import setup_custom_logger

logger = setup_custom_logger("ffmpeg_normalize")

NORMALIZATION_TYPES = ["ebu", "rms", "peak"]
PCM_INCOMPATIBLE_FORMATS = ["mp4", "mp3", "ogg", "webm"]
PCM_INCOMPATIBLE_EXTS = ["mp4", "m4a", "mp3", "ogg", "webm", "flac", "opus"]


def check_range(number: float, min_r: float, max_r: float, name: str = "") -> float:
    """
    Check if a number is within a given range.

    Args:
        number (float): Number to check
        min_r (float): Minimum range
        max_r (float): Maximum range
        name (str): Name of the number to check

    Returns:
        float: Number if it is within the range

    Raises:
        FFmpegNormalizeError: If the number is not within the range
        Exception: If the number cannot be converted to a float
    """
    try:
        number = float(number)
        if number < min_r or number > max_r:
            raise FFmpegNormalizeError(f"{name} must be within [{min_r},{max_r}]")
        return number
    except Exception as e:
        raise e


class FFmpegNormalize:
    """
    ffmpeg-normalize class.

    Args:
        normalization_type (str, optional): Normalization type. Defaults to "ebu".
        target_level (float, optional): Target level. Defaults to -23.0.
        print_stats (bool, optional): Print loudnorm stats. Defaults to False.
        loudness_range_target (float, optional): Loudness range target. Defaults to 7.0.
        keep_loudness_range_target (bool, optional): Keep loudness range target. Defaults to False.
        true_peak (float, optional): True peak. Defaults to -2.0.
        offset (float, optional): Offset. Defaults to 0.0.
        dual_mono (bool, optional): Dual mono. Defaults to False.
        dynamic (bool, optional): Dynamic. Defaults to False.
        audio_codec (str, optional): Audio codec. Defaults to "pcm_s16le".
        audio_bitrate (float, optional): Audio bitrate. Defaults to None.
        sample_rate (int, optional): Sample rate. Defaults to None.
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
        true_peak: float = -2.0,
        offset: float = 0.0,
        dual_mono: bool = False,
        dynamic: bool = False,
        audio_codec: str = "pcm_s16le",
        audio_bitrate: Union[float, None] = None,
        sample_rate: Union[int, None] = None,
        keep_original_audio: bool = False,
        pre_filter: Union[str, None] = None,
        post_filter: Union[str, None] = None,
        video_codec="copy",
        video_disable: bool = False,
        subtitle_disable: bool = False,
        metadata_disable: bool = False,
        chapters_disable: bool = False,
        extra_input_options: Union[List[str], None] = None,
        extra_output_options: Union[List[str], None] = None,
        output_format: Union[str, None] = None,
        dry_run: bool = False,
        debug: bool = False,
        progress: bool = False,
    ):
        self.ffmpeg_exe = get_ffmpeg_exe()
        self.has_loudnorm_capabilities = ffmpeg_has_loudnorm()

        self.normalization_type = normalization_type
        if not self.has_loudnorm_capabilities and self.normalization_type == "ebu":
            raise FFmpegNormalizeError(
                "Your ffmpeg version does not support the 'loudnorm' EBU R128 filter. "
                "Please install ffmpeg v3.1 or above, or choose another normalization type."
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
            logger.warning(
                "Setting --keep-loudness-range-target will override your set loudness range target value! "
                "Remove --keep-loudness-range-target or remove the --lrt/--loudness-range-target option."
            )

        self.true_peak = check_range(true_peak, -9, 0, name="true_peak")
        self.offset = check_range(offset, -99, 99, name="offset")

        self.dual_mono = True if dual_mono in ["true", True] else False
        self.dynamic = True if dynamic in ["true", True] else False
        self.audio_codec = audio_codec
        self.audio_bitrate = audio_bitrate
        self.sample_rate = int(sample_rate) if sample_rate is not None else None
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

        self.stats = []

        if (
            self.output_format
            and (self.audio_codec is None or "pcm" in self.audio_codec)
            and self.output_format in PCM_INCOMPATIBLE_FORMATS
        ):
            raise FFmpegNormalizeError(
                f"Output format {self.output_format} does not support PCM audio. "
                + "Please choose a suitable audio codec with the -c:a option."
            )

        if normalization_type not in NORMALIZATION_TYPES:
            raise FFmpegNormalizeError(
                f"Normalization type must be one of {NORMALIZATION_TYPES}"
            )

        if self.target_level and not isinstance(self.target_level, Number):
            raise FFmpegNormalizeError("target_level must be a number")

        if self.loudness_range_target and not isinstance(
            self.loudness_range_target, Number
        ):
            raise FFmpegNormalizeError("loudness_range_target must be a number")

        if self.true_peak and not isinstance(self.true_peak, Number):
            raise FFmpegNormalizeError("true_peak must be a number")

        if float(target_level) > 0:
            raise FFmpegNormalizeError("Target level must be below 0")

        self.media_files = []
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

        mf = MediaFile(self, input_file, output_file)
        self.media_files.append(mf)

        self.file_count += 1

    def run_normalization(self) -> None:
        """
        Run the normalization procedures
        """
        for index, media_file in enumerate(
            tqdm(self.media_files, desc="File", disable=not self.progress, position=0)
        ):
            logger.info(
                f"Normalizing file {media_file} ({index + 1} of {self.file_count})"
            )

            try:
                media_file.run_normalization()
            except Exception as e:
                if len(self.media_files) > 1:
                    # simply warn and do not die
                    logger.error(
                        f"Error processing input file {media_file}, will "
                        f"continue batch-processing. Error was: {e}"
                    )
                else:
                    # raise the error so the program will exit
                    raise e

            logger.info(f"Normalized file written to {media_file.output_file}")

        if self.print_stats and self.stats:
            print(json.dumps(self.stats, indent=4))
