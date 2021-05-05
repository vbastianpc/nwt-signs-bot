import logging
from uuid import uuid4
import json

from telegram import (
    InlineQueryResultCachedVideo,
    Update,
)
from telegram.ext import (
    CallbackContext,
    InlineQueryHandler,
)
from telegram.constants import MAX_INLINE_QUERY_RESULTS

from models import LocalData
from models import UserController
from utils import parse_bible_pattern, parse_chapter, BooknumNotFound, MultipleBooknumsFound
from utils.decorators import vip
from utils.secret import CHANNEL_ID
from utils.utils import parse_bookname, parse_verses


logger = logging.getLogger(__name__)

@vip
def inlineBibleReady(update: Update, context: CallbackContext) -> None:
    logger.info("%s", update.inline_query.query)
    try:
        booknums = [parse_bookname(update.inline_query.query)]
    except BooknumNotFound:
        booknums = [None]
    except MultipleBooknumsFound as e:
        booknums = e.booknums
    finally:
        chapter = parse_chapter(update.inline_query.query)
        verses = parse_verses(update.inline_query.query)
    uc = UserController(update.effective_user.id)
    results = []
    for booknum in booknums:
        db = LocalData(
            lang=uc.lang(),
            booknum=booknum,
            chapter=chapter,
            verses=verses,
            quality=uc.quality(),
        )
        results += [
            InlineQueryResultCachedVideo(
                id=str(uuid4()),
                video_file_id=file_id,
                title=f'{name} - {uc.lang()} {uc.quality()}',
            )
            for name, file_id in db.iter_smart()
        ]
        names = [name for name, file_id in db.iter_smart()]
        logger.info(f'{booknum=} {names=}')
    update.inline_query.answer(results, auto_pagination=True, cache_time=5)

inline_handler = InlineQueryHandler(inlineBibleReady)
