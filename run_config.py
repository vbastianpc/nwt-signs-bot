from telegram import Bot

from bot.logs import get_logger
from bot.secret import ADMIN
from bot.secret import TOKEN
from bot.utils import dt_now
from bot.database import report
from bot.database import localdatabase as db
from bot.database.schemedb import Language
from bot.database import SESSION
from bot.jw.language import JWLanguage
from bot.utils.fonts import fetch_fonts, download_fonts

logger = get_logger(__name__)


if __name__ == '__main__':
    logger.info('Starting configuration...')
    # db.fetch_languages()
    # logger.info(f'There are {report.count_languages()} languages stored in the database')
    # db.fetch_bible_editions()
    # logger.info(f'There are {report.count_bible_editions()} bible editions stored in the database')
    # for language_meps_symbol in ['E', 'S', 'VT', 'SCH', 'ASL', 'BVL', 'SLV']:
    #     db.fetch_bible_books(language_meps_symbol)
    # bot = Bot(TOKEN)
    # member = bot.get_chat_member(chat_id=ADMIN, user_id=ADMIN)
    # db.set_user(
    #     ADMIN,
    #     full_name=member.user.full_name,
    #     bot_language=db.get_language(code=member.user.language_code),
    #     brother=True,
    #     added_datetime=dt_now()
    # )
    # logger.info(f'User {member.user.full_name} added to database. Configuration succesful!')
    
    fetch_fonts()
    download_fonts()
    logger.info('done')
