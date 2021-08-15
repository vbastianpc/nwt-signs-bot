import logging

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
from handlers.bible import SELECTING_CHAPTERS

from models import JWPubMedia, UserController

from utils import list_of_lists
from utils.decorators import vip, forw


logger = logging.getLogger(__name__)

SETTING_LANG, SETTING_QUALITY = range(2)
SELECTING_LANGUAGE = 'LANG'

@forw
@vip
def manage_langs(update: Update, context: CallbackContext) -> int:
    langs = context.user_data['langs'] = JWPubMedia.signs_languages()

    if context.args:
        return set_lang(update, context)
    uc = UserController(update.message.from_user.id)
    buttons = list_of_lists(
        [
            InlineKeyboardButton(
                f'{lang["code"]} - {lang["vernacular"]}' +
                ('' if lang['label'] == lang['vernacular'] else ' - ' + " ".join(lang["label"].split()[3:])),
                callback_data=f'{SELECTING_LANGUAGE}|{lang["code"]}'
            ) for lang in sorted(langs, key=lambda x: x['code'])
        ],
        columns=1
    )
    update.message.reply_text(
        f'Tu lengua actual es {uc.lang()}\n'
        'Escoge una lengua de señas.',
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return


def set_lang(update: Update, context: CallbackContext) -> int:
    if update.callback_query:
        langs = context.user_data['langs']
        code_lang = update.callback_query.data.split('|')[1]
    else:
        langs = JWPubMedia.signs_languages()
        code_langs = [lang['code'] for lang in langs]
        q = context.args[0]
        if q.upper() in code_langs:
            q = q.upper()
        if q not in code_langs:
            update.message.reply_text('No he reconocido ese idioma')
            return
        else:
            code_lang = q
    vern = next((x['vernacular'] for x in langs if x['code'] == code_lang), '')
    UserController.set_user(
        update.effective_user.id,
        code_lang,
        vernacular=vern,
    )
    update.effective_message.reply_text(f'Lengua cambiada a {code_lang} - {vern}')


@forw
@vip
def get_quality(update: Update, context: CallbackContext) -> int:
    lang = UserController.get_user(update.effective_user.id)['lang']
    jw = JWPubMedia(lang, booknum='49')
    qualities = jw.get_qualities()
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
        text = (f'Tu calidad actual es {uc.quality()}\n'
                'Elige una calidad para los videos')
        update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(buttons))
        return SETTING_QUALITY
    else:
        update.message.reply_text(
            f'No he reconocido esa calidad.')
        return -1



showlangs_handler = CommandHandler('lang', manage_langs)
setlang_handler = CallbackQueryHandler(set_lang, pattern=SELECTING_LANGUAGE)
quality_handler = ConversationHandler(
    entry_points=[CommandHandler('quality', get_quality)],
    states={SETTING_QUALITY: [MessageHandler(Filters.text, get_quality)]},
    fallbacks=[CommandHandler('cancel', lambda x, y: -1)],

)
