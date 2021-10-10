from pathlib import Path
import logging
import json

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

from bot import CHANNEL_ID
from bot import ADMIN
from bot.jw.jwpubmedia import JWBible
from bot.utils import video
from bot.database import start_database
from bot.database import localdatabase as db
from bot.database.schemedb import SentVerse, Language
from bot.utils import BIBLE_BOOKALIAS_NUM
from bot.utils import list_of_lists
from bot.utils import safechars
from bot.utils import parse_bible_pattern
from bot.utils import seems_bible
from bot.utils import BooknumNotFound
from bot.utils import MultipleBooknumsFound
from bot.utils.decorators import vip, forw, log


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

FORWARD_TO_CHANNEL = True
SELECTING_CHAPTERS, SELECTING_VERSES = '0', '1'


def forward_to_channel(bot, from_chat_id, message_id):
    if FORWARD_TO_CHANNEL and from_chat_id != ADMIN:
        bot.forward_message(
            CHANNEL_ID,
            from_chat_id=from_chat_id,
            message_id=message_id,
        )

def fallback_text(update: Update, context: CallbackContext):
    pass


@vip
def parse_lang_bible(update: Update, context: CallbackContext) -> None:
    lang_code = update.message.text.split()[0].strip('/').upper()
    query_bible = ' '.join(update.message.text.split()[1:])
    parse_bible(update, context, query_bible=query_bible, lang_code=lang_code)
    return


@vip
@forw
def parse_bible(update: Update, context: CallbackContext, query_bible=None, lang_code=None) -> None:
    reply_text = update.message.reply_text
    text = query_bible or update.message.text.strip('/')
    try:
        booknum, chapter, verses = parse_bible_pattern(text)
    except BooknumNotFound:
        logger.info('BooknumNotFound')
        if seems_bible(text):
            reply_text('🧐 Uhm... no conozco ese libro de la Biblia')
        else:
            fallback_text(update, context)
        return
    except MultipleBooknumsFound as e:
        # TODO
        logger.info('MultipleBooknumsFound')
        reply_text(f'Los sisguientes libros coinciden {e}')
        # maybe = [
        #     f'{BIBLE_BOOKNAMES[booknum - 1]} - /{bookalias}'
        #     for bookalias, booknum in BIBLE_BOOKALIAS_NUM.items()
        #     if str(booknum) in e.booknums
        # ]
        # reply_text('¿Quizá quieres decir... 🤔?\n\n' + '\n'.join(maybe))
        return

    lang_code = lang_code or db.get_user(update.effective_user.id).lang_code
    if not lang_code:
        reply_text('Primero debes elegir una lengua de señas /signlanguage')
        return

    context.user_data['msg'] = None
    jw = JWBible(lang_code, booknum, chapter, verses)
    kwargs = context.user_data['kwargs'] = {
        'lang_code': lang_code,
        'booknum': booknum,
        'chapter': chapter,
        'verses': verses,
        'raw_verses': ' '.join(str(v) for v in verses),
        'telegram_user_id': update.effective_user.id
    }

    if jw.chapter and jw.pubmedia_exists() and not jw.check_chapternumber():
        reply_text(f'El capítulo {jw.chapter} de {jw.bookname} no está disponible 🤷🏻‍♂️ pero puedes probar con otro capítulo')
        kwargs.update({'chapter': None})
        return show_chapters(update, context)

    if not jw.pubmedia_exists():
        reply_text(f'Este libro no está disponible en {lang_code}. Usa /lang para cambiar la lengua de señas')
        return

    kwargs.update({
        'quality': jw.get_best_quality(),
        'bookname': jw.bookname,
    })
    logger.info('%s', json.dumps(context.user_data['kwargs'], indent=2, ensure_ascii=False))
    db.query_or_create_bible_book(**context.user_data['kwargs'])

    if chapter:
        kwargs.update({
            'checksum': jw.get_checksum(),
        })
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
    buttons = list_of_lists(
        [InlineKeyboardButton(
            str(chapter),
            callback_data=f'{SELECTING_CHAPTERS}|{jw.lang.code}|{jw.booknum}|{chapter}|{jw.get_checksum(chapter)}',
        ) for chapter in jw.get_all_chapternumber()],
        columns=8
    )
    kwargs = {
        'chat_id': update.effective_chat.id,
        'text': f'{jw.lang.code}\n📖 {jw.bookname}\nElige un capítulo',
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': ParseMode.MARKDOWN,
    }
    context.user_data['msg'] = context.bot.edit_message_text(**kwargs) if update.callback_query else context.bot.send_message(**kwargs)
    delete_objects(update, context)


