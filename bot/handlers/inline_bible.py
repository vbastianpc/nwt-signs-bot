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
from utils import parse_bible_pattern
from utils.decorators import vip
from utils.secret import CHANNEL_ID


logger = logging.getLogger(__name__)

@vip
def inlineBibleReady(update: Update, context: CallbackContext) -> None:
    logger.info("%s", update.inline_query.query)
    booknum, chapter, verses = parse_bible_pattern(update.inline_query.query)
    uc = UserController(update.effective_user.id)
    db = LocalData(
        lang=uc.lang(),
        booknum=booknum,
        chapter=chapter,
        verses=verses,
        quality=uc.quality(),
    )
    results = [
        InlineQueryResultCachedVideo(
            id=str(uuid4()),
            video_file_id=file_id,
            title=f'{name} - {uc.lang()} {uc.quality()}',
        )
        for name, file_id in db.iter_smart()
    ]
    update.inline_query.answer(results, auto_pagination=True, cache_time=5)

inline_handler = InlineQueryHandler(inlineBibleReady)
