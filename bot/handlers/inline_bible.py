from uuid import uuid4

from telegram import InlineQueryResultCachedVideo
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import InlineQueryHandler
from telegram.error import BadRequest

from bot.logs import get_logger
from bot.utils.decorators import vip
from bot.jw import BibleObject
from bot import exc
from bot.database import get


logger = get_logger(__name__)


def inline_bible(update: Update, _: CallbackContext) -> None:
    logger.info("%s", update.inline_query.query)
    user = get.user(update.effective_user.id)
    if update.inline_query.query:
        try:
            p = BibleObject.from_human(update.inline_query.query, user.bot_language_code)
        except exc.BaseBibleException:
            return
        files = get.files(user.sign_language_code, p.book.number, p.chapternumber, p.raw_verses, is_deprecated=False)
    else:
        files = get.files(user.sign_language_code, is_deprecated=False)
    results = []
    for file in files:
        title = f'{file.citation} - {user.sign_language.meps_symbol}'
        title += f' ({file.overlay_language_code})' if file.overlay_language_code else ''
        title += ' delogo' if file.delogo else ''
        results.append(
            InlineQueryResultCachedVideo(
                id=str(uuid4()),
                video_file_id=file.telegram_file_id,
                title=title,
                caption=title,
            )
        )
    try:
        update.inline_query.answer(results, auto_pagination=True, cache_time=5)
    except BadRequest:
        return

inline_handler = InlineQueryHandler(inline_bible)
