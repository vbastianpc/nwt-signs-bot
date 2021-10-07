import logging
from math import ceil
from uuid import uuid4
import time

from telegram import Update
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.message import Message
import telegram.error

from bot.models.jwpubmedia import JWInfo
from bot.database import localdatabase as db
from bot.utils import list_of_lists
from bot.utils.decorators import vip, forw
from bot.database import localdatabase as db
from bot.database.schemedb import SignLanguage
from bot.database.localdatabase import SESSION


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


def generate_lang_buttons(update: Update, context: CallbackContext):
    info_for_buttons = context.user_data['info_for_buttons'] = list_of_lists(
        [{
            'text': f'{lang["code"]} - {lang["vernacular"]}',
            'callback_data': f'{SELECTING_LANGUAGE}|{lang["code"]}'
        } for lang in sorted(JWInfo().signs_languages, key=lambda x: x['code'])
        ],
        columns=1
    )
    db_user = db.get_user(update.effective_user.id)
    send_buttons(
        message=update.message,
        info_for_buttons=info_for_buttons,
        text=f'Tu idioma actual es {db_user.lang_code} - {db_user.lang_vernacular}' if db_user.lang_code else f'Primero debes escoger una lengua de señas.'
    )


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
    jw = JWInfo()
    if update.callback_query:
        valid_code = update.callback_query.data.split('|')[1]
        del context.user_data['info_for_buttons']
    elif context.args:
        valid_code = next((lang['code'] for lang in jw.signs_languages if lang['code'].upper() == context.args[0].upper()), None)
        if valid_code is None:
            update.message.reply_text('No he reconocido ese idioma')
            return
    jw.lang_code = valid_code
    locale, name, vern, rsconf, lib = jw.locale(), jw.name(), jw.vernacular(), jw.rsconf(), jw.lib()
    db.insert_or_update_sign_language(valid_code, locale, name, vern, rsconf, lib)
    db.set_user(update.effective_user.id, valid_code)
    text = f'Lengua cambiada a {valid_code} - {vern}'
    if update.callback_query:
        update.effective_message.edit_text(text)
    else:
        update.effective_message.reply_text(text)


def write(update: Update, context: CallbackContext):
    update.message.reply_text('Comenzando test...')
    t0 = time.time()
    for i in range(10000):
        sign_language = SignLanguage(
            lang_code=str(i),
            locale=str(uuid4()),
            name=str(uuid4()),
            vernacular=str(uuid4()),
            rsconf=str(uuid4()),
            lib=str(uuid4())
        )
        SESSION.add(sign_language)
        SESSION.commit()
    update.message.reply_text(f'Han pasado {time.time() - t0:.2f}')


def read(update: Update, context: CallbackContext):
    update.message.reply_text('Comenzando test...')
    t0 = time.time()
    for i in range(10000):
        sign_language = SESSION.query(SignLanguage).filter(SignLanguage.lang_code == str(i)).all()
    update.message.reply_text(f'Han pasado {time.time() - t0:.2f} {sign_language}')



write_handler = CommandHandler('write', write)
read_handler = CommandHandler('read', read)
showlangs_handler = CommandHandler('lang', manage_langs)
setlang_handler = CallbackQueryHandler(set_lang, pattern=SELECTING_LANGUAGE)
pagelang_handler = CallbackQueryHandler(mediator_page, pattern=PAGE)
