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
from bot.database import report
from bot.secret import BACKUP_CHANNEL_ID
from bot.secret import LOG_CHANNEL_ID
from bot.logs import get_logger
from bot.jw import BiblePassage
from bot.jw import BibleEpub
from bot.utils import video
from bot.utils import dt_now
from bot.database import get
from bot.database import fetch
from bot.database import add
from bot import exc
from bot.database.schema import File
from bot.handlers.settings import set_sign_language
from bot.handlers.settings import set_bot_language
from bot.utils import list_of_lists
from bot.utils import safechars
from bot.utils.decorators import vip
from bot.utils.decorators import forw
from bot.strings import TextTranslator


logger = get_logger(__name__)

SELECT_BOOK, SELECT_CHAPTER, SELECT_VERSE = 'B', 'C', 'V'
HTML = ParseMode.HTML

@vip
def parse_query(update: Update, context: CallbackContext) -> None:
    logger.info(f'{context.args=}, {update.effective_message.text}')
    orig_sl_code = get.user(update.effective_user.id).sign_language.code

    def command(string: str) -> str:
        return re.match(r'/([\w-]+)', string).group(1) if string.startswith('/') else ''
    def query(string: str) -> str:
        return string if not string.startswith('/') else ' '.join(string.split()[1:])

    lines = update.effective_message.text.splitlines()[:5]
    for text in lines:
        if not command(text):
            parse_query_bible(update, context, text)
        else:
            language = get.parse_language(command(text))
            if not language:
                user = get.user(update.effective_user.id)
                tt = TextTranslator(user.bot_language_code)
                update.effective_message.reply_text(tt.not_language(command(text)), parse_mode=HTML)
            if query(text):
                if language.is_sign_language is True:
                    add.or_update_user(update.effective_user.id, sign_language_code=language.code)
                    parse_query_bible(update, context, query(text))
            elif len(lines) == 1 and language and not query(text):
                # change language permanent
                if language.is_sign_language is True:
                    set_sign_language(update, context, sign_language_code=language.code)
                elif language.is_sign_language is False:
                    set_bot_language(update, context, bot_language_code=language.code)
                return
            elif language and not query(text):
                add.or_update_user(update.effective_user.id, sign_language_code=language.code)

    add.or_update_user(
        update.effective_user.id,
        sign_language_code=orig_sl_code,
        last_active_datetime=dt_now()
    )


def parse_query_bible(update: Update, context: CallbackContext, query: str) -> None:
    logger.info("query: %s", query)
    user = get.user(update.effective_user.id)
    tt = TextTranslator(user.bot_language.code)
    try:
        passage = BiblePassage.from_human(query, user.bot_language.code)
    except exc.BibleCitationNotFound:
        update.effective_message.reply_text(
            f'<b>{query}:</b> ' + tt.fallback(MyCommand.HELP, report.count_signlanguage()),
            parse_mode=ParseMode.HTML)
        return
    except exc.BookNameNotFound as e:
        update.effective_message.reply_text(tt.book_not_found(e.book_like), parse_mode=HTML)
        return
    except exc.MissingChapterNumber as e:
        update.effective_message.reply_text(tt.missing_chapter(e.bookname), parse_mode=HTML)
        return
    except exc.ChapterNotExists as e:
        update.effective_message.reply_text(tt.chapter_not_exists(e.bookname, e.chapternum, e.last_chapternum),
                                  parse_mode=HTML)
        return
    except exc.VerseNotExists as e:
        d = (e.bookname, e.chapternum, e.wrong_verses, e.last_versenum, e.count_wrong)
        update.effective_message.reply_text(tt.verse_not_exists(*d) if e.count_wrong == 1 else tt.verses_not_exists(*d),
                                  parse_mode=HTML)
        return
    except exc.VerseOmitted as e:
        update.effective_message.reply_text(tt.is_omitted(e.citation), parse_mode=HTML)
        return
    try:
        passage.set_language(user.sign_language.code)
    except exc.BookNameNotFound:
        fetch.books(language_code=user.sign_language.code)
        passage.set_language(user.sign_language.code)
    context.user_data['msg'] = None
    if fetch.need_chapter_and_videomarks(passage.book):
        try:
            update.message.reply_chat_action(ChatAction.TYPING)
            fetch.chapters_and_videomarkers(passage.book)
        except exc.PubmediaNotExists:
            passage.set_language(user.bot_language.code)
            update.effective_message.reply_text(text=tt.that_book_no(passage.book.name, user.sign_language_name),
                                                parse_mode=HTML)
            show_books(update, context, passage.set_language(user.sign_language.code))
            return
        else:
            passage.refresh()

    if passage.chapternumber and not passage.chapter:
        p = BiblePassage.from_num(user.bot_language_code, passage.book.number)
        update.effective_message.reply_text(tt.that_chapter_no(p.book.name, user.sign_language_name) + " " +
                                            tt.but_these_chapters, parse_mode=HTML)
        show_chapters(update, context, passage)
        return

    if passage.verses:
        if fetch.need_ffmpeg(passage.chapter) is True:
            update.effective_message.reply_chat_action(ChatAction.TYPING)
            m = update.effective_message.reply_text('⚡️ ' + tt.fetching_videomarkers)
            fetch.videomarkers_by_ffmpeg(passage.chapter)
            passage.refresh()
            m.delete()
        unavailable_verses = get.unavailable_verses(passage.chapter, passage.verses)
        if unavailable_verses:
            passage.set_language(user.bot_language.code)
            update.effective_message.reply_text(
                tt.that_verse_no(BiblePassage(passage.book, passage.chapternumber, unavailable_verses).citation,
                                 user.sign_language.vernacular) + " " +
                tt.but_these_verses, parse_mode=HTML)
            passage.set_language(user.sign_language.code)
            show_verses(update, context, passage)
            return
        else:
            manage_verses(update, context, passage)
    elif passage.chapternumber:
        show_verses(update, context, passage)
    else:
        show_chapters(update, context, passage)
    return


