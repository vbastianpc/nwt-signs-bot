from uuid import uuid4

from telegram import InlineQueryResultCachedVideo
from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram.ext import InlineQueryHandler
from telegram.error import BadRequest

from bot.logs import get_logger
from bot.jw import BibleObject, BiblePassage
from bot import exc
from bot.database import get


logger = get_logger(__name__)


def inline_bible(update: Update, _: CallbackContext) -> None:
    logger.info("%s", update.inline_query.query)
    user = get.user(update.effective_user.id)
    if (query := update.inline_query.query):
        language = get.parse_language(query.split()[0][1:]) if query.startswith('/') else None
        try:
            p = BibleObject.from_human(query, user.bot_language_code)
        except exc.BaseBibleException:
            return
        files = get.files(language.code if language else None,
                          p.book.number,
                          p.chapternumber,
                          p.raw_verses,
                          limit=200)
    else:
        files = get.files()
    results = []

    for file in files:
        p = BiblePassage.from_num(file.language.code, file.book.number, file.chapter.number, file.raw_verses)
        description = '[OLD] ' if file.is_deprecated else ''
        description += f'({file.overlay_language.name}) overlay ' if file.overlay_language_code else ''
        description += 'delogo' if file.delogo else ''
        results.append(
            InlineQueryResultCachedVideo(
                id=str(uuid4()),
                video_file_id=file.telegram_file_id,
                title=f'{file.citation} - {file.language.meps_symbol}',
                caption=f'<a href="{p.url_share_jw()}">{p.citation}</a> - '
                        f'<a href="{p.url_bible_wol_discover}">{p.language.meps_symbol}</a>',
                description=description,
                parse_mode=ParseMode.HTML
            )
        )
    try:
        update.inline_query.answer(results, auto_pagination=True, cache_time=5)
    except BadRequest:
        return

inline_handler = InlineQueryHandler(inline_bible)
