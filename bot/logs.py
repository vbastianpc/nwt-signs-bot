import logging
from datetime import datetime
import pytz



class Formatter(logging.Formatter):
    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp)
        tzinfo = pytz.timezone('UTC')
        return tzinfo.localize(dt)

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created).astimezone(tz=pytz.timezone('America/Santiago'))
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            s = dt.isoformat(timespec='seconds')
        return s


def get_logger(name, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        Formatter('%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s')
    )
    logger.addHandler(console_handler)
    logger.setLevel(level)
    return logger

logger = get_logger(__name__)