def show_books(update: Update, context: CallbackContext, p: BiblePassage) -> None:
    user = get.user(update.effective_user.id)
    tt = TextTranslator(user.bot_language.code)
    buttons = list_of_lists(
        [InlineKeyboardButton(
            get.book(user.bot_language.code, booknum).official_abbreviation,
            callback_data=f'{SELECT_BOOK}|{p.language.code}|{booknum}'
        ) for booknum in p.available_booknums],
        columns=5
    )

    sign_language = p.language
    p.set_language(user.bot_language.code)
    context.user_data['msg'] = context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'👋🏼 {sign_language.meps_symbol}\n{tt.choose_book}',
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=HTML,
    )


@forw
def get_book(update: Update, context: CallbackContext) -> None:
    update.callback_query.answer()
    _, sign_language_code, booknum = update.callback_query.data.split('|')
    p = BiblePassage.from_num(sign_language_code, booknum)
    show_chapters(update, context, p)


def show_chapters(update: Update, context: CallbackContext, p: BiblePassage) -> None:
    user = get.user(update.effective_user.id)
    tt = TextTranslator(user.bot_language.code)
    if fetch.need_chapter_and_videomarks(p.book):
        update.effective_message.reply_chat_action(ChatAction.TYPING)
        fetch.chapters_and_videomarkers(p.book)
        p.refresh()
    buttons = list_of_lists(
        [InlineKeyboardButton(
            str(chapter.number),
            callback_data=f'{SELECT_CHAPTER}|{p.language.code}|{p.book.number}|{chapter.number}',
        ) for chapter in get.chapters(p.book)],
        columns=8
    )
    sign_language = p.language
    p.set_language(user.bot_language.code)
    kwargs = {
        'chat_id': update.effective_chat.id,
        'text': f'👋🏼 {sign_language.meps_symbol}\n📖 <b>{p.book.name}</b>\n{tt.choose_chapter}',
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': HTML,
    }
    if update.callback_query:
        context.bot.edit_message_text(message_id=update.callback_query.message.message_id, **kwargs)
    elif context.user_data.get('msg'):
        context.bot.edit_message_text(message_id=context.user_data['msg'].message_id, **kwargs)
    else:
        context.bot.send_message(**kwargs)

@forw
def get_chapter(update: Update, context: CallbackContext) -> None:
    _, sign_language_code, booknum, chapternum = update.callback_query.data.split('|')
    p = BiblePassage.from_num(sign_language_code, booknum, chapternum)
    update.callback_query.answer()
    show_verses(update, context, p)


