
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

SELECTING_CHAPTERS, SELECTING_VERSES = range(2)
FORWARD_TO_CHANNEL = True


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
    _, booknum, chapter, verses = parse_bible_pattern(update.message.text.strip('/'))
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
    context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    jw = context.user_data['jw']
    chapters = jw.available_chapters()
    buttons = list_of_lists(
        [InlineKeyboardButton(chapter, callback_data=chapter)
         for chapter in chapters],
        columns=8
    )
    update.message.reply_text(
        f'*{jw.data["pubName"]}*\nElige un capítulo',
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN,
    )
    return SELECTING_CHAPTERS


def get_chapters(update: Update, context: CallbackContext):
    update.callback_query.answer()
    update.callback_query.message.delete()
    context.user_data['jw'].chapter = update.callback_query.data
    return show_verses(update, context)


def show_verses(update: Update, context: CallbackContext):
    message = update.message if update.message else update.callback_query.message
    context.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    jw = context.user_data['jw']
    verses = jw.available_verses()
    buttons = list_of_lists(
        [InlineKeyboardButton(verse, callback_data=verse) for verse in verses],
        columns=8
    )
    context.bot.send_message(
        chat_id=message.chat.id,
        text=f'*{jw.data["pubName"]} {jw.title}*\nElige un versículo',
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN,
    )
    return SELECTING_VERSES


def get_verses(update: Update, context: CallbackContext):
    update.callback_query.answer('Espera unos momentos')
    update.callback_query.message.delete()
    context.user_data['jw'].verses = [update.callback_query.data]
    return manage_verses(update, context)


def manage_verses(update: Update, context: CallbackContext):
    message = update.message if update.message else update.callback_query.message
    chat = update.callback_query.message.chat if update.callback_query else update.effective_chat
    jw = context.user_data['jw']
    db = LocalData(
        booknum=jw.booknum,
        chapter=jw.chapter,
        lang=jw.lang,
        quality=jw.quality,
    )
    context.user_data['db'] = db
    if jw.not_available_verses():
        na = jw.not_available_verses()
        message.reply_text(
            ('El siguiente versículo no está disponible:\n' if len(na) == 1 else
            'Los siguientes versículos no están disponibles:\n') +
            ' '.join(na)
        )
        return -1

    logger.info('(%s) %s', update.effective_user.name, f'{jw.booknum=} {jw.chapter=} {jw.verses}')
    logger.info('%s', f'{jw.filesize=} {db.filesize=}')
    if jw.filesize != db.filesize:
        logger.info('Lo descargo porque no lo tengo, o no coinciden filesize')
        context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
        db.path = Video.download(jw.video_url)
        db.discard_verses()
        db.save()

    verse = jw.verses[0] if len(jw.verses) == 1 else ' '.join(jw.verses)
    if verse in db.existing_verses:
        logger.info('Sending by file_id')
        msgverse = context.bot.send_video(
            chat_id=chat.id,
            video=db.get_fileid(verse),
            caption=db.get_versename(verse),
        )
        forward_to_channel(context.bot, chat.id, msgverse.message_id)
    elif len(jw.verses) == 1:
        send_single_verse(update, context)
    else:
        send_concatenate_verses(update, context)
    logger.info('Success!')
    return -1
    
def send_single_verse(update: Update, context: CallbackContext):
    chat = update.callback_query.message.chat if update.callback_query else update.effective_chat
    jw = context.user_data['jw']
    db = context.user_data['db']
    verse = jw.verses[0]
 
    logger.info("Splitting verse %s from %s", verse, db.path)
    context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
    versepath = Video.split(db.path, jw.match_marker(verse))
    stream = Video.show_streams(versepath)
    context.bot.send_chat_action(chat.id, ChatAction.UPLOAD_VIDEO_NOTE)
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
    forward_to_channel(context.bot, chat.id, msgverse.message_id)
    versepath.unlink()
    db.add_verse(verse, jw.verse_name(verse), msgverse.video.file_id)
    db.save()
    return -1


def send_concatenate_verses(update: Update, context: CallbackContext):
    chat = update.callback_query.message.chat if update.callback_query else update.effective_chat
    jw = context.user_data['jw']
    db = context.user_data['db']
    versenums = ' '.join(jw.verses)

    paths_to_concatenate = []
    new = []
    for verse in jw.verses:
        context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
        if verse in db.existing_verses:
            logger.info('Downloading verse %s from telgram servers', verse)
            file_id = db.get_fileid(verse)
            filename = db.get_versename(verse) + '.mp4'
            versepath = Path(filename)
            context.bot.get_file(file_id).download(custom_path=versepath)
            paths_to_concatenate.append(versepath)
        else:
            logger.info("Splitting verse %s from %s", verse, db.path)
            marker = jw.match_marker(verse)
            versepath = Video.split(db.path, marker)
            paths_to_concatenate.append(versepath)
            new.append((verse, versepath))
    logger.info('Concatenating video %s', jw.pretty_name)
    finalpath = Video.concatenate(
        inputvideos=paths_to_concatenate,
        outname=safechars(jw.pretty_name),
        title_chapters=list(map(jw.verse_name, jw.verses)),
        title=jw.pretty_name,
    )
    logger.info('Sending concatenated video %s', finalpath)
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
    return -1


parse_handler = ConversationHandler(
    entry_points=[
        CommandHandler(BIBLE_BOOKALIAS_NUM.keys(), parse_bible),
        MessageHandler(
            Filters.regex(re.compile(BIBLE_PATTERN, re.IGNORECASE)),
            parse_bible,
        )
    ],
    states={
        SELECTING_CHAPTERS: [CallbackQueryHandler(get_chapters)],
        SELECTING_VERSES: [CallbackQueryHandler(get_verses)]
    },
    allow_reentry=True,
    fallbacks=[CommandHandler('cancel', lambda u, c: -1)],
)
