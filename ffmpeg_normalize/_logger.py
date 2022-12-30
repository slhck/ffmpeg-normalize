from __future__ import annotations

import logging
import sys
from platform import system

from tqdm import tqdm

_global_log: logging.Logger | None = None


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


def setup_custom_logger() -> logging.Logger:
    """
    Grab or create the global logger
    """

    # \033[1;30m - black
    # \033[1;31m - red
    # \033[1;32m - green
    # \033[1;33m - yellow
    # \033[1;34m - blue
    # \033[1;35m - magenta
    # \033[1;36m - cyan
    # \033[1;37m - white

    global _global_log
    if _global_log is not None:
        return _global_log

    if system() not in ("Windows", "cli"):
        logging.addLevelName(logging.ERROR, "[1;31mERROR[1;0m")
        logging.addLevelName(logging.WARNING, "[1;33mWARNING[1;0m")
        logging.addLevelName(logging.INFO, "[1;34mINFO[1;0m")
        logging.addLevelName(logging.DEBUG, "[1;35mDEBUG[1;0m")

    logger = logging.Logger("ffmpeg_normalize")
    logger.setLevel(logging.WARNING)

    handler = TqdmLoggingHandler()
    handler.setFormatter(logging.Formatter(fmt="%(levelname)s: %(message)s"))
    logger.addHandler(handler)

    _global_log = logger

    return logger
