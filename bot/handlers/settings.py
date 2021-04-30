import logging

from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    Filters,
)

from models import JWPubMedia, UserController

from utils import list_of_lists
from utils.decorators import vip, forw


logger = logging.getLogger(__name__)

SETTING_LANG, SETTING_QUALITY = range(2)


@forw
@vip
def get_lang(update: Update, context: CallbackContext) -> int:
    args = update.message.text.split()[1:]
    lang = args[0] if args else update.message.text
    langs = JWPubMedia.get_signs_languages()
    if lang in langs:
        UserController.set_user(update.message.from_user.id, lang)
        update.message.reply_markdown_v2(
            f'Lengua cambiada a\n```\n{lang} - {langs[lang]}\n```')
        return -1
    elif lang == '/lang':
        pretty_langs = '\n'.join([f'{code} - {lang}' for code,
                        lang in sorted(langs.items(), key=lambda x: x[1])])
        update.message.reply_markdown_v2(f'```\n{pretty_langs}\n```')
        update.message.reply_text('Dime el código de tu lengua señas.')
        return SETTING_LANG
    else:
        update.message.reply_text('No he reconocido ese idioma.')
        return -1

@forw
@vip
def get_quality(update: Update, context: CallbackContext) -> int:
    lang = UserController.get_user(update.effective_user.id)['lang']
    jw = JWPubMedia(lang, booknum='1')
    qualities = jw.get_qualities()
    args = update.message.text.split()[1:]
    quality = args[0] if args else update.message.text
    if quality in qualities:
        context.user_data['quality'] = quality
        UserController.set_user(update.message.from_user.id, quality=quality)
        update.message.reply_markdown_v2(
            f'Calidad configurada a\n```\n{quality}\n```', reply_markup=ReplyKeyboardRemove())
    elif quality == '/quality':
        buttons = list_of_lists(
            [KeyboardButton(q) for q in qualities],
            columns=2,
        )
        text = f'Elige la calidad para los videos'
        update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(buttons))
        return SETTING_QUALITY
    else:
        update.message.reply_text(
            f'No he reconocido esa calidad.')
        return -1



lang_handler = ConversationHandler(
    entry_points=[CommandHandler('lang', get_lang)],
    states={SETTING_LANG: [MessageHandler(Filters.text, get_lang)]},
    fallbacks=[CommandHandler('cancel', lambda x, y: -1)],
)

quality_handler = ConversationHandler(
    entry_points=[CommandHandler('quality', get_quality)],
    states={SETTING_QUALITY: [MessageHandler(Filters.text, get_quality)]},
    fallbacks=[CommandHandler('cancel', lambda x, y: -1)],

)
