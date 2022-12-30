import logging
import sys

from ._logger import setup_custom_logger

logger = setup_custom_logger()


class FFmpegNormalizeError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        if logger.getEffectiveLevel() == logging.DEBUG:
            logger.error(f"{self.__class__.__name__}: {message}")
        else:
            logger.error(message)
            sys.exit(1)
