import importlib.metadata

from ._errors import FFmpegNormalizeError
from ._ffmpeg_normalize import FFmpegNormalize
from ._media_file import MediaFile
from ._streams import AudioStream, MediaStream, SubtitleStream, VideoStream

__version__ = importlib.metadata.version("ffmpeg-normalize")

__module_name__ = "ffmpeg_normalize"

__all__ = [
    "FFmpegNormalize",
    "FFmpegNormalizeError",
    "MediaFile",
    "AudioStream",
    "VideoStream",
    "SubtitleStream",
    "MediaStream",
    "__version__",
]
