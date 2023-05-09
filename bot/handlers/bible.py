from pathlib import Path
import re

from telegram import ChatAction
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CallbackQueryHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.error import TelegramError

from bot import MyCommand
from bot.secret import BACKUP_CHANNEL_ID
from bot.secret import LOG_CHANNEL_ID
from bot.logs import get_logger
from bot.jw.pubmedia import SignsBible
from bot.jw.epub import Epub
from bot.utils import video
from bot.database import localdatabase as db
from bot.database.schema import File
from bot.booknames.parse import parse_bible_citation
from bot.booknames.parse import BooknumNotFound, BibleCitationNotFound
from bot.handlers.start import all_fallback
from bot.handlers.settings import set_sign_language
from bot.handlers.settings import set_bot_language
from bot.utils import list_of_lists
from bot.utils import safechars
from bot.utils.decorators import vip
from bot.utils.decorators import forw
from bot.strings import TextGetter


logger = get_logger(__name__)

SELECTING_CHAPTERS, SELECTING_VERSES = 'C', 'V'


@vip
def parse_query(update: Update, context: CallbackContext) -> None:
    logger.info(f'{context.args=}, {update.message.text}')
    original_sign_language_code = db.get_user(update.effective_user.id).sign_language.code
    lines = update.message.text.splitlines()[:5]
    for line in lines:  # new feature: query 5 batch bible
        logger.info("line: %s", line)
        command = re.match(r'/(\w+)', line).group(1) if line.startswith('/') else ''
        query = re.search(f'{command}(.*)', line).group(1) if ' ' in line else None
        if command:
            language = db.get_language(code=command.lower())
            language2 = db.get_language(meps_symbol=command.upper())
            if language and language.is_sign_language:
                set_sign_language(update, context, sign_language_code=language.code)
            elif language and not language.is_sign_language:
                set_bot_language(update, context, bot_language_code=language.code)
            elif language2 and language2.is_sign_language:
                set_sign_language(update, context, sign_language_code=language2.code)
            elif language2 and not language2.is_sign_language:
                set_bot_language(update, context, bot_language_code=language2.code)
            if not query and len(lines) == 1:
                return
        if query:
            parse_query_bible(update, context, query)
    db.set_user(
        update.effective_user.id,
        sign_language_code=original_sign_language_code,
        last_active_datetime=db.dt_now()
    )