def show_verses(update: Update, context: CallbackContext, p: BiblePassage) -> None:
    user = get.user(update.effective_user.id)
    tt = TextTranslator(user.bot_language.code)
    if fetch.need_ffmpeg(p.chapter):
        update.effective_message.reply_chat_action(ChatAction.TYPING)
        m = update.effective_message.reply_text('⚡️ ' + tt.fetching_videomarkers)
        fetch.videomarkers_by_ffmpeg(p.chapter)
        m.delete()
        p.refresh()
    buttons = list_of_lists(
        [InlineKeyboardButton(
            str(video_marker.versenum),
            callback_data=f'{SELECT_VERSE}|{p.language.code}|{p.book.number}'
                          f'|{p.chapternumber}|{video_marker.versenum}',
        ) for video_marker in p.chapter.video_markers],
        columns=8
    )
    sign_language = p.language
    p.set_language(user.bot_language.code)
    kwargs = {
        'chat_id': update.effective_chat.id,
        'text': f'👋🏼 {sign_language.meps_symbol}\n📖 <b>{p.book.name} {p.chapternumber}</b>\n{tt.choose_verse}',
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': HTML,
    }
    if update.callback_query:
        context.bot.edit_message_text(message_id=update.callback_query.message.message_id, **kwargs)
    elif context.user_data.get('msg'):
        context.bot.edit_message_text(message_id=context.user_data['msg'].message_id, **kwargs)
    else:
        context.bot.send_message(**kwargs)


@forw
def get_verse(update: Update, context: CallbackContext) -> None:
    update.callback_query.answer()
    _, sign_lang_code, booknum, chapternum, verse = update.callback_query.data.split('|')
    p = BiblePassage.from_num(sign_lang_code, booknum, chapternum, verse)
    context.user_data['msg'] = update.callback_query.message
    manage_verses(update, context, p)


def manage_verses(update: Update, context: CallbackContext, p: BiblePassage) -> None:
    logger.info('(%s) %s', update.effective_user.name, p.citation)
    user = get.user(update.effective_user.id)
    epub = BibleEpub(get.book(user.bot_language.code, p.book.number), p.chapternumber, p.verses)
    if (file := p.chapter.get_file(p.verses, user.overlay_language_code if p.book.name != epub.book.name else None)):
        send_by_fileid(update, context, p, epub, file)
    elif len(p.verses) == 1:
        send_single_verse(update, context, p, epub)
    else:
        send_concatenate_verses(update, context, p, epub)


def send_by_fileid(update: Update, context: CallbackContext, p: BiblePassage, epub: BibleEpub, file: File) -> None:
    if context.user_data.get('msg'):
        context.user_data.get('msg').delete()
    try:
        msgvideo = context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=file.telegram_file_id,
            caption=(f'<a href="{p.url_share_jw()}">{epub.citation}</a> - '
                     f'<a href="{p.url_bible_wol_discover}">{p.language.meps_symbol}</a>'),
            parse_mode=HTML
        )
        context.bot.send_chat_action(update.effective_user.id, ChatAction.TYPING)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=epub.get_text(),
            parse_mode=HTML,
            disable_web_page_preview=True
        )
    except TelegramError as e:
        # Nunca ha pasado
        logger.critical('Al parecer se ha eliminado de los servidores de Telegram file_id=%s', file.telegram_file_id)
        context.bot.send_message(
            LOG_CHANNEL_ID,
            f'Al parecer se ha eliminado de los servidores de Telegram file_id={file.telegram_file_id}')
        send_single_verse(update, context, p, epub)
        raise e
    add.file2user(file.id, get.user(update.effective_user.id).id)
    context.bot.copy_message(LOG_CHANNEL_ID, update.effective_user.id,
                                msgvideo.message_id, disable_notification=True)


