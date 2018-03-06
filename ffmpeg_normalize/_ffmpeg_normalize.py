import os
import json
from numbers import Number

from ._cmd_utils import get_ffmpeg_exe, ffmpeg_has_loudnorm
from ._media_file import MediaFile
from ._errors import FFmpegNormalizeError
from ._logger import setup_custom_logger

logger = setup_custom_logger('ffmpeg_normalize')

NORMALIZATION_TYPES = ['ebu', 'rms', 'peak']

def check_range(number, min_r, max_r, name=""):
    """
    Check if a number is within a given range
    """
    try:
        number = float(number)
        if number < min_r or number > max_r:
            raise FFmpegNormalizeError(
                "{} must be within [{},{}]".format(
                    name, min_r, max_r
                )
            )
        return number
        pass
    except Exception as e:
        raise e


class FFmpegNormalize():
    """
    ffmpeg-normalize class.
    """

    def __init__(
        self,
        normalization_type='ebu',
        target_level=-23.0,
        print_stats=False,
        # threshold=0.5,
        loudness_range_target=7.0,
        true_peak=-2.0,
        offset=0.0,
        dual_mono=False,
        audio_codec='pcm_s16le',
        audio_bitrate=None,
        sample_rate=None,
        video_codec='copy',
        video_disable=False,
        subtitle_disable=False,
        metadata_disable=False,
        extra_output_options=None,
        output_format=None,
        dry_run=False,
        debug=False
    ):
        self.ffmpeg_exe = get_ffmpeg_exe()
        self.has_loudnorm_capabilities = ffmpeg_has_loudnorm()

        self.normalization_type = normalization_type
        if not self.has_loudnorm_capabilities and self.normalization_type == 'ebu':
            raise FFmpegNormalizeError(
                "Your ffmpeg version does not support the 'loudnorm' EBU R128 filter. "
                "Please install ffmpeg v3.1 or above, or choose another normalization type."
            )

        if self.normalization_type == 'ebu':
            self.target_level = check_range(
                target_level, -70, -5, name='target_level'
            )
        else:
            self.target_level = check_range(
                target_level, -99, 0, name='target_level'
            )

        self.print_stats = print_stats

        # self.threshold = float(threshold)

        self.loudness_range_target = check_range(
            loudness_range_target, 1, 20, name='loudness_range_target'
        )
        self.true_peak = check_range(
            true_peak, -9, 0, name='true_peak'
        )
        self.offset = check_range(
            offset, -99, 99, name='offset'
        )

        self.dual_mono = True if dual_mono in ['true', True] else False
        self.audio_codec = audio_codec
        self.audio_bitrate = audio_bitrate
        self.sample_rate = int(sample_rate) if sample_rate is not None else None
        self.video_codec = video_codec
        self.video_disable = video_disable
        self.subtitle_disable = subtitle_disable
        self.metadata_disable = metadata_disable

        if extra_output_options:
            try:
                if isinstance(extra_output_options, str):
                    self.extra_output_options = json.loads(extra_output_options)
                elif isinstance(extra_output_options, list):
                    self.extra_output_options = extra_output_options
            except Exception as e:
                raise FFmpegNormalizeError(
                    "Could not parse extra_options: {}".format(e)
                )
        else:
            self.extra_output_options = {}

        self.output_format = output_format
        self.dry_run = dry_run
        self.debug = debug

        if normalization_type not in NORMALIZATION_TYPES:
            raise FFmpegNormalizeError(
                "Normalization type must be one of {}".format(NORMALIZATION_TYPES)
            )

        if self.target_level and not isinstance(self.target_level, Number):
            raise FFmpegNormalizeError("target_level must be a number")

        if self.loudness_range_target and not isinstance(self.loudness_range_target, Number):
            raise FFmpegNormalizeError("loudness_range_target must be a number")

        if self.true_peak and not isinstance(self.true_peak, Number):
            raise FFmpegNormalizeError("true_peak must be a number")

        if float(target_level) > 0:
            raise FFmpegNormalizeError("Target level must be below 0")

        self.media_files = []
        self.file_count = 0

    def add_media_file(self, input_file, output_file):
        """
        Add a media file to normalize

        Arguments:
            input_file {str} -- Path to input file
            output_file {str} -- Path to output file
        """
        if not os.path.exists(input_file):
            raise FFmpegNormalizeError("file " + input_file + " does not exist")

        mf = MediaFile(self, input_file, output_file)
        self.media_files.append(mf)

        self.file_count += 1

    def run_normalization(self):
        """
        Run the normalization procedures
        """
        for index, media_file in enumerate(self.media_files):
            logger.info("Normalizing file {} ({} of {})".format(media_file, index + 1, self.file_count))

            media_file.run_normalization()

            logger.info("Normalized file written to {}".format(media_file.output_file))