def parse_query_bible(update: Update, context: CallbackContext, query: str) -> None:
    logger.info("query: %s", query)
    db_user = db.get_user(update.effective_user.id)
    t = TextGetter(db_user.bot_language.code)
    try:
        book, chapternum, verses = parse_bible_citation(query, db_user.sign_language.code)
    except BooknumNotFound:
        update.message.reply_text(t.book_not_found.format(MyCommand.BOOKNAMES), parse_mode=ParseMode.MARKDOWN)
        return
    except BibleCitationNotFound:
        all_fallback(update, context)
        return

    context.user_data['jw'] = jw = SignsBible(db_user.sign_language.meps_symbol, book.number, chapternum, verses)
    context.user_data['msg'] = None
    if not jw.pubmedia_exists():
        update.message.reply_text(
            text=t.unavailable.format(book.name, db_user.sign_language.meps_symbol) +
            " " + t.optional_book.format(MyCommand.SIGNLANGUAGE),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if jw.chapternum and not jw.check_chapternumber():
        update.message.reply_text(
            text=t.unavailable.format(f'{jw.bookname} {jw.chapternum}',
                                      db_user.sign_language.meps_symbol) + ' ' + t.optional_chapter,
            parse_mode=ParseMode.MARKDOWN
        )
        show_chapters(update, context)
        return

    if jw.chapternum:
        context.bot.send_chat_action(update.effective_user.id, ChatAction.TYPING)
        db.manage_video_markers(jw)

    if not jw.chapternum:
        show_chapters(update, context)
    elif jw.verses:
        manage_verses(update, context)
    elif jw.chapternum:
        show_verses(update, context)
    return


def show_chapters(update: Update, context: CallbackContext):
    jw = context.user_data['jw']  # type: SignsBible
    t = TextGetter(db.get_user(update.effective_user.id).bot_language.code)
    buttons = list_of_lists(
        [InlineKeyboardButton(
            str(chapternum),
            callback_data=f'{SELECTING_CHAPTERS}|{jw.language_meps_symbol}|{jw.booknum}|{chapternum}',
        ) for chapternum in jw.get_all_chapternumber()],
        columns=8
    )
    db_user = db.get_user(update.effective_user.id)
    book = db.get_book(db_user.bot_language.code, jw.booknum)
    kwargs = {
        'chat_id': update.effective_chat.id,
        'text': f'🧏‍♂️ {jw.language_meps_symbol}\n📖 *{book.name}*\n{t.choose_chapter}',
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': ParseMode.MARKDOWN,
    }
    context.user_data['msg'] = context.bot.edit_message_text(
        **kwargs) if update.callback_query else context.bot.send_message(**kwargs)


@forw
def get_chapter(update: Update, context: CallbackContext):
    _, sign_language_meps_symbol, booknum, chapternum = update.callback_query.data.split('|')
    context.user_data['jw'] = SignsBible(sign_language_meps_symbol, booknum, chapternum)
    db.manage_video_markers(context.user_data['jw'])
    update.callback_query.answer()
    show_verses(update, context)


def show_verses(update: Update, context: CallbackContext):
    jw = context.user_data['jw']  # type: SignsBible
    bible_chapter = db.get_chapter(jw)
    t = TextGetter(db.get_user(update.effective_user.id).bot_language.code)

    buttons = list_of_lists(
        [InlineKeyboardButton(
            str(verse),
            callback_data=f'{SELECTING_VERSES}|{jw.language_meps_symbol}|{jw.booknum}|{jw.chapternum}|{verse}',
        ) for verse in (video_marker.versenum for video_marker in bible_chapter.video_markers)],
        columns=8
    )
    if update.callback_query:
        message_id = update.callback_query.message.message_id
    elif context.user_data.get('msg'):
        message_id = context.user_data['msg'].message_id
    else:
        message_id = None

    db_user = db.get_user(update.effective_user.id)
    book = db.get_book(db_user.bot_language.code, jw.booknum)
    kwargs = {
        'chat_id': update.effective_chat.id,
        'text': f'🧏‍♂️ {jw.language_meps_symbol}\n📖 *{book.chapter_display_title} {jw.chapternum}*\n{t.choose_verse}',
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': ParseMode.MARKDOWN,
    }
    if message_id:
        context.bot.edit_message_text(message_id=message_id, **kwargs)
    else:
        context.bot.send_message(**kwargs)


@forw
def get_verse(update: Update, context: CallbackContext):
    update.callback_query.answer()
    _, sign_lang_code, booknum, chapternum, verse = update.callback_query.data.split('|')
    context.user_data['jw'] = SignsBible(sign_lang_code, booknum, chapternum, verses=verse)
    context.user_data['msg'] = update.callback_query.message
    manage_verses(update, context)


def manage_verses(update: Update, context: CallbackContext):
    db_user = db.get_user(update.effective_user.id)
    jw = context.user_data['jw']  # type: SignsBible
    context.user_data['epub'] = Epub(db_user.bot_language.meps_symbol, jw.booknum, jw.chapternum, jw.verses)
    t = TextGetter(db_user.bot_language.code)
    logger.info('(%s) %s', update.effective_user.name, jw.citation())

    not_available = [v for v in jw.verses if v not in db.get_all_versenumbers(jw)]
    if not_available:
        v = not_available[0] if len(not_available) == 1 else ", ".join(map(str, not_available))
        update.effective_message.reply_text(
            text=t.unavailable.format(f'{jw.bookname} {jw.chapternum}:{v}',
                                      jw.language_meps_symbol) + ' ' + t.optional_verse,
            parse_mode=ParseMode.MARKDOWN
        )
        return show_verses(update, context)

    book = db.get_book(db_user.bot_language.code, jw.booknum)
    book_sign = db.get_book(db_user.sign_language.code, jw.booknum)
    with_overlay = db_user.overlay_language_id is not None and book.name != book_sign.name
    file = db.get_file(jw, db_user.overlay_language.code if with_overlay else None)
    if file:
        return send_by_fileid(update, context, file)

    if len(jw.verses) == 1:
        send_single_verse(update, context)
    else:
        send_concatenate_verses(update, context)
    logger.info('Success!')
    context.user_data.pop('jw', None)
    context.user_data.pop('msg', None)
    context.user_data.pop('epub', None)
    return


def send_by_fileid(update: Update, context: CallbackContext, file: File):
    logger.info('Sending by file_id')
    jw = context.user_data['jw']  # type: SignsBible
    if context.user_data.get('msg'):
        context.user_data.get('msg').delete()
    db_user = db.get_user(update.effective_user.id)
    book = db.get_book(db_user.bot_language.code, jw.booknum)
    bookname = book.standard_plural_bookname if len(jw.verses) > 1 else book.standard_singular_bookname
    citation = jw.citation(bookname)
    try:
        msgverse = context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=file.telegram_file_id,
            caption=(f'<a href="{jw.share_url()}">{citation}</a> - '
                     f'<a href="{jw.wol_discover()}">{jw.language_meps_symbol}</a>'),
            parse_mode=ParseMode.HTML
        )
        context.bot.send_chat_action(update.effective_user.id, ChatAction.TYPING)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f'<a href="{jw.share_url(is_sign_language=False)}">{citation}</a>\n' +
            context.user_data['epub'].verse_text(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    except TelegramError as e:
        # Nunca ha pasado
        logger.critical('Al parecer se ha eliminado de los servidores de Telegram file_id=%s', file.telegram_file_id)
        raise e

    else:
        db.add_file2user(file, update.effective_user.id)
        context.bot.copy_message(LOG_CHANNEL_ID, update.effective_user.id, msgverse.message_id)
    return


def send_single_verse(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    jw = context.user_data['jw']  # type: SignsBible
    msg = context.user_data.get('msg')
    t = TextGetter(db.get_user(update.effective_user.id).bot_language.code)
    db_user = db.get_user(update.effective_user.id)
    book = db.get_book(db_user.bot_language.code, jw.booknum)
    book_sign = db.get_book(db_user.sign_language.code, jw.booknum)
    with_overlay = db_user.overlay_language_id is not None and book.name != book_sign.name
    citation = f'{book.standard_singular_bookname} {jw.chapternum}:{jw.verses[0]}'
    logger.info("Splitting %s", citation)
    if msg:
        msg.edit_text(f'✂️ {t.trimming} *{citation}*', parse_mode=ParseMode.MARKDOWN)
    else:
        msg = message.reply_text(
            f'✂️ {t.trimming} *{citation}*',
            disable_notification=True,
            parse_mode=ParseMode.MARKDOWN
        )
    context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
    marker = db.get_videomarker(jw)
    versepath = video.split(
        marker,
        overlay_text=citation if with_overlay else None,
        script=db_user.bot_language.script
    )
    streams = video.show_streams(versepath)
    context.bot.send_chat_action(chat.id, ChatAction.UPLOAD_VIDEO)
    msg.edit_text(f'📦 {t.sending} *{citation}*', parse_mode=ParseMode.MARKDOWN)
    thumbnail = video.make_thumbnail(versepath)
    logger.info('%s', thumbnail)
    sign_book = db.get_book(db_user.sign_language.code, jw.booknum)
    sign_citation = jw.citation(sign_book.standard_singular_bookname)
    name = f'{safechars(sign_citation)} - {jw.language_meps_symbol}.mp4'
    msgverse = context.bot.send_video(
        chat_id=chat.id,
        video=versepath.read_bytes(),
        filename=name,
        # TODO no usar jw.share_url
        caption=(f'<a href="{jw.share_url()}">{citation}</a> - '
                 f'<a href="{jw.wol_discover()}">{jw.language_meps_symbol}</a>'),
        width=streams['width'],
        height=streams['height'],
        duration=round(float(streams['duration'])),
        timeout=120,
        thumb=thumbnail,
        parse_mode=ParseMode.HTML
    )
    file = db.add_file(msgverse.video, jw, db_user.overlay_language_id if with_overlay else None)
    db.add_file2user(file, update.effective_user.id)
    context.bot.send_chat_action(update.effective_user.id, ChatAction.TYPING)
    url = jw.share_url(is_sign_language=False, language_meps_symbol=db_user.bot_language.meps_symbol)
    context.bot.send_message(
        chat_id=chat.id,
        text=f'<a href="{url}">{citation}</a>\n' + context.user_data['epub'].verse_text(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    thumbnail.unlink()
    context.bot.copy_message(LOG_CHANNEL_ID, chat.id, msgverse.message_id)
    msg.delete()
    versepath.unlink()


def send_concatenate_verses(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    db_user = db.get_user(update.effective_user.id)
    jw = context.user_data['jw']  # type: SignsBible
    book = db.get_book(db_user.bot_language.code, jw.booknum)
    book_sign = db.get_book(db_user.sign_language.code, jw.booknum)
    with_overlay = db_user.overlay_language_id is not None and book.name != book_sign.name
    verses = jw.verses
    msg = context.user_data.get('msg')
    t = TextGetter(db.get_user(update.effective_user.id).bot_language.code)

    paths_to_concatenate = []
    new = []
    for verse in jw.verses:
        jw.verses = verse
        file = db.get_file(jw, db_user.overlay_language.code if with_overlay else None)
        citation = f'{book.standard_singular_bookname} {jw.chapternum}:{verse}'
        if file:
            logger.info('Downloading verse %s from telegram servers', citation)
            text = f'⬇️ {t.downloading} *{citation}*'
            if msg:
                msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)
            else:
                msg = message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            versepath = Path(f'{file.id}.mp4')  # cualquier nombre sirve
            context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
            context.bot.get_file(file.telegram_file_id, timeout=120).download(custom_path=versepath)
            paths_to_concatenate.append(versepath)
        else:
            logger.info("Splitting %s", citation)
            if msg:
                msg.edit_text(f'✂️ {t.trimming} *{citation}*', parse_mode=ParseMode.MARKDOWN)
            else:
                msg = message.reply_text(f'✂️ {t.trimming} *{citation}*', parse_mode=ParseMode.MARKDOWN)
            context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
            marker = db.get_videomarker(jw)
            versepath = video.split(
                marker,
                overlay_text=citation if with_overlay else None,
                script=db_user.bot_language.script
            )
            paths_to_concatenate.append(versepath)
            new.append((verse, versepath))
    jw.verses = verses
    book_sign = db.get_book(db_user.sign_language.code, jw.booknum)
    sign_citation = jw.citation(book_sign.standard_plural_bookname)
    logger.info('Concatenating video %s', citation)
    msg.edit_text(f'🎥 {t.splicing}', parse_mode=ParseMode.MARKDOWN)
    finalpath = video.concatenate(
        inputvideos=paths_to_concatenate,
        outname=f'{safechars(sign_citation)} - {jw.language_meps_symbol}',
        title_chapters=[jw.citation(book_sign.standard_singular_bookname, verses=verse) for verse in jw.verses],
        title=sign_citation,
    )
    logger.info('Sending concatenated video %s', finalpath)
    citation = jw.citation(book.standard_plural_bookname)
    msg.edit_text(f'📦 {t.sending} *{citation}*', parse_mode=ParseMode.MARKDOWN)
    context.bot.send_chat_action(chat.id, ChatAction.UPLOAD_VIDEO)
    stream = video.show_streams(finalpath)
    thumbnail = video.make_thumbnail(finalpath)
    msgverse = context.bot.send_video(
        chat_id=chat.id,
        video=finalpath.read_bytes(),
        filename=safechars(finalpath.name),
        # TODO no usar metodo jw.share_url
        caption=(f'<a href="{jw.share_url()}">{citation}</a> - '
                 f'<a href="{jw.wol_discover()}">{jw.language_meps_symbol}</a>'),
        width=stream['width'],
        height=stream['height'],
        duration=round(float(stream['duration'])),
        timeout=120,
        thumb=thumbnail,
        parse_mode=ParseMode.HTML
    )
    context.bot.send_chat_action(update.effective_user.id, ChatAction.TYPING)
    context.bot.send_message(
        chat_id=chat.id,
        text=f'<a href="{jw.share_url(is_sign_language=False)}">{citation}</a>\n' +
        context.user_data['epub'].verse_text(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    thumbnail.unlink()
    msg.delete()
    context.bot.copy_message(LOG_CHANNEL_ID, chat.id, msgverse.message_id)

    file = db.add_file(msgverse.video, jw, db_user.overlay_language_id if with_overlay else None)
    db.add_file2user(file, update.effective_user.id)
    for verse, versepath in new:
        stream = video.show_streams(versepath)
        thumbnail = video.make_thumbnail(versepath)
        jw.verses = verse
        msgverse = context.bot.send_video(
            chat_id=BACKUP_CHANNEL_ID,
            video=versepath.read_bytes(),
            filename=f'{safechars(versepath.stem)} - {jw.language_meps_symbol}.mp4',
            caption=(f'<a href="{jw.share_url(verse)}">{jw.citation(book.standard_singular_bookname)}</a> - '
                     f'<a href="{jw.wol_discover()}">{jw.language_meps_symbol}</a>'),
            parse_mode=ParseMode.HTML,
            width=stream['width'],
            height=stream['height'],
            duration=round(float(stream['duration'])),
            timeout=120,
            thumb=thumbnail,
        )
        thumbnail.unlink()
        file = db.add_file(msgverse.video, jw, db_user.overlay_language_id if with_overlay else None)
        db.add_file2user(file, update.effective_user.id)
    for versepath in paths_to_concatenate + [finalpath]:
        versepath.unlink()


chapter_handler = CallbackQueryHandler(get_chapter, pattern=SELECTING_CHAPTERS)
verse_handler = CallbackQueryHandler(get_verse, pattern=SELECTING_VERSES)
parse_bible_handler = MessageHandler(Filters.text, parse_query)
