import logging
from math import ceil
from uuid import uuid4
import time

from telegram import Update
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import CallbackQueryHandler
from telegram.message import Message
import telegram.error

from bot.jw.jwlanguage import JWLanguage
from bot.database import localdatabase as db
from bot.database import report as rdb
from bot.utils import list_of_lists
from bot.utils.decorators import vip, forw


logger = logging.getLogger(__name__)

SETTING_LANG, SETTING_QUALITY = range(2)
SELECTING_LANGUAGE = 'LANG'
PAGE = 'PAGE'


@forw
@vip
def manage_langs(update: Update, context: CallbackContext):
    if context.args:
        set_lang(update, context)
    else:
        generate_lang_buttons(update, context)


def button_info():
    return list_of_lists(
        [{
            'text': f'{sign_language.code} - {sign_language.vernacular}',
            'callback_data': f'{SELECTING_LANGUAGE}|{sign_language.code}'
        } for sign_language in db.get_sign_languages()
        ],
        columns=1
    )


def generate_lang_buttons(update: Update, context: CallbackContext):
    text = f'🧏‍♂️ <b>Escoge una lengua de señas</b>\n🌎 Total: <b>{rdb.count_signlanguage()}</b>'
    send_buttons(
        message=update.message,
        info_for_buttons=button_info(),
        text=text,
    )


def send_buttons(message: Message, info_for_buttons, page: int=1, text: str=None, max_buttons: int=10):
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
    kwargs = {'text': text, 'reply_markup': InlineKeyboardMarkup(buttons), 'parse_mode': ParseMode.HTML}
    try:
        message.edit_text(**kwargs)
    except telegram.error.BadRequest:
        message.reply_text(**kwargs)
    return


def mediator_page(update: Update, context: CallbackContext):
    send_buttons(
        message=update.effective_message,
        info_for_buttons=button_info(),
        page=int(update.callback_query.data.strip(f'{PAGE}|')),
    )


def set_lang(update: Update, context: CallbackContext) -> int:
    lang = JWLanguage()
    if update.callback_query:
        lang.code = update.callback_query.data.split('|')[1]
    elif context.args:
        lang.code = context.args[0].upper()
        if lang.locale is None:
            update.message.reply_text('No he reconocido ese idioma')
            return
    db.set_user(update.effective_user.id, lang.code)
    text = f'Has escogido <b>{lang.code} - {lang.vernacular}</b>'
    if update.callback_query:
        update.effective_message.edit_text(text, parse_mode=ParseMode.HTML)
    else:
        update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


showlangs_handler = CommandHandler('signlanguage', manage_langs)
setlang_handler = CallbackQueryHandler(set_lang, pattern=SELECTING_LANGUAGE)
pagelang_handler = CallbackQueryHandler(mediator_page, pattern=PAGE)
