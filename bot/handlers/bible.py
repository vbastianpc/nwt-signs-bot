from pathlib import Path

from telegram import ChatAction
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.error import TelegramError

from bot import CHANNEL_ID, MyCommand, get_logger
from bot import ADMIN
from bot.jw.jwpubmedia import JWBible
from bot.jw.jwlanguage import JWLanguage
from bot.utils import video
from bot.database import localdatabase as db
from bot.database.schemedb import SentVerse, Language
from bot.database import start_database
from bot.booknames.parse import parse_bible_citation
from bot.booknames.parse import BooknumNotFound, BibleCitationNotFound
from bot.handlers.start import all_fallback
from bot.handlers.settings import set_lang
from bot.utils import list_of_lists
from bot.utils import safechars
from bot.utils.decorators import vip, forw
from bot.strings import TextGetter


logger = get_logger(__name__)

FORWARD_TO_CHANNEL = True
SELECTING_CHAPTERS, SELECTING_VERSES = 'C', 'V'


def forward_to_channel(bot, from_chat_id, message_id):
    if FORWARD_TO_CHANNEL and from_chat_id != ADMIN:
        bot.forward_message(
            CHANNEL_ID,
            from_chat_id=from_chat_id,
            message_id=message_id,
        )

@vip
def parse_lang_bible(update: Update, context: CallbackContext) -> None:
    sign_lang_code = update.effective_message.text.split()[0].strip('/').upper()
    logger.info("%s", context.args)
    if context.args:
        parse_bible(update, context, ' '.join(context.args), sign_lang_code)
    else:
        set_lang(update, context, sign_lang_code)
    return


@vip
@forw
def parse_bible(update: Update, context: CallbackContext, likely_bible_citation=None, sign_lang_code=None) -> None:
    reply_text = update.effective_message.reply_text
    db_user = db.get_user(update.effective_user.id)
    t = TextGetter(db_user.bot_lang)
    try:
        sign_lang_code = sign_lang_code or db_user.signlanguage.code
    except AttributeError:
        reply_text(t.choose_signlang.format(MyCommand.SIGNLANGUAGE), parse_mode=ParseMode.MARKDOWN)
        return

    likely_bible_citation = likely_bible_citation or update.effective_message.text.strip('/')
    try:
        book, chapter, verses = parse_bible_citation(likely_bible_citation, db_user.bot_lang)
    except BooknumNotFound:
        reply_text(t.book_not_found.format(MyCommand.BOOKNAMES), parse_mode=ParseMode.MARKDOWN)
        return
    except BibleCitationNotFound:
        return all_fallback(update, context)

    context.user_data['msg'] = None
    jw = JWBible(sign_lang_code, book.booknum, chapter, verses, JWLanguage(locale=db_user.bot_lang))
    kwargs = context.user_data['kwargs'] = {
        'sign_lang_code': sign_lang_code,
        'booknum': book.booknum,
        'chapter': chapter,
        'verses': verses,
        'raw_verses': ' '.join(map(str, verses)),
        'telegram_user_id': update.effective_user.id,
    }

    if not jw.pubmedia_exists():
        reply_text(
            text=t.unavailable.format(book.full_name, sign_lang_code) + " " + t.optional_book.format(MyCommand.SIGNLANGUAGE),
            parse_mode=ParseMode.MARKDOWN    
        )
        return

    kwargs.update({
        'quality': jw.get_best_quality(),
        # 'bookname': jw.bookname,
    })
    db.query_or_create_bible_book(**context.user_data['kwargs'], bookname=jw.bookname)

    if jw.chapter and not jw.check_chapternumber():
        reply_text(
            text=t.unavailable.format(f'{jw.bookname} {jw.chapter}', sign_lang_code) + ' ' + t.optional_chapter,
            parse_mode=ParseMode.MARKDOWN
        )
        kwargs.update({'chapter': None})
        return show_chapters(update, context)

    if chapter:
        kwargs.update({'checksum': jw.get_checksum()})
        context.bot.send_chat_action(update.effective_user.id, ChatAction.TYPING)
        db.manage_video_markers(jw.get_markers, **kwargs)

    if verses:
        manage_verses(update, context)
    elif chapter:
        show_verses(update, context)
    else:
        show_chapters(update, context)


