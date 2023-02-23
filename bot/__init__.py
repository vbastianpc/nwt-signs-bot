import os
import logging
from datetime import datetime
import pytz


class MyCommand:
    START = 'start'
    SIGNLANGUAGE = 'signlanguage'
    BOTLANGUAGE = 'botlanguage'
    INLINE = 'inline'
    FEEDBACK = 'feedback'
    HELP = 'help'
    BOOKNAMES = 'booknames'
    DEPR_SIGNLANGUAGE = 'lang'
    CANCEL = 'cancel'
    OK = 'ok'
    SETTINGS = 'settings'

class AdminCommand:
    ADD = 'add'
    BAN = 'ban'
    USERS = 'users'
    SETCOMMANDS = 'setcommands'
    NOTIFY = 'notify'
    BACKUP = 'backup'
    LOGS = 'logs'
    LOGFILE = 'logfile'
    STATS = 'stats'
    TEST = 'test'
    RESET_CHAPTER = 'reset_chapter'

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
        Formatter('%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(console_handler)
    logger.setLevel(level)
    return logger

logger = get_logger(__name__)


TOKEN = os.getenv('TOKEN_NWT')
ADMIN = int(os.getenv('USER_ID_ADMIN', 0))
CHANNEL_ID = int(os.getenv('CHANNEL_ID', 0))


if TOKEN is None:
    logger.warning('Missing environment variable TOKEN_NWT')
if ADMIN == 0:
    logger.warning('Missing environment variable USER_ID_ADMIN')
if CHANNEL_ID == 0:
    logger.warning('Missing environment variable CHANNEL_ID')
