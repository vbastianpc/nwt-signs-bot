from pathlib import Path
import re
from random import choice

from telegram import ChatAction
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram import ParseMode
from telegram import Message
from telegram.ext import CallbackContext
from telegram.ext import CallbackQueryHandler
from telegram.ext import MessageHandler
from telegram.ext import CommandHandler
from telegram.ext import Filters
from telegram.error import TelegramError

from bot import MyCommand
from bot.database import report
from bot.secret import LOG_GROUP_ID
from bot.secret import TOPIC_BACKUP
from bot.secret import TOPIC_USE
from bot.secret import TOPIC_ERROR
from bot.logs import get_logger
from bot.jw import BiblePassage
from bot.jw import BibleEpub
from bot.utils import video
from bot.utils import how_to_say
from bot.database import get
from bot.database import fetch
from bot.database import add
from bot import exc
from bot.database.schema import File, Language
from bot.handlers.settings import set_language
from bot.utils import list_of_lists
from bot.utils.decorators import vip
from bot.utils.decorators import forw
from bot.strings import TextTranslator


logger = get_logger(__name__)

SELECT_BOOK, SELECT_CHAPTER, SELECT_VERSE = 'B', 'C', 'V'
HTML = ParseMode.HTML
COLUMNS = 8 # inline keyboard. maximum is 8
MAX_BUTTONS = 100 - 100 % COLUMNS # 100 is max telegram server. MAX_BUTTONS is beauty formatted buttons

@vip
def parse_query(update: Update, context: CallbackContext) -> None:
    logger.info(f'{context.args=}, {update.effective_message.text}')
    orig_sl = get.user(update.effective_user.id).sign_language
    tt: TextTranslator = context.user_data['tt']

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
                update.effective_message.reply_html(tt.not_language(command(text)))
                continue
            if query(text):
                if language.is_sign_language is True:
                    add.or_update_user(update.effective_user.id, sign_language_code=language.code)
                    parse_query_bible(update, context, query(text), language)
            elif len(lines) == 1 and language and not query(text):
                # change language permanent
                set_language(update, context, code_or_meps=language.code)
                return
            elif language and not query(text):
                add.or_update_user(update.effective_user.id, sign_language_code=language.code)

    add.or_update_user(update.effective_user.id, sign_language_code=orig_sl.code)


def check_passage(update: Update, query: str, bot_language_code: str) -> BiblePassage | None:
    tt = TextTranslator(bot_language_code)
    try:
        passage = BiblePassage.from_human(query, bot_language_code)
    except exc.BibleCitationNotFound:
        update.effective_message.reply_html(f'<b>{query}:</b> ' + tt.fallback(MyCommand.HELP, report.count_signlanguage()))
    except exc.BookNameNotFound as e:
        update.effective_message.reply_html(tt.book_not_found(e.book_like))
    except exc.MissingChapterNumber as e:
        update.effective_message.reply_html(tt.missing_chapter(e.bookname))
    except exc.ChapterNotExists as e:
        update.effective_message.reply_html(tt.chapter_not_exists(e.bookname, e.chapternum, e.last_chapternum))
    except exc.VerseNotExists as e:
        d = (BiblePassage.from_num(bot_language_code, e.booknum).book.name, e.chapternum, e.wrong_verses,
             e.last_versenum, e.count_wrong)
        update.effective_message.reply_html(tt.verse_not_exists(*d) if e.count_wrong == 1 else tt.verses_not_exists(*d))
    except exc.VerseOmitted as e:
        update.effective_message.reply_html(tt.is_omitted(e.citation))
        return BiblePassage.from_human(query, bot_language_code, include_omitted=True)
    else:
        return passage
    return None


