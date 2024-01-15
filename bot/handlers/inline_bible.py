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
    user = get.user(update.effective_user.id)
    if (query := update.inline_query.query):
        language = get.parse_language(query.split()[0][1:]) if query.startswith('/') else None
        citation = ' '.join(query.split()[1:]) if query.startswith('/') else query
        try:
            p = BibleObject.from_human(citation, user.bot_language_code)
        except exc.BaseBibleException as e:
            if language:
                files = get.files(language.code, is_deprecated=False, limit=200)
            else:
                logger.error(f'{query!r}', exc_info=e)
                return
        else:
            files = get.files(language.code if language else None,
                              p.book.number,
                              p.chapternumber,
                              p.raw_verses,
                              is_deprecated=False,
                              limit=200)
    else:
        files = get.files(is_deprecated=False, limit=200)
    results = []
    logger.info(f'{query=} {len(files)=} first={files[0] if files else None}')

    for file in files:
        p = BiblePassage.from_num(
            language_code=file.language.code,
            booknumber=file.book.number,
            chapternumber=file.chapter.number,
            verses=file.raw_verses.split(),
            include_omitted=True,
        )
        logger.info(f'{file.language.code} {p.citation}')
        description = '[OLD] ' if file.is_deprecated else ''
        description += '+ ' if not file.delogo and file.overlay_language_code else ''
        description += file.overlay_language.name if file.overlay_language_code else ''
        results.append(
            InlineQueryResultCachedVideo(
                id=str(uuid4()),
                video_file_id=file.telegram_file_id,
                title=f'{file.language.meps_symbol} - {file.citation}',
                caption=f'<a href="{p.url_share_jw()}">{p.citation}</a> - '
                        f'<a href="{p.url_bible_wol_discover}">{p.language.meps_symbol}</a>',
                description=description,
                parse_mode=ParseMode.HTML
            )
        )
    try:
        update.inline_query.answer(results, auto_pagination=True, cache_time=10)
    except BadRequest as e:
        raise e

inline_handler = InlineQueryHandler(inline_bible)
