import logging
from platform import system
import io
from tqdm import tqdm
from multiprocessing import Lock

loggers = {}


# https://stackoverflow.com/questions/38543506/
class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super(TqdmLoggingHandler, self).__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.set_lock(Lock())
            tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

def setup_custom_logger(name):
    """
    Create a logger with a certain name and level
    """
    global loggers

    if loggers.get(name):
        return loggers.get(name)

    formatter = logging.Formatter(
        fmt='%(levelname)s: %(message)s'
    )

    # handler = logging.StreamHandler()
    handler = TqdmLoggingHandler()
    handler.setFormatter(formatter)

    # \033[1;30m - black
    # \033[1;31m - red
    # \033[1;32m - green
    # \033[1;33m - yellow
    # \033[1;34m - blue
    # \033[1;35m - magenta
    # \033[1;36m - cyan
    # \033[1;37m - white

    if system() not in ['Windows', 'cli']:
        logging.addLevelName(logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
        logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
        logging.addLevelName(logging.INFO, "\033[1;34m%s\033[1;0m" % logging.getLevelName(logging.INFO))
        logging.addLevelName(logging.DEBUG, "\033[1;35m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))

    logger = logging.getLogger(name)
    logger.setLevel(logging.WARNING)

    # if (logger.hasHandlers()):
    #     logger.handlers.clear()
    if logger.handlers:
        logger.handlers = []
    logger.addHandler(handler)
    loggers.update(dict(name=logger))

    return logger