def prepare_passage(passage: BiblePassage, sl_code: str, update: Update, tt: TextTranslator):
    try:
        passage.set_language(sl_code)
    except exc.BookNotFound:
        fetch.books(language_code=sl_code)
        passage.set_language(sl_code)
    if fetch.need_chapter_and_videomarks(passage.book):
        update.message.reply_chat_action(ChatAction.TYPING)
        fetch.chapters_and_videomarkers(passage.book) # could raise PubmediaNotExists
        passage.refresh()
    if passage.verses and passage.chapter:
        if fetch.need_ffmpeg(passage.chapter) is True:
            update.effective_message.reply_chat_action(ChatAction.TYPING)
            m = update.effective_message.reply_text('⚡️ ' + tt.fetching_videomarkers)
            fetch.videomarkers_by_ffmpeg(passage.chapter) # could raise PubmediaNotExists
            passage.refresh()
            m.delete()


def parse_query_bible(update: Update, context: CallbackContext, query: str, sign_language: Language = None) -> None:
    logger.info("query: %s", query)
    user = get.user(update.effective_user.id)
    tt: TextTranslator = context.user_data['tt']
    if not (passage := check_passage(update, query, user.bot_language_code)):
        return
    if passage.verses:
        context.chat_data['msgverse'] = None
        for sl in ([sign_language] if sign_language else user.sign_languages):
            try:
                prepare_passage(passage, sl.code, update, tt)
            except exc.PubmediaNotExists:
                continue
            if passage.chapter and not get.unavailable_verses(passage.chapter, passage.verses):
                manage_verses(update, context, passage)
                return
    sl = sign_language or user.sign_language
    try:
        prepare_passage(passage, sl.code, update, tt)
    except exc.PubmediaNotExists:
        passage.set_language(user.bot_language.code)
        update.effective_message.reply_text(
            text=tt.that_book_no(passage.book.name, how_to_say(sl.code, user.bot_language_code)), parse_mode=HTML)
        show_books(update, context, passage.set_language(sl.code))
        return
    if passage.chapternumber and not passage.chapter:
        p = BiblePassage.from_num(user.bot_language_code, passage.book.number)
        update.effective_message.reply_text(
            tt.that_chapter_no(p.book.name, how_to_say(sl.code, user.bot_language_code)) + " " + tt.but_these_chapters,
            parse_mode=HTML)
        show_chapters(update, context, passage.set_language(sl.code))
        return
    if passage.chapter and passage.verses:
        unavailable_verses = get.unavailable_verses(passage.chapter, passage.verses)
        if unavailable_verses:
            passage.set_language(user.bot_language.code)
            update.effective_message.reply_text(
                tt.that_verse_no(BiblePassage(passage.book, passage.chapternumber, unavailable_verses).citation,
                                how_to_say(sl.code, user.bot_language_code)) + " " +
                tt.but_these_verses, parse_mode=HTML)
            show_verses(update, context, passage.set_language(sl.code))
            return
    if passage.chapternumber:
        show_verses(update, context, passage.set_language(sl.code))
    else:
        show_chapters(update, context, passage.set_language(sl.code))


def show_books(update: Update, context: CallbackContext, p: BiblePassage = None) -> None:
    user = get.user(update.effective_user.id)
    tt: TextTranslator = context.user_data['tt']
    if not p:
        p = BiblePassage(book=get.books(user.sign_language_code)[0])

    buttons = []
    ps = BiblePassage(book=get.book(user.bot_language_code, booknum=1))
    available_booknums = p.available_booknums
    for num in range(1, 67):
        if num == 40:
            buttons += [InlineKeyboardButton(text=' ', callback_data=' ')]*3
        ps.set_booknum(num)
        buttons.append(InlineKeyboardButton(
            text=ps.book.official_abbreviation if num in available_booknums else '-',
            callback_data=f'{SELECT_BOOK}|{p.language.code}|{num}' if num in available_booknums else '-'
        ))
    buttons += [InlineKeyboardButton(text=' ', callback_data=' ')]*3
    buttons = [[InlineKeyboardButton(ps.edition.hebrew, callback_data=' ')]] + \
            list_of_lists(buttons[:42], columns=6) + \
            [[InlineKeyboardButton(ps.edition.greek, callback_data=' ')]] + \
            list_of_lists(buttons[42:], columns=6)

    update.message.reply_html(
        f'👋 {p.language.meps_symbol}\n'
        f'📖 <a href="{p.url_wol_binav}"><b>{p.book.edition.name}</b></a>\n\n'
        f'{tt.choose_book}',
        reply_markup=InlineKeyboardMarkup(buttons),
        disable_web_page_preview=True
    )


