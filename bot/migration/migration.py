from datetime import datetime
from time import sleep

from telegram import Bot
from telegram import ChatAction
from telegram.error import Unauthorized

from bot.migration.old_schema import old_session
from bot.migration.old_schema import Language as oLanguage
from bot.migration.old_schema import BibleBook as oBibleBook
from bot.migration.old_schema import BibleChapter as oBibleChapter
from bot.migration.old_schema import VideoMarker as oVideoMarker
from bot.migration.old_schema import SentVerse as oSentVerse
from bot.migration.old_schema import User as oUser
from bot.migration.old_schema import SentVerseUser as oSentVerseUser
from bot.migration.old_schema import BookNamesAbbreviation as oBookNamesAbbreviation

from bot.database import session
from bot.database.schema import Bible
from bot.database.schema import Language
from bot.database.schema import Edition
from bot.database.schema import Book
from bot.database.schema import Chapter
from bot.database.schema import VideoMarker
from bot.database.schema import File
from bot.database.schema import User
from bot.database.schema import File2User
from bot.database import get
from bot.utils.browser import browser
from bot.utils import how_to_say, dt_now
from bot.logs import get_logger
from bot.secret import TOKEN

logger = get_logger(__name__)

bot = Bot(TOKEN)


def migrate_users():
    ousers: list[oUser] = old_session.query(oUser).all()
    users = []
    for ouser in ousers:
        bot_language = get.language(code=ouser.bot_lang)
        if ouser.sign_language_id is not None:
            sl_code = old_session.query(oLanguage).where(oLanguage.id == ouser.sign_language_id).one().locale
            sl_id = get.language(code=sl_code).id
        else:
            logger.info(f'{ouser.full_name} has no sign language. User discarded.')
            continue
        if ouser.status in [-1, 0]:
            continue
        try:
            bot.send_chat_action(ouser.telegram_user_id, ChatAction.TYPING)
        except Unauthorized:
            logger.info(f'{ouser.full_name} has blocked this bot. User discarded')
            continue
        else:
            member = bot.get_chat_member(chat_id=ouser.telegram_user_id, user_id=ouser.telegram_user_id)
        users.append(User(
            telegram_user_id=ouser.telegram_user_id,
            first_name=member.user.first_name,
            last_name=member.user.last_name or '',
            user_name=member.user.username,
            is_premium=member.user.is_premium,
            sign_language_id=sl_id,
            bot_language_id=bot_language.id,
            overlay_language_id=None,
            sign_language_name=how_to_say(sl_code, bot_language.code),
            status=ouser.status,
            added_datetime=datetime.fromisoformat(ouser.added_datetime) if ouser.added_datetime else dt_now(),
            last_active_datetime=None
        ))
    session.add_all(users)
    session.commit()


def migrate_files():
    sent_verses: list[oSentVerse] = old_session.query(oSentVerse).limit(50).all()
    for sent_verse in sent_verses:
        print(sent_verse.id, sent_verse.parent.booknum, sent_verse.parent.bookname, sent_verse.parent.parent.locale)




if __name__ == '__main__':
    migrate_files()