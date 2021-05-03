
from pathlib import Path
import logging
import re

from telegram import (
    ChatAction,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ParseMode,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    Filters,
)

from models import UserController
from models import JWPubMedia, LocalData, Video
from utils import (
    BIBLE_BOOKALIAS_NUM,
    list_of_lists,
    BIBLE_PATTERN,
    parse_bible_pattern,
    safechars,
)
from utils.decorators import vip, forw
from utils.secret import CHANNEL_ID


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

FORWARD_TO_CHANNEL = True
SELECTING_CHAPTERS, SELECTING_VERSES = 'SELECTING_CHAPTERS', 'SELECTING_VERSES'


def forward_to_channel(bot, from_chat_id, message_id):
    if FORWARD_TO_CHANNEL:
        bot.forward_message(
            CHANNEL_ID,
            from_chat_id=from_chat_id,
            message_id=message_id,
        )


@forw
@vip
def parse_bible(update: Update, context: CallbackContext):
    booknum, chapter, verses = parse_bible_pattern(update.message.text.strip('/'))
    uc = UserController(update.effective_user.id)
    context.user_data['jw'] = JWPubMedia(
        lang=uc.lang(),
        booknum=booknum,
        chapter=chapter,
        verses=verses,
        quality=uc.quality(),
    )
    if verses:
        return manage_verses(update, context)
    elif chapter:
        return show_verses(update, context)
    else:
        return show_chapters(update, context)


def show_chapters(update: Update, context: CallbackContext):
    jw = context.user_data['jw']
    buttons = list_of_lists(
        [InlineKeyboardButton(
            chapter,
            callback_data=f'{SELECTING_CHAPTERS}||{jw.booknum}||{chapter}||',
        ) for chapter in jw.available_chapters()],
        columns=8
    )
    kwargs = {
        'chat_id': update.effective_chat.id,
        'text': f'📖 *{jw.bookname}*\nElige un capítulo',
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': ParseMode.MARKDOWN,
    }
    if update.callback_query:
        update.effective_message.edit_text(**kwargs)
    else:
        context.bot.send_message(**kwargs)


def get_chapter(update: Update, context: CallbackContext):
    update.callback_query.answer()
    _, booknum, chapter, _ = update.callback_query.data.split('||')
    uc = UserController(update.effective_user.id)
    context.user_data['jw'] = JWPubMedia(
        lang=uc.lang(),
        booknum=booknum,
        chapter=chapter,
        quality=uc.quality(),
    )
    show_verses(update, context)


def show_verses(update: Update, context: CallbackContext):
    jw = context.user_data['jw']
    buttons = list_of_lists(
        [InlineKeyboardButton(
            verse,
            callback_data=f'{SELECTING_VERSES}||{jw.booknum}||{jw.chapter}||{verse}',
        ) for verse in jw.available_verses()],
        columns=8
    )
    kwargs = {
        'chat_id': update.effective_chat.id,
        'text': f'📖 *{jw.bookname} {jw.title_chapter}*\nElige un versículo',
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': ParseMode.MARKDOWN,
    }
    if update.callback_query:
        context.bot.edit_message_text(
            message_id=update.callback_query.message.message_id,
            **kwargs,
        )
    else:
        context.bot.send_message(**kwargs)


def get_verse(update: Update, context: CallbackContext):
    update.callback_query.answer('Espera unos momentos')
    _, booknum, chapter, verse = update.callback_query.data.split('||')
    uc = UserController(update.effective_user.id)
    context.user_data['jw'] = JWPubMedia(
        lang=uc.lang(),
        booknum=booknum,
        chapter=chapter,
        verses=[verse],
        quality=uc.quality(),
    )
    update.callback_query.message.delete()
    return manage_verses(update, context)


