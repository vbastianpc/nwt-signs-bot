import logging
from uuid import uuid4

from telegram import InlineQueryResultCachedVideo
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import InlineQueryHandler

from bot.utils import parse_chapter, BooknumNotFound, MultipleBooknumsFound
from bot.utils.decorators import vip
from bot.utils.utils import parse_booknum, parse_verses
import bot.database.localdatabase as db


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


@vip
def inlineBibleReady(update: Update, context: CallbackContext) -> None:
    logger.info("%s", update.inline_query.query)
    try:
        booknums = [parse_booknum(update.inline_query.query)]
    except BooknumNotFound:
        booknums = [None]
    except MultipleBooknumsFound as e:
        booknums = e.booknums
    finally:
        chapter = parse_chapter(update.inline_query.query)
        verses = parse_verses(update.inline_query.query)
    db_user = db.get_user(update.effective_user.id)
    results = []
    logger.info(f'{booknums!r} {chapter!r} {verses!r}')
    for booknum in booknums:
        sent_verses = db.query_sent_verses(
            lang_code=db_user.signlanguage.code,
            booknum=booknum,
            chapter=chapter,
            raw_verses=' '.join(verses),
        )
        results += [
            InlineQueryResultCachedVideo(
                id=str(uuid4()),
                video_file_id=sent_verse.telegram_file_id,
                title=f'{sent_verse.citation} - {db_user.signlanguage.code}',
            )
            for sent_verse in sent_verses
        ]
    update.inline_query.answer(results, auto_pagination=True, cache_time=5)

inline_handler = InlineQueryHandler(inlineBibleReady)
