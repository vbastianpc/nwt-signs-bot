from pathlib import Path
import logging

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
    Filters,
)

from models import JWBible, LocalData, Video, UserController
from utils import (
    BIBLE_BOOKALIAS_NUM,
    BIBLE_BOOKNAMES,
    list_of_lists,
    safechars,
    parse_bible_pattern,
    seems_bible,
    BooknumNotFound,
    MultipleBooknumsFound,
)
from utils.decorators import vip, forw, log
from utils.secret import CHANNEL_ID, ADMIN


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

FORWARD_TO_CHANNEL = True
SELECTING_CHAPTERS, SELECTING_VERSES = 'CHAPTER', 'VERSE'


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
@forw
def parse_bible(update: Update, context: CallbackContext):
    logger.info(update.message.text)
    text = update.message.text.strip('/')
    reply_text = update.message.reply_text
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
        logger.info('MultipleBooknumsFound')
        maybe = [
            f'{BIBLE_BOOKNAMES[booknum - 1]} - /{bookalias}'
            for bookalias, booknum in BIBLE_BOOKALIAS_NUM.items()
            if str(booknum) in e.booknums
        ]
        reply_text('¿Quizá quieres decir... 🤔?\n\n' + '\n'.join(maybe))
        return

    uc = UserController(update.effective_user.id)
    jw = JWBible(uc.get_lang(), uc.get_quality(), booknum, chapter, verses)
    context.user_data['kwargs'] = {
        'code_lang': uc.get_lang(),
        'quality': uc.get_quality(),
        'booknum': booknum,
        'chapter': chapter,
        'verses': verses,
    }
    context.user_data['msg'] = None

    if not jw.pubmedia_exists():
        reply_text(f'No está disponible en {uc.get_lang()}. Prueba con otro libro, o cambia la lengua con /lang')
        return

    if jw.chapter and jw.chapter not in jw.available_chapters:
        reply_text(f'El capítulo {jw.chapter} de {jw.bookname} no está disponible 🤷🏻‍♂️ pero puedes probar con otro capítulo')
        return show_chapters(update, context)
    
    if uc.get_quality() not in jw.available_qualities:
        reply_text(
            f'{jw.bookname} no está disponible en {jw.quality}.\n\nUsa /quality '
            'y elige una de las siguientes calidades disponibles:\n\n' + 
            '\n'.join(jw.available_qualities)
        )
        return

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
            callback_data=f'{SELECTING_CHAPTERS}||{jw.code_lang}||{jw.quality}||{jw.booknum}||{chapter}',
        ) for chapter in jw.available_chapters],
        columns=8
    )
    kwargs = {
        'chat_id': update.effective_chat.id,
        'text': f'📖 *{jw.bookname}*\nElige un capítulo',
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': ParseMode.MARKDOWN,
    }
    context.user_data['msg'] = context.bot.edit_message_text(**kwargs) if update.callback_query else context.bot.send_message(**kwargs)


@log
def get_chapter(update: Update, context: CallbackContext):
    update.callback_query.answer()
    _, code_lang, quality, booknum, chapter = update.callback_query.data.split('||')
    context.user_data.setdefault('kwargs', {}).update({
        'code_lang': code_lang,
        'quality': quality,
        'booknum': booknum,
        'chapter': chapter,
    })
    show_verses(update, context)


