from dotenv import dotenv_values

from bot.logs import get_logger


logger = get_logger(__name__)

config = dotenv_values()

TOKEN = config['TOKEN_NWT']
ADMIN = int(config['USER_ID_ADMIN'])
LOG_GROUP_ID = int(config['LOG_GROUP_ID'])
TOPIC_BACKUP = int(config['TOPIC_BACKUP'])
TOPIC_ERROR = int(config['TOPIC_ERROR'])
TOPIC_WAITING = int(config['TOPIC_WAITING'])
TOPIC_USE = int(config['TOPIC_USE'])
URL_FUNCTION = config.get('URL_FUNCTION', '')
