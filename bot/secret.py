import os
from dotenv import load_dotenv

from bot.logs import get_logger


logger = get_logger(__name__)

load_dotenv()
TOKEN = os.getenv('TOKEN_NWT')
ADMIN = int(os.getenv('USER_ID_ADMIN', 0))
LOG_GROUP_ID = int(os.getenv('LOG_GROUP_ID', 0))
TOPIC_BACKUP = int(os.getenv('TOPIC_BACKUP', 0))
TOPIC_ERROR = int(os.getenv('TOPIC_ERROR', 0))
TOPIC_WAITING = int(os.getenv('TOPIC_WAITING', 0))
TOPIC_USE = int(os.getenv('TOPIC_USE', 0))
URL_FUNCTION = os.getenv('URL_FUNCTION', '')

if TOKEN is None:
    logger.warning('Missing environment variable TOKEN_NWT')
if ADMIN == 0:
    logger.warning('Missing environment variable USER_ID_ADMIN')
if LOG_GROUP_ID == 0:
    logger.warning('Missing environment variable LOG_GROUP_ID')
if TOPIC_BACKUP == 0:
    logger.warning('Missing environment variable BACKUP_CHANNEL_ID')
if TOPIC_ERROR == 0:
    logger.warning('Missing environment variable TOPIC_ERROR')
if TOPIC_WAITING == 0:
    logger.warning('Missing environment variable TOPIC_WAITING')
if TOPIC_USE == 0:
    logger.warning('Missing environment variable TOPIC_USE')
