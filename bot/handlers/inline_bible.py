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

from models import LocalData
from models import UserController
from utils import parse_chapter, BooknumNotFound, MultipleBooknumsFound
from utils.decorators import vip
from utils.utils import parse_booknum, parse_verses


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
    uc = UserController(update.effective_user.id)
    results = []
    logger.info(f'{booknums} {chapter} {verses}')
    for booknum in booknums:
        db = LocalData(
            code_lang=uc.get_lang(),
            booknum=booknum,
            chapter=chapter,
            verses=verses,
            quality=uc.get_quality(),
        )
        results += [
            InlineQueryResultCachedVideo(
                id=str(uuid4()),
                video_file_id=file_id,
                title=f'{name} - {uc.get_lang()} {uc.get_quality()}',
            )
            for name, file_id in db.iter_smart()
        ]
    update.inline_query.answer(results, auto_pagination=True, cache_time=5)

inline_handler = InlineQueryHandler(inlineBibleReady)
