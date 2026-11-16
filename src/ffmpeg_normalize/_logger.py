from __future__ import annotations

import argparse
import logging

from rich.text import Text

from ffmpeg_normalize import __module_name__ as LOGGER_NAME

from ._console import get_console


class RichLogHandler(logging.Handler):
    """
    Log handler that prints `LEVEL: message` lines to the shared rich console.

    Printing through the console keeps messages above any live progress bars.
    The plain `LEVEL: message` layout is kept so that output stays easy to
    grep when stderr is redirected; colors are only used on terminals.
    Messages are never wrapped, and rich markup in messages is not interpreted.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            level = record.levelname
            line = Text()
            line.append(f"{level}:", style=f"log.{level.lower()}")
            line.append(" ")
            if record.levelno >= logging.ERROR:
                line.append(message, style="log.error")
            elif record.levelno == logging.DEBUG:
                line.append(message, style="dim")
            else:
                line.append(message)
            get_console().print(line, soft_wrap=True)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


def setup_cli_logger(arguments: argparse.Namespace) -> None:
    """Configures the CLI logger.

    Args:
        arguments (argparse.Namespace): The CLI arguments.
    """

    logger = logging.getLogger(LOGGER_NAME)

    handler = RichLogHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    logger.setLevel(logging.WARNING)

    if arguments.quiet:
        logger.setLevel(logging.ERROR)
    elif arguments.debug:
        logger.setLevel(logging.DEBUG)
    elif arguments.verbose:
        logger.setLevel(logging.INFO)