@log
def get_chapter(update: Update, context: CallbackContext):
    _, lang_code, booknum, chapter, checksum = update.callback_query.data.split('|')
    context.user_data['kwargs'] = {
        'lang_code': lang_code,
        'booknum': booknum,
        'chapter': chapter,
        'checksum': checksum
    }
    jw = JWBible(**context.user_data['kwargs'])
    db.manage_video_markers(jw.get_markers, **context.user_data['kwargs'])
    update.callback_query.answer()
    show_verses(update, context)


def show_verses(update: Update, context: CallbackContext):
    jw = JWBible(**context.user_data['kwargs'])
    bible_chapter = db.get_bible_chapter(**context.user_data['kwargs'])

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
        'text': f'{jw.lang.code}\n📖 {jw.bookname} {jw.booknum}\nElige un versículo',
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': ParseMode.MARKDOWN,
    }
    if message_id:
        context.bot.edit_message_text(message_id=message_id, **kwargs)
    else:
        context.bot.send_message(**kwargs)
    delete_objects(update, context)



@log
def get_verse(update: Update, context: CallbackContext):
    update.callback_query.answer()
    _, lang_code, booknum, chapter, checksum, verse = update.callback_query.data.split('|')
    context.user_data['kwargs'] = {
        'lang_code': lang_code,
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
    kwargs = context.user_data['kwargs']
    jw = context.user_data['jw'] = JWBible(**kwargs)
    kwargs.update(dict(quality=jw.get_best_quality()))
    logger.info('%s', json.dumps(kwargs, indent=2, ensure_ascii=False))
    logger.info('(%s) %s', update.effective_user.name, jw.citation())

    not_available = [verse for verse in kwargs['verses'] if int(verse) not in db.get_all_versenumbers(**kwargs)]
    if len(not_available) == 1:
        text = f'{not_available[0]} no está disponible.'
    elif len(not_available) > 1:
        text = f'{", ".join([str(i) for i in not_available])} no están disponibles.'
    if not_available:
        update.message.reply_text(
            f'{jw.bookname} {jw.chapter}:{text}\nPero puedes elegir uno de los siguientes versículos:'
        )
        show_verses(update, context)
        return

    sent_verse = db.query_sent_verse(**kwargs)
    if sent_verse and sent_verse.raw_verses == ' '.join(str(v) for v in kwargs['verses']):
        send_by_fileid(update, context, sent_verse)
        return

    if len(jw.verses) == 1:
        send_single_verse(update, context)
    else:
        send_concatenate_verses(update, context)
    logger.info('Success!')
    delete_objects(update, context)
    return


def send_by_fileid(update: Update, context: CallbackContext, sent_verse: SentVerse):
    logger.info('Sending by file_id')
    if context.user_data.get('msg'):
        context.user_data.get('msg').delete()
    try:
        msgverse = context.bot.send_video(
            chat_id=update.effective_chat.id,
            video=sent_verse.telegram_file_id,
            caption=sent_verse.citation,
        )
    except TelegramError:
        logger.critical('Al parecer se ha eliminado de los servidores de Telegram %s file_id=%s', sent_verse.citation, sent_verse.telegram_file_id)

    else:
        db.add_sent_verse_user(sent_verse, update.effective_user.id)
        forward_to_channel(context.bot, update.effective_chat.id, msgverse.message_id)
    return


def send_single_verse(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    jw = context.user_data['jw']
    msg = context.user_data.get('msg')
    verse = str(jw.verses[0])
    citation = f'{jw.bookname} {jw.chapter}:{verse}'
    logger.info("Splitting %s", citation)
    text = f'✂️🎞 Cortando {citation}'
    if msg:
        msg.edit_text(text)
    else:
        msg = message.reply_text(text, disable_notification=True)
    context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
    marker = db.get_videomarker(versenum=verse, **context.user_data['kwargs'])
    versepath = video.split(jw.get_video_url(), marker)
    streams = video.show_streams(versepath)
    context.bot.send_chat_action(chat.id, ChatAction.UPLOAD_VIDEO_NOTE)
    msg.edit_text(f'📦 Enviando {citation}')
    msgverse = context.bot.send_video(
        chat_id=chat.id,
        video=versepath.read_bytes(),
        filename=versepath.name,
        caption=citation,
        width=streams['width'],
        height=streams['height'],
        duration=round(float(streams['duration'])),
        timeout=120,
        # thumb= TODO
    )
    msg.delete()
    forward_to_channel(context.bot, chat.id, msgverse.message_id)
    context.user_data['kwargs'].update({
        'citation': citation,
        'telegram_file_id': msgverse.video.file_id,
        'size': versepath.stat().st_size,
        'verses': verse,
    })
    sent_verse = db.add_sent_verse(**context.user_data['kwargs'])
    db.add_sent_verse_user(sent_verse, update.effective_user.id)
    # TODO
    # CommandsScope por lenguaje
    versepath.unlink()


def send_concatenate_verses(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    jw = context.user_data['jw']
    kwargs = context.user_data['kwargs']
    msg = context.user_data.get('msg')
    raw_verses = ' '.join([str(v) for v in jw.verses])

    paths_to_concatenate = []
    new = []
    for verse in jw.verses:
        kwargs.update({'raw_verses': str(verse)})
        sent_verse = db.query_sent_verse(**kwargs)
        if sent_verse:
            logger.info('Downloading verse %s from telegram servers', sent_verse.citation)
            text = f'📥 Obteniendo {sent_verse.citation}'
            if msg:
                msg.edit_text(text)
            else:
                msg = message.reply_text(text)
            versepath = Path(f'{sent_verse.id}.mp4')
            context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
            context.bot.get_file(sent_verse.telegram_file_id, timeout=120).download(custom_path=versepath)
            paths_to_concatenate.append(versepath)
        else:
            citation = f'{jw.bookname} {jw.chapter}:{verse}'
            logger.info("Splitting %s", citation)
            text = f'✂️🎞 Cortando {citation}'
            if msg:
                msg.edit_text(text)
            else:
                msg = message.reply_text(text)
            context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
            marker = db.get_videomarker(versenum=verse, **context.user_data['kwargs'])
            versepath = video.split(jw.get_video_url(), marker)
            paths_to_concatenate.append(versepath)
            new.append((verse, versepath))
    logger.info('Concatenating video %s', jw.citation())
    msg.edit_text(f'🎥 Uniendo versículos')
    finalpath = video.concatenate(
        inputvideos=paths_to_concatenate,
        outname=f'{jw.lang_code} - {safechars(jw.citation())} - {jw.get_best_quality()}',
        title_chapters=list(map(jw.citation, jw.verses)),
        title=jw.citation(),
    )
    logger.info('Sending concatenated video %s', finalpath)
    msg.edit_text(f'📦 Enviando {jw.citation()}')
    context.bot.send_chat_action(chat.id, ChatAction.UPLOAD_VIDEO_NOTE)
    stream = video.show_streams(finalpath)
    msgverse = context.bot.send_video(
        chat_id=chat.id,
        video=finalpath.read_bytes(),
        filename=finalpath.name,
        caption=jw.citation(),
        width=stream['width'],
        height=stream['height'],
        duration=round(float(stream['duration'])),
        timeout=120,
        # thumb= TODO
    )
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
    logger.info('Sending backup single verse %s', [verse for verse, _ in new])
    for verse, versepath in new:
        stream = video.show_streams(versepath)
        msgverse = context.bot.send_video(
            chat_id=CHANNEL_ID,
            video=versepath.read_bytes(),
            filename=versepath.name,
            caption=jw.citation(verses=verse),
            width=stream['width'],
            height=stream['height'],
            duration=round(float(stream['duration'])),
            timeout=120,
            # thumb= TODO
        )
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


LANGCODES = [
        lang[0] for lang in
        start_database().query(Language.code)
        .filter(Language.is_sign_lang == True)
        .all()
    ]

parse_bible_re_handler = MessageHandler(Filters.text, parse_bible)
parse_bible_cmd_handler = CommandHandler([*BIBLE_BOOKALIAS_NUM], parse_bible)
chapter_handler = CallbackQueryHandler(get_chapter, pattern=SELECTING_CHAPTERS)
verse_handler = CallbackQueryHandler(get_verse, pattern=SELECTING_VERSES)
parse_lang_bible_handler = CommandHandler(LANGCODES, parse_lang_bible)