@forw
def get_book(update: Update, context: CallbackContext) -> None:
    update.callback_query.answer()
    _, sign_language_code, booknum = update.callback_query.data.split('|')
    p = BiblePassage.from_num(sign_language_code, booknum)
    show_chapters(update, context, p)


def show_chapters(update: Update, context: CallbackContext, p: BiblePassage) -> None:
    tt: TextTranslator = context.user_data['tt']
    if fetch.need_chapter_and_videomarks(p.book):
        update.effective_message.reply_chat_action(ChatAction.TYPING)
        fetch.chapters_and_videomarkers(p.book)
        p.refresh()
    buttons = []
    available_chapternumbers = [chapter.number for chapter in get.chapters(p.book)]
    for chapternumber in range(1, get.last_chapternum(p.book.number) + 1):
        if chapternumber in available_chapternumbers:
            buttons.append(InlineKeyboardButton(
                str(chapternumber),
                callback_data=f'{SELECT_CHAPTER}|{p.language.code}|{p.book.number}|{chapternumber}',
            ))
        else:
            buttons.append(InlineKeyboardButton('-', callback_data='-'))
    if len(buttons) % COLUMNS:
        buttons += [InlineKeyboardButton(' ', callback_data=' ') for _ in range(COLUMNS - len(buttons) % COLUMNS)]

    sign_language = p.language
    p.set_language(tt.language_code)
    text = f'👋🏼 {sign_language.meps_symbol}\n📖 <b>{p.book.name}</b>\n{tt.choose_chapter}'
    lkwargs = []
    while True:
        keyboard = list_of_lists(buttons[:MAX_BUTTONS], COLUMNS)

        lkwargs.append({
            'chat_id': update.effective_chat.id,
            'text': text,
            'reply_markup': InlineKeyboardMarkup(keyboard),
            'parse_mode': HTML,
        })

        if len(buttons) > MAX_BUTTONS:
            buttons = buttons[MAX_BUTTONS:]
            text = chr(12644) # empty space
        else:
            break

    lmsg = []
    if update.callback_query:
        lmsg.append(context.bot.edit_message_text(message_id=update.callback_query.message.message_id, **lkwargs[0]))
        for kwargs in lkwargs[1:]:
            lmsg.append(context.bot.send_message(**kwargs))
    else:
        for kwargs in lkwargs:
            lmsg.append(context.bot.send_message(**kwargs))
    context.chat_data['lmsg'] = lmsg


@forw
def get_chapter(update: Update, context: CallbackContext) -> None:
    _, sign_language_code, booknum, chapternum = update.callback_query.data.split('|')
    p = BiblePassage.from_num(sign_language_code, booknum, chapternum)
    update.callback_query.answer()
    show_verses(update, context, p)


def show_verses(update: Update, context: CallbackContext, p: BiblePassage) -> None:
    tt: TextTranslator = context.user_data['tt']
    if fetch.need_ffmpeg(p.chapter):
        update.effective_message.reply_chat_action(ChatAction.TYPING)
        m = update.effective_message.reply_text('⚡️ ' + tt.fetching_videomarkers)
        fetch.videomarkers_by_ffmpeg(p.chapter)
        m.delete()
        p.refresh()

    buttons = []
    available_versenumbers = [vm.versenum for vm in get.videomarkers(p.chapter)]
    for versenumber in range(1, get.last_versenum(p.book.number, p.chapternumber) + 1):
        if versenumber in available_versenumbers:
            buttons.append(InlineKeyboardButton(
                str(versenumber),
                callback_data=f'{SELECT_VERSE}|{p.language.code}|{p.book.number}|{p.chapternumber}|{versenumber}',
            ))
        else:
            buttons.append(InlineKeyboardButton('-', callback_data='-'))
    if len(buttons) % COLUMNS:
        buttons += [InlineKeyboardButton(' ', callback_data=' ') for _ in range(COLUMNS - len(buttons) % COLUMNS)]

    sign_language = p.language
    p.set_language(tt.language_code)
    text = f'👋🏼 {sign_language.meps_symbol}\n📖 <b>{p.book.name} {p.chapternumber}</b>\n{tt.choose_verse}'
    lkwargs = []
    while True:
        keyboard = list_of_lists(buttons[:MAX_BUTTONS], COLUMNS)

        lkwargs.append({
            'chat_id': update.effective_chat.id,
            'text': text,
            'reply_markup': InlineKeyboardMarkup(keyboard),
            'parse_mode': HTML,
        })
        if len(buttons) > MAX_BUTTONS:
            buttons = buttons[MAX_BUTTONS:]
            text = chr(12644) # empty space
        else:
            break

    for msg in context.chat_data.get('lmsg', []):
        msg: Message
        if update.callback_query and update.callback_query.message.message_id != msg.message_id:
            msg.delete()
    lmsg = []
    if update.callback_query:
        lmsg.append(context.bot.edit_message_text(message_id=update.callback_query.message.message_id, **lkwargs[0]))
        for kwargs in lkwargs[1:]:
            lmsg.append(context.bot.send_message(**kwargs))
    else:
        for kwargs in lkwargs:
            lmsg.append(context.bot.send_message(**kwargs))
    context.chat_data['lmsg'] = lmsg



