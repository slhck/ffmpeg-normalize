from __future__ import annotations

import argparse
import logging
import sys

import colorlog
from tqdm import tqdm

from ffmpeg_normalize import __module_name__ as LOGGER_NAME


# https://stackoverflow.com/questions/38543506/
class TqdmLoggingHandler(logging.StreamHandler):
    def __init__(self) -> None:
        super().__init__(sys.stderr)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            set_mp_lock()
            tqdm.write(msg, file=sys.stderr)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


def set_mp_lock() -> None:
    try:
        from multiprocessing import Lock

        tqdm.set_lock(Lock())
    except (ImportError, OSError):
        # Some python environments do not support multiprocessing
        # See: https://github.com/slhck/ffmpeg-normalize/issues/156
        pass


def setup_cli_logger(arguments: argparse.Namespace) -> None:
    """Configurs the CLI logger.

    Args:
        arguments (argparse.Namespace): The CLI arguments.
    """

    logger = colorlog.getLogger(LOGGER_NAME)

    handler = TqdmLoggingHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)s: %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )
    logger.addHandler(handler)

    logger.setLevel(logging.WARNING)

    if arguments.quiet:
        logger.setLevel(logging.ERROR)
    elif arguments.debug:
        logger.setLevel(logging.DEBUG)
    elif arguments.verbose:
        logger.setLevel(logging.INFO)