def show_verses(update: Update, context: CallbackContext):
    message = update.effective_message
    db = LocalData(**context.user_data['kwargs'])
    context.user_data['kwargs'].update({'videopath': db.path})
    jw = JWBible(**context.user_data['kwargs'])
    msg = context.user_data.get('msg')

    if not jw.is_wol_available() and jw.checksum != db.checksum:
        if db.checksum:
            context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f'Se ha actualizado {jw.bookname} {jw.chapter} con fecha {jw.modifiedDatetime}',
            )
        text = f'📥 Descargando {jw.bookname} {jw.chapter}'
        msg = context.user_data['msg'] = msg.edit_text(text) if msg else message.reply_text(text)
        download_chapter(jw, db)
    buttons = list_of_lists(
        [InlineKeyboardButton(
            str(verse),
            callback_data=f'{SELECTING_VERSES}||{jw.code_lang}||{jw.quality}||{jw.booknum}||{jw.chapter}||{verse}',
        ) for verse in jw.available_verses],
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
        return
    if context.user_data.get('msg'):
        context.bot.edit_message_text(
            message_id=context.user_data['msg'].message_id,
            **kwargs,
        )
    else:
        context.bot.send_message(**kwargs)


@log
def get_verse(update: Update, context: CallbackContext):
    update.callback_query.answer('Espera unos momentos')
    _, code_lang, quality, booknum, chapter, verse = update.callback_query.data.split('||')
    context.user_data['kwargs'].update({
        'code_lang': code_lang,
        'quality': quality,
        'booknum': booknum,
        'chapter': chapter,
        'verses': [verse]
    })
    context.user_data['msg'] = update.callback_query.message
    logger.info(f'Recibido: {code_lang} {quality} {booknum} {chapter} {verse}')
    return manage_verses(update, context)


def manage_verses(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    db = context.user_data['db'] = LocalData(**context.user_data['kwargs'])
    context.user_data['kwargs'].update({'videopath': db.path})
    jw = context.user_data['jw'] = JWBible(**context.user_data['kwargs'])
    msg = context.user_data.get('msg')
    logger.info('(%s) %s', update.effective_user.name, f'{jw.booknum} {jw.chapter} {jw.verses}')

    verse = str(jw.verses[0]) if len(jw.verses) == 1 else ' '.join([str(v) for v in jw.verses])

    if jw.checksum != db.checksum:
        if db.checksum:
            context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=f'Se ha actualizado {jw.bookname} {jw.chapter} con fecha {jw.modifiedDatetime}',
            )
        text = f'📥 Descargando {jw.bookname} {jw.chapter}'
        msg = context.user_data['msg'] = msg.edit_text(text) if msg else message.reply_text(text)
        download_chapter(jw, db)

    if verse in db.existing_verses:
        if msg:
            msg.delete()
        logger.info('Sending by file_id')
        msgverse = context.bot.send_video(
            chat_id=chat.id,
            video=db.get_fileid(verse),
            caption=db.get_versename(verse),
        )
        forward_to_channel(context.bot, chat.id, msgverse.message_id)
        return

    if jw.not_available_verses:
        na = jw.not_available_verses
        message.reply_text(
            f'{jw.bookname} {jw.chapter}:' + 
            (f'{na[0]} no está disponible 🤷🏻‍♂️' if len(na) == 1 else f'{", ".join([str(i) for i in na])} no están disponibles 🤷🏻‍♂️')
        )
        return

    if len(jw.verses) == 1:
        send_single_verse(update, context)
    else:
        send_concatenate_verses(update, context)
    logger.info('Success!')
    return delete_objects(update, context)


def download_chapter(jw: JWBible, db: LocalData):
    logger.info(f'Descargando {jw.bookname} {jw.chapter}')
    db.path = Video.download(jw.video_url)
    db.discard_verses()
    jw.videopath = db.path
    db.save(jw.checksum, jw.modifiedDatetime, jw.filesize)


def send_single_verse(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    jw = context.user_data['jw']
    db = context.user_data['db']
    msg = context.user_data.get('msg')
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
    msg.edit_text(f'📦 Enviando {jw.citation()}')
    msgverse = context.bot.send_video(
        chat_id=chat.id,
        video=versepath.read_bytes(),
        filename=versepath.name,
        caption=jw.citation(),
        width=stream['width'],
        height=stream['height'],
        duration=round(float(stream['duration'])),
        timeout=120,
        # thumb= TODO
    )
    msg.delete()
    forward_to_channel(context.bot, chat.id, msgverse.message_id)
    versepath.unlink()
    db.add_verse(verse, jw.citation(), msgverse.video.file_id)
    db.save(jw.checksum, jw.modifiedDatetime, jw.filesize)


def send_concatenate_verses(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    jw = context.user_data['jw']
    db = context.user_data['db']
    msg = context.user_data.get('msg')
    versenums = ' '.join([str(v) for v in jw.verses])

    paths_to_concatenate = []
    new = []
    for verse in jw.verses:
        context.bot.send_chat_action(chat.id, ChatAction.RECORD_VIDEO_NOTE)
        if str(verse) in db.existing_verses:
            logger.info('Downloading verse %s from telegram servers', verse)
            text = f'📥 Obteniendo {jw.bookname} {jw.chapter}:{verse}'
            if msg:
                msg.edit_text(text)
            else:
                msg = message.reply_text(text)
            file_id = db.get_fileid(verse)
            filename = db.get_versename(verse) + '.mp4'
            versepath = Path(filename)
            context.bot.get_file(file_id, timeout=120).download(custom_path=versepath)
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
    logger.info('Concatenating video %s', jw.citation())
    msg.edit_text(f'🎥 Uniendo versículos')
    finalpath = Video.concatenate(
        inputvideos=paths_to_concatenate,
        outname=safechars(jw.citation()),
        title_chapters=list(map(jw.citation, jw.verses)),
        title=jw.citation(),
    )
    logger.info('Sending concatenated video %s', finalpath)
    msg.edit_text(f'📦 Enviando {jw.citation()}')
    context.bot.send_chat_action(chat.id, ChatAction.UPLOAD_VIDEO_NOTE)
    stream = Video.show_streams(finalpath)
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
    db.add_verse(
        verse=versenums,
        versename=jw.citation(),
        file_id=msgverse.video.file_id,
    )
    logger.info('Sending backup single verse %s', [verse for verse, _ in new])
    for verse, versepath in new:
        stream = Video.show_streams(versepath)
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
        db.add_verse(
            verse=verse,
            versename=jw.citation(verses=verse),
            file_id=msgverse.video.file_id,
        )
    for versepath in paths_to_concatenate + [finalpath]:
        versepath.unlink()
    db.save(jw.checksum, jw.modifiedDatetime, jw.filesize)

def delete_objects(update: Update, context: CallbackContext):
    context.user_data.pop('jw', None)
    context.user_data.pop('db', None)
    context.user_data.pop('kwargs', None)
    context.user_data.pop('msg', None)


parse_bible_re_handler = MessageHandler(Filters.text, parse_bible)
parse_bible_cmd_handler = CommandHandler([*BIBLE_BOOKALIAS_NUM], parse_bible)
chapter_handler = CallbackQueryHandler(get_chapter, pattern=SELECTING_CHAPTERS)
verse_handler = CallbackQueryHandler(get_verse, pattern=SELECTING_VERSES)