@forw
def get_verse(update: Update, context: CallbackContext) -> None:
    update.callback_query.answer()
    _, sign_lang_code, booknum, chapternum, verse = update.callback_query.data.split('|')
    p = BiblePassage.from_num(sign_lang_code, booknum, chapternum, verse)
    context.chat_data['msgverse'] = update.callback_query.message
    manage_verses(update, context, p)


def manage_verses(update: Update, context: CallbackContext, p: BiblePassage) -> None:
    logger.info('(%s) %s', update.effective_user.name, p.citation)
    user = get.user(update.effective_user.id)
    epub = BibleEpub(get.book(user.bot_language.code, p.book.number), p.chapternumber, p.verses)

    if user.overlay_language_code and p.book.name != get.book(user.overlay_language_code, p.book.number).name:
        overlay = context.user_data['overlay'] = BiblePassage.from_num(
            user.overlay_language_code,
            p.book.number,
            p.chapternumber,
            p.verses)
    else:
        overlay = context.user_data['overlay'] = None
    delogo = context.user_data['delogo'] = bool(user.delogo and overlay)

    if (file := p.chapter.get_file(p.verses, overlay.language.code if overlay else None, delogo)):
        send_by_fileid(update, context, p, epub, file)
    elif len(p.verses) == 1:
        send_single_verse(update, context, p, epub)
    else:
        send_concatenate_verses(update, context, p, epub)


def send_by_fileid(update: Update, context: CallbackContext, p: BiblePassage, epub: BibleEpub, file: File) -> None:
    if context.chat_data.get('msgverse'):
        context.chat_data['msgverse'].delete()
    try:
        msgvideo = context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=file.telegram_file_id,
            caption=(f'<a href="{p.url_share_jw()}">{epub.citation}</a> - '
                     f'<a href="{p.url_bible_wol_discover}">{p.language.meps_symbol}</a>'),
            parse_mode=HTML
        )
        context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=epub.get_text(),
            parse_mode=HTML,
            disable_web_page_preview=True
        )
    except TelegramError as e:
        logger.critical('Al parecer se ha eliminado de los servidores de Telegram file_id=%s', file.telegram_file_id)
        context.bot.send_message(
            LOG_GROUP_ID,
            text=f'Al parecer se ha eliminado de los servidores de Telegram {file.citation}'
                 f'\n\n<pre>{file.id=}\n\n{file.language.code}\n\n{e.message=}\n\n{e.__class__.__name__}</pre>',
            message_thread_id=TOPIC_ERROR,
            parse_mode=HTML
        )
        send_single_verse(update, context, p, epub)
        raise e
    add.file2user(file.id, get.user(update.effective_user.id).id)
    context.bot.copy_message(LOG_GROUP_ID, update.effective_chat.id, msgvideo.message_id,
                             message_thread_id=TOPIC_USE, disable_notification=True)


