from uuid import uuid4

from telegram import InlineQueryResultCachedVideo
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import InlineQueryHandler

from bot.logs import get_logger
from bot.utils import parse_chapter, BooknumNotFound, MultipleBooknumsFound
from bot.utils.decorators import vip
from bot.jw.pubmedia import BaseBible
import bot.database.localdatabase as db


logger = get_logger(__name__)


@vip
def inlineBibleReady(update: Update, context: CallbackContext) -> None:
    logger.info("%s", update.inline_query.query)
    try:
        booknums = [] # type function herre
    except BooknumNotFound:
        booknums = [None]
    except MultipleBooknumsFound as e:
        booknums = e.booknums
    finally:
        chapter = parse_chapter(update.inline_query.query)
        # verses = parse_verses(update.inline_query.query)
    db_user = db.get_user(update.effective_user.id)
    citation = BaseBible().citation
    results = []
    for booknum in booknums:
        files = db.get_files() # TODO muestra las versiones antiguas también. quedarse solo con la última versión
        bookname = db.get_book(db_user.bot_language.code, booknum).name
        results += [
            InlineQueryResultCachedVideo(
                id=str(uuid4()),
                video_file_id=file.telegram_file_id,
                title=f'{citation(bookname, chapter, file.raw_verses)} - {db_user.signlanguage.meps_symbol}',
                caption=f'{citation(bookname, chapter, file.raw_verses)} - {db_user.signlanguage.meps_symbol}',
            )
            for file in files
        ]
    update.inline_query.answer(results, auto_pagination=True, cache_time=5)

inline_handler = InlineQueryHandler(inlineBibleReady)
