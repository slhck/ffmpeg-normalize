import os
from numbers import Number
from tqdm import tqdm

from ._cmd_utils import get_ffmpeg_exe, ffmpeg_has_loudnorm
from ._media_file import MediaFile
from ._errors import FFmpegNormalizeError
from ._logger import setup_custom_logger

logger = setup_custom_logger('ffmpeg_normalize')

NORMALIZATION_TYPES = ['ebu', 'rms', 'peak']
PCM_INCOMPATIBLE_FORMATS = ['mp4', 'mp3', 'ogg', 'webm']
PCM_INCOMPATIBLE_EXTS = ['mp4', 'm4a', 'mp3', 'ogg', 'webm']

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
        audio_quality=None,
        sample_rate=None,
        keep_original_audio=False,
        video_codec='copy',
        video_disable=False,
        subtitle_disable=False,
        metadata_disable=False,
        chapters_disable=False,
        extra_output_options=None,
        output_format=None,
        dry_run=False,
        debug=False,
        progress=False,
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

        if audio_quality is not None:
            self.audio_quality = check_range(audio_quality, 0, 9, "audio_quality")

        if self.audio_bitrate is not None and self.audio_quality is not None:
            raise FFmpegNormalizeError("You can't set audio-bitrate and autio-quality at same time")

        self.sample_rate = int(sample_rate) if sample_rate is not None else None
        self.keep_original_audio = keep_original_audio
        self.video_codec = video_codec
        self.video_disable = video_disable
        self.subtitle_disable = subtitle_disable
        self.metadata_disable = metadata_disable
        self.chapters_disable = chapters_disable

        self.extra_output_options = extra_output_options

        self.output_format = output_format
        self.dry_run = dry_run
        self.debug = debug
        self.progress = progress

        if self.output_format and (self.audio_codec is None or 'pcm' in self.audio_codec) and \
                self.output_format in PCM_INCOMPATIBLE_FORMATS:
            raise FFmpegNormalizeError(
                "Output format {} does not support PCM audio. Please choose a suitable audio codec with the -c:a option.".format(self.output_format)
            )

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

        ext = os.path.splitext(output_file)[1][1:]
        if (self.audio_codec is None or 'pcm' in self.audio_codec) and ext in PCM_INCOMPATIBLE_EXTS:
            raise FFmpegNormalizeError(
                "Output extension {} does not support PCM audio. Please choose a suitable audio codec with the -c:a option.".format(ext)
            )

        mf = MediaFile(self, input_file, output_file)
        self.media_files.append(mf)

        self.file_count += 1

    def run_normalization(self):
        """
        Run the normalization procedures
        """
        for index, media_file in enumerate(
                tqdm(
                    self.media_files,
                    desc="File",
                    disable=not self.progress,
                    position=0
                )):
            logger.info("Normalizing file {} ({} of {})".format(media_file, index + 1, self.file_count))

            media_file.run_normalization()

            logger.info("Normalized file written to {}".format(media_file.output_file))