def send_single_verse(update: Update, context: CallbackContext, p: BiblePassage, epub: BibleEpub) -> None:
    msg: Message | None = context.chat_data.get('msgverse')
    user = get.user(update.effective_user.id)
    tt: TextTranslator = context.user_data['tt']
    overlay: BiblePassage | None = context.user_data['overlay']
    delogo: bool = context.user_data['delogo']

    logger.info(f"Splitting {p.citation} delogo={delogo}")
    text = (f'✂️ {tt.trimming} <b>{epub.citation} - {p.language.meps_symbol}'
            f'{" - " + overlay.language.meps_symbol if overlay else ""}'
            f'{" delogo" if delogo else ""}'
            '</b>')
    if msg:
        msg.edit_text(text, parse_mode=HTML)
    else:
        msg = update.effective_message.reply_html(text, disable_notification=True)
    context.bot.send_chat_action(update.effective_chat.id, ChatAction.RECORD_VIDEO_NOTE)
    videopath = video.split(p, overlay, delogo)
    update.effective_message.reply_chat_action(ChatAction.UPLOAD_VIDEO)
    msg.edit_text(f'✈️ {tt.sending} <b>{epub.citation}</b>', parse_mode=HTML)

    thumbnail = video.make_thumbnail(videopath)
    streams = video.show_streams(videopath)
    msgvideo = update.effective_message.reply_video(
        video=videopath.read_bytes(),
        filename=videopath.name,
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
                    duration=float(streams['duration']),
                    citation=p.citation,
                    file_size=msgvideo.video.file_size,
                    overlay_language_code=overlay.language.code if overlay else None,
                    delogo=delogo)
    add.file2user(file.id, user.id)
    update.effective_message.reply_chat_action(ChatAction.TYPING)
    update.effective_message.reply_html(text=epub.get_text(), disable_web_page_preview=True)
    thumbnail.unlink()
    context.bot.copy_message(LOG_GROUP_ID, update.effective_chat.id, msgvideo.message_id,
                             message_thread_id=TOPIC_USE, disable_notification=True)
    msg.delete()
    videopath.unlink()

    del context.user_data['delogo']
    del context.user_data['overlay']


