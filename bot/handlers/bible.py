
import os
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
from jw_pubmedia import (
    get_bibleBookChapters,
    get_filesize,
    get_jw_data,
    get_marker,
    get_url_file,
    get_verseNumbers,
    is_available,
    get_title,
)
from local_jw import (
    download_video,
    get_entry_local_jw,
    save_local_jw,
    split_video,
)
from utils import (
    BIBLE_BOOKALIAS_NUM,
    BIBLE_NUM_BOOKALIAS,
    list_of_lists,
    BIBLE_PATTERN,
    parse_bible_pattern,
)
from decorators import vip, forw
from users import get_user_quality, get_user_lang
from secret import CHANNEL_ID

# logging.basicConfig(
#     format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s', level=logging.INFO
# )

logger = logging.getLogger(__name__)

SELECTING_CHAPTERS, SELECTING_VERSES = range(2)


@forw
@vip
def parse_bible(update: Update, context: CallbackContext):
    book_alias, booknum, chapter, verses = parse_bible_pattern(update.message.text.strip('/'))
    ud = context.user_data
    ud['quality'] = get_user_quality(update.message.from_user.id)
    ud['lang'] = get_user_lang(update.message.from_user.id)
    ud['bible'] = [booknum, chapter, verses]
    logger.info("(%s) %s %s", update.effective_user.name, book_alias, ud['bible'])
    ud['jw'] = get_jw_data(booknum, lang=ud['lang'])

    if verses:
        return send_video(update, context)
    if chapter:
        return show_verses(update, context)
    if not chapter:
        return show_chapters(update, context)

def show_chapters(update: Update, context: CallbackContext):
    context.bot.send_chat_action(update.message.chat.id, ChatAction.TYPING)
    ud = context.user_data
    chapters = get_bibleBookChapters(
        context.user_data['jw'],
        lang=ud['lang'],
        label=ud['quality']
    )
    buttons = list_of_lists(
        [InlineKeyboardButton(chapter, callback_data=chapter)
         for chapter in chapters],
        columns=8
    )
    update.message.reply_text(
        f'*{ud["jw"]["pubName"]}*\nElige un capítulo',
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN,
    )
    return SELECTING_CHAPTERS


def get_chapters(update: Update, context: CallbackContext):
    update.callback_query.answer()
    ud = context.user_data
    update.callback_query.message.delete()
    chapter = update.callback_query.data
    ud['bible'][1] = chapter
    return show_verses(update, context)


def show_verses(update: Update, context: CallbackContext):
    message = update.message if update.message else update.callback_query.message
    context.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    ud = context.user_data
    chapter = ud['bible'][1]
    verses = get_verseNumbers(ud['jw'], chapter, lang=ud['lang'])
    buttons = list_of_lists(
        [InlineKeyboardButton(verse, callback_data=verse) for verse in verses],
        columns=8
    )
    context.bot.send_message(
        chat_id=message.chat.id,
        text=f'*{ud["jw"]["pubName"]} {get_title(ud["jw"], chapter, ud["lang"])}*\nElige un versículo',
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN,
    )
    return SELECTING_VERSES


def get_verses(update: Update, context: CallbackContext):
    update.callback_query.answer('Espera unos momentos')
    ud = context.user_data
    update.callback_query.message.delete()
    verses = [update.callback_query.data]
    ud['bible'][2] = verses
    return send_video(update, context)


def send_video(update: Update, context: CallbackContext):
    message = update.message if update.message else update.callback_query.message
    chat = update.callback_query.message.chat if update.callback_query else update.effective_chat
    ud = context.user_data
    booknum, chapter, verses = ud['bible']
    if not is_available(ud['jw'], chapter, verses, ud['lang'], ud['quality']):
        message.reply_text('Ese video no está disponible')
        return -1
    url = get_url_file(ud['jw'], chapter, ud['lang'], ud['quality'])
    db = get_entry_local_jw(booknum, chapter, ud['lang'], ud['quality'])
    server_filesize = get_filesize(
        ud['jw'], chapter, ud['lang'], ud['quality'])
    local_filesize = os.stat(
        db['file']).st_size if os.path.isfile(db['file']) else 0
    logger.info('(%s) %s', update.effective_user.name, ud['bible'])
    for verse in verses:
        marker = get_marker(ud['jw'], chapter, verse, ud['lang'])
        if server_filesize == db['filesize'] and verse in db['verses']:
            logger.info('Te lo reenvío. Easy')
            msgverse = context.bot.send_video(chat.id, db['verses'][verse]['file_id'])
            context.bot.forward_message(CHANNEL_ID, chat.id, msgverse.message_id)
            continue
        if server_filesize != local_filesize:
            logger.info('Lo descargo porque no lo tengo, o no coinciden filesize')
            context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
            nwt_video_path = download_video(url)
            db['file'] = nwt_video_path
            db['filesize'] = os.stat(nwt_video_path).st_size
        context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
        versepath = split_video(db['file'], marker)
        context.bot.send_chat_action(chat.id, ChatAction.UPLOAD_VIDEO_NOTE)
        msgverse = context.bot.send_video(chat.id, open(versepath, 'rb'))
        context.bot.forward_message(CHANNEL_ID, chat.id, msgverse.message_id)
        os.remove(versepath)
        db['verses'][verse] = {
            'file_id': msgverse.video.file_id, 'name': marker['label']}
    logger.info('Hecho')
    save_local_jw(db, booknum, chapter, ud['lang'], ud['quality'])
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
    fallbacks=[CommandHandler('cancel', lambda x, y: -1)],
)
