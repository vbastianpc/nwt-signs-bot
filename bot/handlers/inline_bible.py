from uuid import uuid4

from telegram import InlineQueryResultCachedVideo
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import InlineQueryHandler

from bot.logs import get_logger
from bot.utils.decorators import vip
from bot.jw.pubmedia import BibleObject
from bot import exc


logger = get_logger(__name__)


# @vip
# def inlineBibleReady(update: Update, context: CallbackContext) -> None:
#     logger.info("%s", update.inline_query.query)
#     try:
#         booknums = [] # type function herre
#     except exc.BookNumberNotExists:
#         booknums = [None]
#     finally:
#         chapter = parse_chapter(update.inline_query.query)
#         # verses = parse_verses(update.inline_query.query)
#    user = get.user(update.effective_user.id)
#     citation = BibleObject().citation
#     results = []
#     for booknum in booknums:
#         files = get.files() # TODO muestra las versiones antiguas también. quedarse solo con la última versión
#         bookname = get.book(user.bot_language.code, booknum).name
#         results += [
#             InlineQueryResultCachedVideo(
#                 id=str(uuid4()),
#                 video_file_id=file.telegram_file_id,
#                 title=f'{citation(bookname, chapter, file.raw_verses)} - {user.signlanguage.meps_symbol}',
#                 caption=f'{citation(bookname, chapter, file.raw_verses)} - {user.signlanguage.meps_symbol}',
#             )
#             for file in files
#         ]
#     update.inline_query.answer(results, auto_pagination=True, cache_time=5)

# inline_handler = InlineQueryHandler(inlineBibleReady)