def show_chapters(update: Update, context: CallbackContext):
    jw = JWBible(**context.user_data['kwargs'])
    t = TextGetter(db.get_user(update.effective_user.id).bot_lang)
    buttons = list_of_lists(
        [InlineKeyboardButton(
            str(chapter),
            callback_data=f'{SELECTING_CHAPTERS}|{jw.lang.code}|{jw.booknum}|{chapter}|{jw.get_checksum(chapter)}',
        ) for chapter in jw.get_all_chapternumber()],
        columns=8
    )
    kwargs = {
        'chat_id': update.effective_chat.id,
        'text': f'????????????? {jw.lang.code}\n???? {jw.bookname}\n{t.choose_chapter}',
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': ParseMode.MARKDOWN,
    }
    context.user_data['msg'] = context.bot.edit_message_text(**kwargs) if update.callback_query else context.bot.send_message(**kwargs)
    delete_objects(update, context)


@forw
def get_chapter(update: Update, context: CallbackContext):
    _, sign_lang_code, booknum, chapter, checksum = update.callback_query.data.split('|')
    context.user_data['kwargs'] = {
        'sign_lang_code': sign_lang_code,
        'booknum': booknum,
        'chapter': chapter,
        'checksum': checksum,
    }
    jw = JWBible(**context.user_data['kwargs'])
    db.manage_video_markers(jw.get_markers, **context.user_data['kwargs'])
    update.callback_query.answer()
    show_verses(update, context)


def show_verses(update: Update, context: CallbackContext):
    jw = JWBible(**context.user_data['kwargs'])
    bible_chapter = db.get_bible_chapter(**context.user_data['kwargs'])
    t = TextGetter(db.get_user(update.effective_user.id).bot_lang)

    buttons = list_of_lists(
        [InlineKeyboardButton(
            str(verse),
            callback_data=f'{SELECTING_VERSES}|{jw.lang.code}|{jw.booknum}|{jw.chapter}|{jw.get_checksum()}|{verse}',
        ) for verse in (video_marker.versenum for video_marker in bible_chapter.video_markers)],
        columns=8
    )
    if update.callback_query:
        message_id = update.callback_query.message.message_id
    elif context.user_data.get('msg'):
        message_id = context.user_data['msg'].message_id
    else:
        message_id = None

    kwargs = {
        'chat_id': update.effective_chat.id,
        'text': f'????????????? {jw.lang.code}\n???? {jw.bookname} {jw.chapter}\n{t.choose_verse}',
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': ParseMode.MARKDOWN,
    }
    if message_id:
        context.bot.edit_message_text(message_id=message_id, **kwargs)
    else:
        context.bot.send_message(**kwargs)
    delete_objects(update, context)


@forw
def get_verse(update: Update, context: CallbackContext):
    update.callback_query.answer()
    _, sign_lang_code, booknum, chapter, checksum, verse = update.callback_query.data.split('|')
    context.user_data['kwargs'] = {
        'sign_lang_code': sign_lang_code,
        'booknum': booknum,
        'chapter': chapter,
        'checksum': checksum,
        'verses': [int(verse)],
        'raw_verses': str(verse),
        'telegram_user_id': update.effective_user.id
    }
    context.user_data['msg'] = update.callback_query.message
    manage_verses(update, context)
    return


def manage_verses(update: Update, context: CallbackContext):
    db_user = db.get_user(update.effective_user.id)
    kwargs = context.user_data['kwargs']
    kwargs.update({
        'lang_locale_written': db_user.bot_lang,
        'bookname': db.get_bookname(db_user.bot_lang, kwargs['booknum']).full_name
    })
    jw = context.user_data['jw'] = JWBible(**kwargs)
    kwargs.update(dict(quality=jw.get_best_quality()))
    t = TextGetter(db.get_user(update.effective_user.id).bot_lang)
    logger.info('(%s) %s', update.effective_user.name, jw.citation())

    not_available = [verse for verse in kwargs['verses'] if int(verse) not in db.get_all_versenumbers(**kwargs)]
    if len(not_available) == 1:
        v = not_available[0]
    elif len(not_available) > 1:
        v = ", ".join(map(str, not_available))
    if not_available:
        update.effective_message.reply_text(
            text=t.unavailable.format(f'{jw.bookname} {jw.chapter}:{v}', jw.lang.code) + ' ' + t.optional_verse,
            parse_mode=ParseMode.MARKDOWN
        )
        show_verses(update, context)
        return

    sent_verse = db.query_sent_verse(**kwargs)
    if sent_verse and sent_verse.raw_verses == ' '.join(map(str, kwargs['verses'])):
        send_by_fileid(update, context, sent_verse, jw)
        return

    if len(jw.verses) == 1:
        send_single_verse(update, context)
    else:
        send_concatenate_verses(update, context)
    logger.info('Success!')
    delete_objects(update, context)
    return


