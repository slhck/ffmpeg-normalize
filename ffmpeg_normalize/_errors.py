import sys
import logging
from ._logger import setup_custom_logger

logger = setup_custom_logger("ffmpeg_normalize")


class FFmpegNormalizeError(Exception):
    def __init__(self, message):
        super().__init__(message)
        if logger.getEffectiveLevel() == logging.DEBUG:
            logger.error(f"{self.__class__.__name__}: {message}")
        else:
            logger.error(message)
            sys.exit(1)
