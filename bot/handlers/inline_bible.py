import logging
import os
from uuid import uuid4
import json
import re

from telegram import (
    InlineQueryResultCachedVideo,
    InlineQueryResultArticle,
    InputTextMessageContent,
    ParseMode,
    Update,
)
#from telegram.constants import MAX_INLINE_QUERY_RESULTS
from telegram.ext import (
    CallbackContext,
    InlineQueryHandler,
)
from telegram.constants import MAX_INLINE_QUERY_RESULTS

from jw_pubmedia import (
    get_filesize,
    get_jw_data,
    get_marker,
    get_url_file,
    is_available,
)
from local_jw import (
    download_video,
    get_entry_local_jw,
    get_local_jw,
    save_local_jw,
    split_video,
)
from utils import parse_bible_pattern
from decorators import vip
from users import get_user_quality, get_user_lang
from secret import CHANNEL_ID


logger = logging.getLogger(__name__)

def _s(pair):
    return int(pair[0])

@vip
def inlineBibleReady(update: Update, context: CallbackContext) -> None:
    logger.info("(%s) %s", update.effective_user.name, update.inline_query.query)
    ud = context.user_data
    logger.info("%s", update.inline_query.query)
    book_alias, q_booknum, q_chapter, q_verses = parse_bible_pattern(update.inline_query.query)
    logger.info("%s   %s   %s   %s", f'{book_alias=}', f'{q_booknum=}', f'{q_chapter=}', f'{q_verses=}')
    ud['bible'] = [q_booknum, q_chapter, q_verses]
    ud['lang'] = get_user_lang(update.inline_query.from_user.id)
    local_jw = get_local_jw()
    results = [
        InlineQueryResultCachedVideo(
            id=str(uuid4()),
            video_file_id=verse_info['file_id'],
            title=f'{verse_info["name"]} - {lang} {quality}',
        )
        for lang, booknums in local_jw.items() if lang == ud['lang']
        for booknum, qualities in sorted(booknums.items(), key=_s) if bool(True if q_booknum is None else booknum == q_booknum)
        for quality, chapters in qualities.items()
        for chapter, chapter_info in sorted(chapters.items(), key=_s) if bool(True if q_chapter is None else chapter == q_chapter)
        for verse, verse_info in sorted(chapter_info['verses'].items(), key=_s) if bool(True if not q_verses else verse in q_verses)
    ]
    if results:
        update.inline_query.answer(results, auto_pagination=True, cache_time=5)
    elif q_booknum and q_chapter and q_verses:
        inlineBibleCook(update, context)
    else:
        update.inline_query.answer([])


def inlineBibleCook(update: Update, context: CallbackContext) -> None:
    logger.info('')
    ud = context.user_data
    booknum, chapter, verses = ud['bible']
    verse = verses[0] if verses else None
    ud['quality'] = get_user_quality(update.inline_query.from_user.id)
    ud['jw'] = get_jw_data(booknum, lang=ud['lang'])

    if not is_available(ud['jw'], chapter, [verse], ud['lang'], ud['quality']):
        update.inline_query.answer([])
        return

    url = get_url_file(ud['jw'], chapter, ud['lang'], ud['quality'])
    db = get_entry_local_jw(booknum, chapter, ud['lang'], ud['quality'])
    logger.debug("%s", json.dumps(db, indent=2))
    server_filesize = get_filesize(
        ud['jw'], chapter, ud['lang'], ud['quality'])
    local_filesize = os.stat(
        db['file']).st_size if os.path.isfile(db['file']) else 0
    marker = get_marker(ud['jw'], chapter, verse, ud['lang'])

    if server_filesize != local_filesize:
        logger.info('Lo descargo porque no coinciden filesize')
        nwt_video_path = download_video(url)
        db['file'] = nwt_video_path
        db['filesize'] = os.stat(nwt_video_path).st_size
    else:
        logger.info('No lo descargo. Ya lo tengo.')

    versepath = split_video(db['file'], marker)
    msg = context.bot.send_video(
        CHANNEL_ID,
        open(versepath, 'rb'),
        caption=f'{update.inline_query.from_user.mention_markdown_v2()}',
        parse_mode=ParseMode.MARKDOWN_V2,
    )
    os.remove(versepath)
    db['verses'][verse] = {
        'file_id': msg.video.file_id, 'name': marker['label']}
    save_local_jw(db, booknum, chapter, ud['lang'], ud['quality'])
    results = [
        InlineQueryResultCachedVideo(
            id=str(uuid4()),
            video_file_id=msg.video.file_id,
            title=f"{db['verses'][verse]['name']} - {ud['lang']} {ud['quality']}",
        )
    ]
    update.inline_query.answer(results)
    logger.info('Finalizado. Guardando local')
    return


inline_handler = InlineQueryHandler(inlineBibleReady)