def send_single_verse(update: Update, context: CallbackContext, p: BiblePassage, epub: BibleEpub) -> None:
    msg = context.user_data.get('msg')
    user = get.user(update.effective_user.id)
    tt = TextTranslator(user.bot_language.code)

    with_overlay = user.overlay_language_code is not None and p.book.name != epub.book.name
    logger.info("Splitting %s", p.citation)
    if msg:
        msg.edit_text(f'✂️ {tt.trimming} <b>{epub.citation}</b>', parse_mode=HTML)
    else:
        msg = update.effective_message \
            .reply_text(f'✂️ {tt.trimming} <b>{epub.citation}</b>',
                        disable_notification=True,
                        parse_mode=HTML)
    context.bot.send_chat_action(update.effective_chat.id, ChatAction.RECORD_VIDEO_NOTE)
    videopath = video.split(
        p.chapter.get_videomarker(p.verses[0]),
        overlay_text=epub.citation if with_overlay else None,
        script=user.bot_language.script
    )
    update.effective_message.reply_chat_action(ChatAction.UPLOAD_VIDEO)
    msg.edit_text(f'✈️ {tt.sending} <b>{epub.citation}</b>', parse_mode=HTML)

    thumbnail = video.make_thumbnail(videopath)
    if with_overlay:
        filename = f'{safechars(p.citation)} - {p.language.meps_symbol} ({user.bot_language_code}).mp4'
    else:
        filename = f'{safechars(p.citation)} - {p.language.meps_symbol}.mp4'
    streams = video.show_streams(videopath)
    msgvideo = update.effective_message.reply_video(
        video=videopath.read_bytes(),
        filename=filename,
        caption=(f'<a href="{p.url_share_jw()}">{epub.citation}</a> - '
                    f'<a href="{p.url_bible_wol_discover}">{p.language.meps_symbol}</a>'),
        width=streams['width'],
        height=streams['height'],
        duration=round(float(streams['duration'])),
        timeout=120,
        thumb=thumbnail.read_bytes(),
        parse_mode=HTML
    )
    file = add.file(chapter_id=p.chapter.id,
                    verses=p.verses,
                    telegram_file_id=msgvideo.video.file_id,
                    telegram_file_unique_id=msgvideo.video.file_unique_id,
                    duration=msgvideo.video.duration,
                    citation=p.citation,
                    file_size=msgvideo.video.file_size,
                    overlay_language_code=user.overlay_language_code if with_overlay else None)
    add.file2user(file.id, user.id)
    update.effective_message.reply_chat_action(ChatAction.TYPING)
    update.effective_message.reply_text(
        text=epub.get_text(),
        parse_mode=HTML,
        disable_web_page_preview=True,
    )
    thumbnail.unlink()
    context.bot.copy_message(LOG_CHANNEL_ID, update.effective_chat.id, msgvideo.message_id, disable_notification=True)
    msg.delete()
    videopath.unlink()