def send_by_fileid(update: Update, context: CallbackContext, sent_verse: SentVerse, jw: JWBible):
    logger.info('Sending by file_id')
    bookname = context.user_data['kwargs']['bookname']
    if context.user_data.get('msg'):
        context.user_data.get('msg').delete()
    try:
        msgverse = context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=sent_verse.telegram_file_id,
            caption=f'<a href="{jw.wol_discover()}"><b>{jw.citation(bookname)} - {jw.lang.code}</b></a>',
            parse_mode=ParseMode.HTML
        )
        context.bot.send_chat_action(update.effective_user.id, ChatAction.TYPING)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=jw.nwt.passages(),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    except TelegramError as e:
        # Nunca ha pasado
        logger.critical('Al parecer se ha eliminado de los servidores de Telegram %s file_id=%s', sent_verse.citation, sent_verse.telegram_file_id)
        raise e

    else:
        db.add_sent_verse_user(sent_verse, update.effective_user.id)
        forward_to_channel(context.bot, update.effective_chat.id, msgverse.message_id)
    return


def send_single_verse(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    jw = context.user_data['jw']
    msg = context.user_data.get('msg')
    t = TextGetter(db.get_user(update.effective_user.id).bot_lang)
    verse = str(jw.verses[0])
    bookname = context.user_data['kwargs']['bookname']
    citation = f'{bookname} {jw.chapter}:{verse}'
    logger.info("Splitting %s", citation)
    text = f'?????? {t.trimming} {citation}'
    if msg:
        msg.edit_text(text)
    else:
        msg = message.reply_text(text, disable_notification=True)
    context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
    marker = db.get_videomarker(versenum=verse, **context.user_data['kwargs'])
    versepath = video.split(jw.get_video_url(), marker)
    streams = video.show_streams(versepath)
    context.bot.send_chat_action(chat.id, ChatAction.UPLOAD_VIDEO)
    msg.edit_text(f'???? {t.sending} {citation}', parse_mode=ParseMode.MARKDOWN)
    thumbnail = video.make_thumbnail(versepath)
    logger.info('%s', thumbnail)
    msgverse = context.bot.send_video(
        chat_id=chat.id,
        video=versepath.read_bytes(),
        filename=f'{versepath.stem} - {jw.lang.code}.mp4',
        caption=f'<a href="{jw.wol_discover()}"><b>{citation} - {jw.lang.code}</b></a>',
        width=streams['width'],
        height=streams['height'],
        duration=round(float(streams['duration'])),
        timeout=120,
        thumb=thumbnail,
        parse_mode=ParseMode.HTML
    )
    context.bot.send_chat_action(update.effective_user.id, ChatAction.TYPING)
    context.bot.send_message(
        chat_id=chat.id,
        text=jw.nwt.passages(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    thumbnail.unlink()
    msg.delete()
    forward_to_channel(context.bot, chat.id, msgverse.message_id)
    context.user_data['kwargs'].update({
        'citation': jw.citation(verses=verse),
        'telegram_file_id': msgverse.video.file_id,
        'size': versepath.stat().st_size,
        'verses': verse,
    })
    sent_verse = db.add_sent_verse(**context.user_data['kwargs'])
    db.add_sent_verse_user(sent_verse, update.effective_user.id)
    versepath.unlink()


def send_concatenate_verses(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    jw = context.user_data['jw']
    kwargs = context.user_data['kwargs']
    msg = context.user_data.get('msg')
    t = TextGetter(db.get_user(update.effective_user.id).bot_lang)
    bookname = kwargs['bookname']
    raw_verses = ' '.join(map(str, jw.verses))

    paths_to_concatenate = []
    new = []
    for verse in jw.verses:
        kwargs.update({'raw_verses': str(verse)})
        sent_verse = db.query_sent_verse(**kwargs)
        citation = f'{bookname} {jw.chapter}:{verse}'
        if sent_verse:
            logger.info('Downloading verse %s from telegram servers', citation)
            text = f'???? {t.downloading} {citation}'
            if msg:
                msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)
            else:
                msg = message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            versepath = Path(f'{sent_verse.id}.mp4')
            context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
            context.bot.get_file(sent_verse.telegram_file_id, timeout=120).download(custom_path=versepath)
            paths_to_concatenate.append(versepath)
        else:
            logger.info("Splitting %s", citation)
            text = f'?????? {t.trimming} {citation}'
            if msg:
                msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)
            else:
                msg = message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
            marker = db.get_videomarker(versenum=verse, **context.user_data['kwargs'])
            versepath = video.split(jw.get_video_url(), marker)
            paths_to_concatenate.append(versepath)
            new.append((verse, versepath))
    citation = jw.citation(bookname)
    logger.info('Concatenating video %s', citation)
    msg.edit_text(f'???? {t.splicing}', parse_mode=ParseMode.MARKDOWN)
    finalpath = video.concatenate(
        inputvideos=paths_to_concatenate,
        outname=f'{safechars(jw.citation())} - {jw.lang.code}',
        title_chapters=[jw.citation(verses=verse) for verse in jw.verses],
        title=jw.citation(),
    )
    logger.info('Sending concatenated video %s', finalpath)
    msg.edit_text(f'???? {t.sending} {citation}', parse_mode=ParseMode.MARKDOWN)
    context.bot.send_chat_action(chat.id, ChatAction.UPLOAD_VIDEO)
    stream = video.show_streams(finalpath)
    thumbnail = video.make_thumbnail(finalpath)
    msgverse = context.bot.send_video(
        chat_id=chat.id,
        video=finalpath.read_bytes(),
        filename=finalpath.name,
        caption=f'<a href="{jw.wol_discover()}"><b>{citation} - {jw.lang.code}</b></a>',
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
        text=jw.nwt.passages(),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )
    thumbnail.unlink()
    msg.delete()
    forward_to_channel(context.bot, chat.id, msgverse.message_id)
    kwargs.update({
        'citation': jw.citation(),
        'telegram_file_id': msgverse.video.file_id,
        'size': finalpath.stat().st_size,
        'raw_verses': raw_verses,
    })
    sent_verse = db.add_sent_verse(**kwargs)
    db.add_sent_verse_user(sent_verse, update.effective_user.id)
    for verse, versepath in new:
        stream = video.show_streams(versepath)
        thumbnail = video.make_thumbnail(versepath)
        msgverse = context.bot.send_video(
            chat_id=CHANNEL_ID,
            video=versepath.read_bytes(),
            filename=f'{versepath.stem} - {jw.lang.code}.mp4',
            caption=f'<a href="{jw.wol_discover()}"><b>{jw.citation(verses=verse)} - {jw.lang.code}</b></a>',
            parse_mode=ParseMode.HTML,
            width=stream['width'],
            height=stream['height'],
            duration=round(float(stream['duration'])),
            timeout=120,
            thumb=thumbnail,
        )
        thumbnail.unlink()
        kwargs.update({
            'citation': jw.citation(verses=verse),
            'telegram_file_id': msgverse.video.file_id,
            'size': versepath.stat().st_size,
            'raw_verses': str(verse)
        })
        sent_verse = db.add_sent_verse(**kwargs)
        db.add_sent_verse_user(sent_verse, update.effective_user.id)
    for versepath in paths_to_concatenate + [finalpath]:
        versepath.unlink()


def delete_objects(update: Update, context: CallbackContext):
    context.user_data.pop('jw', None)
    context.user_data.pop('kwargs', None)
    context.user_data.pop('msg', None)


SIGN_LANGCODES = [
        lang[0] for lang in
        start_database().query(Language.code)
        .filter(Language.is_sign_lang == True)
        .all()
    ]


parse_bible_text_handler = MessageHandler(Filters.text, parse_bible)
chapter_handler = CallbackQueryHandler(get_chapter, pattern=SELECTING_CHAPTERS)
verse_handler = CallbackQueryHandler(get_verse, pattern=SELECTING_VERSES)
parse_lang_bible_handler = CommandHandler(SIGN_LANGCODES, parse_lang_bible)
# parse_lang_bible_handler = MessageHandler(Filters.command, parse_lang_bible)
