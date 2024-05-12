import logging
from datetime import datetime
import pytz
from pathlib import Path


PATH_LOG = Path('./log.log')

class Formatter(logging.Formatter):
    def converter(self, timestamp):
        return datetime.fromtimestamp(timestamp).astimezone()

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created).astimezone(tz=pytz.timezone('America/Santiago'))
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            s = dt.isoformat(timespec='seconds')
        return s


def get_logger(name, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    # console_handler = logging.StreamHandler()
    PATH_LOG.touch()
    console_handler = logging.FileHandler(PATH_LOG)
    console_handler.setFormatter(
        Formatter('%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s')
    )
    logger.addHandler(console_handler)
    logger.setLevel(level)
    return logger

logger = get_logger(__name__)
