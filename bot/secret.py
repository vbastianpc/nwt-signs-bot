import os

from bot.logs import get_logger


logger = get_logger(__name__)

TOKEN = os.getenv('TOKEN_NWT')
ADMIN = int(os.getenv('USER_ID_ADMIN', 0))
BACKUP_CHANNEL_ID = int(os.getenv('BACKUP_CHANNEL_ID', 0))
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', 0))


if TOKEN is None:
    logger.warning('Missing environment variable TOKEN_NWT')
if ADMIN == 0:
    logger.warning('Missing environment variable USER_ID_ADMIN')
if BACKUP_CHANNEL_ID == 0:
    logger.warning('Missing environment variable BACKUP_CHANNEL_ID')
if LOG_CHANNEL_ID == 0:
    logger.warning('Missing environment variable LOG_CHANNEL_ID')