def send_concatenate_verses(update: Update, context: CallbackContext, p: BiblePassage, epub: BibleEpub) -> None:
    user = get.user(update.effective_user.id)
    with_overlay = user.overlay_language_code is not None and p.book.name != epub.book.name
    msg = context.user_data.get('msg')
    tt = TextTranslator(user.bot_language.code)

    paths_to_concatenate, new, title_markers = [], [], []
    verses = p.verses
    for verse in verses:
        epub.verses = verse
        p.verses = verse
        title_markers.append(p.citation)
        file = p.chapter.get_file(p.verses,user.overlay_language_code if p.book.name != epub.book.name else None)
        if file:
            logger.info('Downloading verse %s from telegram servers', epub.citation)
            text = f'⬇️ {tt.downloading} <b>{epub.citation}</b>'
            if msg:
                msg.edit_text(text, parse_mode=HTML)
            else:
                msg = update.effective_message.reply_text(text, parse_mode=HTML)
            videopath = Path(f'{file.id}.mp4')  # cualquier nombre sirve
            update.effective_message.reply_chat_action(ChatAction.RECORD_VIDEO_NOTE)
            context.bot.get_file(file.telegram_file_id, timeout=120).download(custom_path=videopath)
            paths_to_concatenate.append(videopath)
        else:
            if msg:
                msg.edit_text(f'✂️ {tt.trimming} <b>{epub.citation}</b>', parse_mode=HTML)
            else:
                msg = update.effective_message.reply_text(f'✂️ {tt.trimming} <b>{epub.citation}</b>', parse_mode=HTML)
            update.effective_message.reply_chat_action(ChatAction.RECORD_VIDEO_NOTE)
            videopath = video.split(
                p.chapter.get_videomarker(verse),
                overlay_text=epub.citation if with_overlay else None,
                script=user.bot_language.script
            )
            paths_to_concatenate.append(videopath)
            new.append((verse, videopath))
    epub.verses = verses
    p.verses = verses
    logger.info('Concatenating video %s', epub.citation)
    finalpath = video.concatenate(
        inputvideos=paths_to_concatenate,
        outname=f'{safechars(p.citation)} - {p.language.meps_symbol}',
        title_chapters=title_markers,
        title=p.citation,
    )
    msg.edit_text(f'✈️ {tt.sending} <b>{epub.citation}</b>', parse_mode=HTML)
    update.effective_message.reply_chat_action(ChatAction.UPLOAD_VIDEO)
    stream = video.show_streams(finalpath)
    thumbnail = video.make_thumbnail(finalpath)
    filename = f'{safechars(p.citation)} - {p.language.meps_symbol}' + \
        (f' ({user.bot_language_code})' if with_overlay else '') + '.mp4'
    msgvideo = update.effective_message.reply_video(
        video=finalpath.read_bytes(),
        filename=filename,
        caption=(f'<a href="{p.url_share_jw()}">{epub.citation}</a> - '
                 f'<a href="{p.url_bible_wol_discover}">{p.language.meps_symbol}</a>'),
        width=stream['width'],
        height=stream['height'],
        duration=round(float(stream['duration'])),
        timeout=120,
        thumb=thumbnail,
        parse_mode=HTML
    )
    context.bot.send_chat_action(update.effective_user.id, ChatAction.TYPING)
    update.effective_message.reply_text(
        text=epub.get_text(),
        parse_mode=HTML,
        disable_web_page_preview=True,
    )
    thumbnail.unlink()
    msg.delete()
    context.bot.copy_message(LOG_CHANNEL_ID, update.effective_chat.id, msgvideo.message_id, disable_notification=True)

    file = add.file(chapter_id=p.chapter.id,
                    verses=p.verses,
                    telegram_file_id=msgvideo.video.file_id,
                    telegram_file_unique_id=msgvideo.video.file_unique_id,
                    duration=msgvideo.video.duration,
                    citation=p.citation,
                    file_size=msgvideo.video.file_size,
                    overlay_language_code=user.overlay_language_code if with_overlay else None)
    add.file2user(file.id,user.id)

    for verse, videopath in new:
        stream = video.show_streams(videopath)
        thumbnail = video.make_thumbnail(videopath)
        p.verses = verse
        epub.verses = verse
        if with_overlay:
            filename = f'{safechars(p.citation)} - {p.language.meps_symbol} ({user.bot_language_code}).mp4'
        else:
            filename = f'{safechars(p.citation)} - {p.language.meps_symbol}.mp4'
        msgvideo = context.bot.send_video(
            chat_id=BACKUP_CHANNEL_ID,
            video=videopath.read_bytes(),
            filename=filename,
            caption=(f'<a href="{p.url_share_jw()}">{epub.citation}</a> - '
                     f'<a href="{p.url_bible_wol_discover}">{p.language.meps_symbol}</a>'),
            parse_mode=HTML,
            width=stream['width'],
            height=stream['height'],
            duration=round(float(stream['duration'])),
            timeout=120,
            thumb=thumbnail,
            disable_notification=True
        )
        thumbnail.unlink()
        file = add.file(chapter_id=p.chapter.id,
                        verses=p.verses,
                        telegram_file_id=msgvideo.video.file_id,
                        telegram_file_unique_id=msgvideo.video.file_unique_id,
                        duration=msgvideo.video.duration,
                        citation=p.citation,
                        file_size=msgvideo.video.file_size,
                        overlay_language_code=user.overlay_language_code if with_overlay else None)
    for videopath in paths_to_concatenate + [finalpath]:
        videopath.unlink()


chapter_handler = CallbackQueryHandler(get_chapter, pattern=SELECT_CHAPTER)
book_handler = CallbackQueryHandler(get_book, pattern=SELECT_BOOK)
verse_handler = CallbackQueryHandler(get_verse, pattern=SELECT_VERSE)
parse_bible_handler = MessageHandler(Filters.text, parse_query)