def send_concatenate_verses(update: Update, context: CallbackContext, p: BiblePassage, epub: BibleEpub) -> None:
    user = get.user(update.effective_user.id)
    overlay: BiblePassage | None = context.user_data['overlay']
    delogo: bool = context.user_data['delogo']
    msg: Message | None = context.chat_data.get('msgverse')
    tt: TextTranslator = context.user_data['tt']

    paths_to_concatenate, new, title_markers = [], [], []
    verses = p.verses
    for verse in verses:
        epub.verses = verse
        p.verses = verse
        if overlay:
            overlay.verses = verse
        title_markers.append(p.citation)
        file = p.chapter.get_file(
            verses=p.verses,
            overlay_language_code=overlay.language.code if overlay else None,
            delogo=delogo
            )
        if file:
            logger.info('Downloading verse %s from telegram servers', epub.citation)
            text = f'⬇️ {tt.downloading} <b>{epub.citation}</b>'
            if msg:
                msg.edit_text(text, parse_mode=HTML)
            else:
                msg = update.effective_message.reply_html(text)
            videopath = Path(f'{file.id}.mp4')  # cualquier nombre sirve
            update.effective_message.reply_chat_action(ChatAction.RECORD_VIDEO_NOTE)
            context.bot.get_file(file.telegram_file_id, timeout=120).download(custom_path=videopath)
            paths_to_concatenate.append(videopath)
        else:
            text = f'✂️ {tt.trimming} <b>{epub.citation} - {p.language.meps_symbol}' \
                   f'{" - " + overlay.language.meps_symbol if overlay else ""}</b>'
            if msg:
                msg.edit_text(text, parse_mode=HTML)
            else:
                msg = update.effective_message.reply_html(text)
            update.effective_message.reply_chat_action(ChatAction.RECORD_VIDEO_NOTE)
            videopath = video.split(p, overlay, delogo)
            paths_to_concatenate.append(videopath)
            new.append((verse, videopath))
    epub.verses = verses
    p.verses = verses
    logger.info('Concatenating video %s', epub.citation)

    finalpath = video.concatenate(
        inputvideos=paths_to_concatenate,
        outname=video.set_filename(p, overlay, delogo),
        title_chapters=title_markers,
        title=p.citation,
    )
    msg.edit_text(f'✈️ {tt.sending} <b>{epub.citation}</b>', parse_mode=HTML)
    update.effective_message.reply_chat_action(ChatAction.UPLOAD_VIDEO)
    stream = video.show_streams(finalpath)
    thumbnail = video.make_thumbnail(finalpath)
    msgvideo = update.effective_message.reply_video(
        video=finalpath.read_bytes(),
        filename=finalpath.name,
        caption=(f'<a href="{p.url_share_jw()}">{epub.citation}</a> - '
                 f'<a href="{p.url_bible_wol_discover}">{p.language.meps_symbol}</a>'),
        width=stream['width'],
        height=stream['height'],
        duration=round(float(stream['duration'])),
        timeout=120,
        thumb=thumbnail,
        parse_mode=HTML
    )
    context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    update.effective_message.reply_html(epub.get_text(), disable_web_page_preview=True)
    thumbnail.unlink()
    msg.delete()
    context.bot.copy_message(LOG_GROUP_ID, update.effective_chat.id, msgvideo.message_id,
                             message_thread_id=TOPIC_USE, disable_notification=True)

    file = add.file(chapter_id=p.chapter.id,
                    verses=p.verses,
                    telegram_file_id=msgvideo.video.file_id,
                    telegram_file_unique_id=msgvideo.video.file_unique_id,
                    duration=float(stream['duration']),
                    citation=p.citation,
                    file_size=msgvideo.video.file_size,
                    overlay_language_code=overlay.language.code if overlay else None,
                    delogo=delogo)
    add.file2user(file.id,user.id)

    for verse, videopath in new:
        stream = video.show_streams(videopath)
        thumbnail = video.make_thumbnail(videopath)
        p.verses = verse
        epub.verses = verse
        msgvideo = context.bot.send_video(
            chat_id=LOG_GROUP_ID,
            message_thread_id=TOPIC_BACKUP,
            video=videopath.read_bytes(),
            filename=video.set_filename(p, overlay, delogo),
            caption=(f'<a href="{p.url_share_jw()}">{epub.citation}</a> - '
                     f'<a href="{p.url_bible_wol_discover}">{p.language.meps_symbol}</a>'),
            parse_mode=HTML,
            width=stream['width'],
            height=stream['height'],
            duration=round(float(stream['duration'])),
            timeout=120,
            # thumb=thumbnail,
            disable_notification=True
        )
        thumbnail.unlink()
        file = add.file(chapter_id=p.chapter.id,
                        verses=p.verses,
                        telegram_file_id=msgvideo.video.file_id,
                        telegram_file_unique_id=msgvideo.video.file_unique_id,
                        duration=float(stream['duration']),
                        citation=p.citation,
                        file_size=msgvideo.video.file_size,
                        overlay_language_code=overlay.language.code if overlay else None,
                        delogo=delogo)
    for videopath in paths_to_concatenate + [finalpath]:
        videopath.unlink()
    del context.user_data['delogo']
    del context.user_data['overlay']


def fallback_query(update: Update, context: CallbackContext):
    tt: TextTranslator = context.user_data['tt']
    match update.callback_query.data:
        case ' ':
            update.callback_query.answer(choice('😀😃😄😁😆🙂🙃😉🧐😝😏🤔'))
        case '-':
            update.callback_query.answer(tt.not_available)


chapter_handler = CallbackQueryHandler(get_chapter, pattern=SELECT_CHAPTER)
book_handler = CallbackQueryHandler(get_book, pattern=SELECT_BOOK)
verse_handler = CallbackQueryHandler(get_verse, pattern=SELECT_VERSE)
show_books_handler = CommandHandler(MyCommand.BIBLE, vip(show_books))
parse_bible_handler = MessageHandler(Filters.text, parse_query)
fallback_query_handler = CallbackQueryHandler(fallback_query)
