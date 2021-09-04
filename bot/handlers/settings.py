import logging
from math import ceil
import sys

from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.message import Message
import telegram.error

from models import JWInfo, JWBible, UserController

from utils import list_of_lists
from utils.decorators import vip, forw


logger = logging.getLogger(__name__)

SETTING_LANG, SETTING_QUALITY = range(2)
SELECTING_LANGUAGE = 'LANG'
PAGE = 'PAGE'


@forw
@vip
def manage_langs(update: Update, context: CallbackContext) -> int:
    uc = UserController(update.message.from_user.id)

    if context.args:
        return set_lang(update, context)
    info_for_buttons = context.user_data['info_for_buttons'] = list_of_lists(
        [{
            'text': f'{lang["code"]} - {lang["vernacular"]}' +
                    ('' if lang['name'] == lang['vernacular'] else ' - ' + " ".join(lang["name"].split()[3:])),
            'callback_data': f'{SELECTING_LANGUAGE}|{lang["code"]}'
        } for lang in sorted(JWInfo.get_signs_languages(), key=lambda x: x['code'])
        ],
        columns=1
    )
    send_buttons(
        message=update.message,
        info_for_buttons=info_for_buttons,
        text=f'Tu lengua actual es {uc.get_lang()}\nEscoge una lengua de señas.',
    )
    return

def send_buttons(message: Message, info_for_buttons, page: int=1, text: str=None, max_buttons: int=12):
    """Generic function to split large data into inlinekeyboard pages"""
    if text is None:
        text = message.text
    buttons = []
    data = info_for_buttons[(page - 1) * max_buttons:page * max_buttons]
    if not data:
        return
    for row in data:
        buttons.append([InlineKeyboardButton(**kwargs) for kwargs in row])
    buttons.append([
        InlineKeyboardButton('◀️', callback_data=f'{PAGE}|{page - 1}'),
        InlineKeyboardButton(f'{page}/{ceil( len(info_for_buttons) / max_buttons)}', callback_data='None'),
        InlineKeyboardButton('▶️', callback_data=f'{PAGE}|{page + 1}')
    ])
    kwargs = {'text': text, 'reply_markup': InlineKeyboardMarkup(buttons)}
    try:
        message.edit_text(**kwargs)
    except telegram.error.BadRequest:
        message.reply_text(**kwargs)
    return

def mediator_page(update: Update, context: CallbackContext):
    send_buttons(
        message=update.effective_message,
        info_for_buttons=context.user_data['info_for_buttons'],
        page=int(update.callback_query.data.strip(f'{PAGE}|')),
    )

def set_lang(update: Update, context: CallbackContext) -> int:
    if update.callback_query:
        valid_code = update.callback_query.data.split('|')[1]
        del context.user_data['info_for_buttons']
    elif context.args:
        valid_code = next((lang['code'] for lang in JWInfo.get_signs_languages() if lang['code'].upper() == context.args[0].upper()), None)
        if valid_code is None:
            update.message.reply_text('No he reconocido ese idioma')
            return
    vern = next((lang['vernacular'] for lang in JWInfo.get_signs_languages() if lang['code'] == valid_code), '')
    UserController.set_user(
        telegram_id=update.effective_user.id,
        lang=valid_code,
    )
    text = f'Lengua cambiada a {valid_code} - {vern}'
    if update.callback_query:
        update.effective_message.edit_text(text)
    else:
        update.effective_message.reply_text(text)


@forw
@vip
def get_quality(update: Update, context: CallbackContext) -> int:
    lang = UserController(update.effective_user.id).get_lang()
    jw = JWBible(code_lang=lang, booknum=49)
    qualities = jw.available_qualities
    args = update.message.text.split()[1:]
    quality = args[0] if args else update.message.text
    if quality in qualities:
        context.user_data['quality'] = quality
        UserController.set_user(update.message.from_user.id, quality=quality)
        update.message.reply_markdown_v2(
            f'Calidad configurada a\n```\n{quality}\n```', reply_markup=ReplyKeyboardRemove())
        return -1
    elif quality == '/quality':
        buttons = list_of_lists(
            [KeyboardButton(q) for q in qualities],
            columns=2,
        )
        uc = UserController(update.message.from_user.id)
        text = (f'Tu calidad actual es {uc.get_quality()}\n'
                'Elige una calidad para los videos')
        update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(buttons))
        return SETTING_QUALITY
    else:
        update.message.reply_text(
            f'No he reconocido esa calidad.')
        return -1



showlangs_handler = CommandHandler('lang', manage_langs)
setlang_handler = CallbackQueryHandler(set_lang, pattern=SELECTING_LANGUAGE)
pagelang_handler = CallbackQueryHandler(mediator_page, pattern=PAGE)
quality_handler = ConversationHandler(
    entry_points=[CommandHandler('quality', get_quality)],
    states={SETTING_QUALITY: [MessageHandler(Filters.text, get_quality)]},
    fallbacks=[CommandHandler('cancel', lambda x, y: -1)],

)