def manage_verses(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    jw = context.user_data['jw']
    db = LocalData(
        booknum=jw.booknum,
        chapter=jw.chapter,
        lang=jw.lang,
        quality=jw.quality,
    )
    context.user_data['db'] = db
    context.user_data['msg'] = None

    if jw.chapter not in jw.available_chapters():
        message.reply_text(f'El capítulo {jw.chapter} de {jw.bookname} no está disponible 🤷🏻‍♂️')
        return
    elif jw.not_available_verses():
        na = jw.not_available_verses()
        message.reply_text(
            f'{jw.bookname} {jw.chapter}:' + 
            (f'{na[0]} no está disponible 🤷🏻‍♂️' if len(na) == 1 else f'{", ".join(na)} no están disponibles 🤷🏻‍♂️')
        )
        return

    logger.info('(%s) %s', update.effective_user.name, f'{jw.booknum} {jw.chapter} {jw.verses}')
    logger.info('%s', f'{jw.filesize} {db.filesize}')

    verse = jw.verses[0] if len(jw.verses) == 1 else ' '.join(jw.verses)
    if verse in db.existing_verses:
        logger.info('Sending by file_id')
        msgverse = context.bot.send_video(
            chat_id=chat.id,
            video=db.get_fileid(verse),
            caption=db.get_versename(verse),
        )
        forward_to_channel(context.bot, chat.id, msgverse.message_id)
        return
    elif jw.filesize != db.filesize:
        logger.info('Lo descargo porque no lo tengo, o no coinciden filesize')
        context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
        context.user_data['msg'] = message.reply_text(
            f'📥 Descargando {jw.bookname} {jw.title_chapter}',
            disable_notification=True)
        db.path = Video.download(jw.video_url)
        db.discard_verses()
        db.save()
    if len(jw.verses) == 1:
        send_single_verse(update, context)
    else:
        send_concatenate_verses(update, context)
    logger.info('Success!')


def send_single_verse(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    jw = context.user_data['jw']
    db = context.user_data['db']
    msg = context.user_data['msg']
    verse = jw.verses[0]
 
    logger.info("Splitting verse %s from %s", verse, db.path)
    context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
    text = f'✂️🎞 Cortando {jw.bookname} {jw.chapter}:{verse}'
    if msg:
        msg.edit_text(text)
    else:
        msg = message.reply_text(text, disable_notification=True)

    versepath = Video.split(db.path, jw.match_marker(verse))
    stream = Video.show_streams(versepath)
    context.bot.send_chat_action(chat.id, ChatAction.UPLOAD_VIDEO_NOTE)
    msg.edit_text(f'📦 Enviando {jw.bookname} {jw.chapter}:{verse}')
    msgverse = context.bot.send_video(
        chat_id=chat.id,
        video=versepath.read_bytes(),
        filename=versepath.name,
        caption=jw.verse_name(verse),
        width=stream['width'],
        height=stream['height'],
        duration=round(float(stream['duration'])),
        timeout=120,
    )
    msg.delete()
    forward_to_channel(context.bot, chat.id, msgverse.message_id)
    versepath.unlink()
    db.add_verse(verse, jw.verse_name(verse), msgverse.video.file_id)
    db.save()


def send_concatenate_verses(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    jw = context.user_data['jw']
    db = context.user_data['db']
    msg = context.user_data['msg']
    versenums = ' '.join(jw.verses)

    paths_to_concatenate = []
    new = []
    for verse in jw.verses:
        context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
        if verse in db.existing_verses:
            logger.info('Downloading verse %s from telegram servers', verse)
            text = f'📥 Descargando {jw.bookname} {jw.chapter}:{verse}'
            if msg:
                msg.edit_text(text)
            else:
                msg = message.reply_text(text)
            file_id = db.get_fileid(verse)
            filename = db.get_versename(verse) + '.mp4'
            versepath = Path(filename)
            context.bot.get_file(file_id).download(custom_path=versepath)
            paths_to_concatenate.append(versepath)
        else:
            logger.info("Splitting verse %s from %s", verse, db.path)
            text = f'✂️🎞 Cortando {jw.bookname} {jw.chapter}:{verse}'
            if msg:
                msg.edit_text(text)
            else:
                msg = message.reply_text(text)
            marker = jw.match_marker(verse)
            versepath = Video.split(db.path, marker)
            paths_to_concatenate.append(versepath)
            new.append((verse, versepath))
    logger.info('Concatenating video %s', jw.pretty_name)
    msg.edit_text(f'🎥 Uniendo versículos...')
    finalpath = Video.concatenate(
        inputvideos=paths_to_concatenate,
        outname=safechars(jw.pretty_name),
        title_chapters=list(map(jw.verse_name, jw.verses)),
        title=jw.pretty_name,
    )
    logger.info('Sending concatenated video %s', finalpath)
    msg.edit_text(f'📦 Enviando {jw.pretty_name}')
    context.bot.send_chat_action(chat.id, ChatAction.UPLOAD_VIDEO_NOTE)
    stream = Video.show_streams(finalpath)
    msgverse = context.bot.send_video(
        chat_id=chat.id,
        video=finalpath.read_bytes(),
        filename=finalpath.name,
        caption=jw.pretty_name,
        width=stream['width'],
        height=stream['height'],
        duration=round(float(stream['duration'])),
        timeout=120,
    )
    msg.delete()
    forward_to_channel(context.bot, chat.id, msgverse.message_id)
    db.add_verse(
        verse=versenums,
        versename=jw.pretty_name,
        file_id=msgverse.video.file_id,
    )
    logger.info('Sending backup single verse %s', [verse for verse, _ in new])
    for verse, versepath in new:
        stream = Video.show_streams(versepath)
        msgverse = context.bot.send_video(
            chat_id=CHANNEL_ID,
            video=versepath.read_bytes(),
            filename=versepath.name,
            caption=jw.verse_name(verse),
            width=stream['width'],
            height=stream['height'],
            duration=round(float(stream['duration'])),
            timeout=120,
        )
        db.add_verse(
            verse=verse,
            versename=jw.verse_name(verse),
            file_id=msgverse.video.file_id,
        )
    for versepath in paths_to_concatenate + [finalpath]:
        versepath.unlink()
    db.save()


parse_bible_handler = MessageHandler(
    Filters.regex(re.compile(BIBLE_PATTERN, re.IGNORECASE)),
    parse_bible,
)
chapter_handler = CallbackQueryHandler(get_chapter, pattern=SELECTING_CHAPTERS)
verse_handler = CallbackQueryHandler(get_verse, pattern=SELECTING_VERSES)