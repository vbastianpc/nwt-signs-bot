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

from jw_pubmedia import (
    get_jw_data,
    get_labels,
    get_signs_languages,
)

from utils import list_of_lists
from decorators import vip, forw
from users import set_user_lang, set_user_quality, get_user_lang, get_user_quality


logger = logging.getLogger(__name__)

SETTING_LANG, SETTING_QUALITY = range(2)


@forw
@vip
def get_lang(update: Update, context: CallbackContext) -> int:
    args = update.message.text.split()[1:]
    lang = args[0] if args else update.message.text
    ud = context.user_data
    ud['all_langs'] = get_signs_languages()
    if lang in ud['all_langs']:
        set_user_lang(update.message.from_user.id, lang)
        update.message.reply_markdown_v2(
            f'Lengua cambiada a\n```\n{lang} - {ud["all_langs"][lang]}\n```')
        return -1
    elif lang == '/lang':
        langs = '\n'.join([f'{code} - {lang}' for code,
                        lang in sorted(ud['all_langs'].items(), key=lambda x: x[1])])
        update.message.reply_markdown_v2(f'```\n{langs}\n```')
        update.message.reply_text('Dime el código de la lengua señas.')
        return SETTING_LANG
    else:
        update.message.reply_text('No he reconocido ese idioma.')
        return -1

@forw
@vip
def get_quality(update: Update, context: CallbackContext) -> int:
    lang = get_user_lang(update.effective_user.id)
    jw_data = get_jw_data(1, lang)  # genesis
    args = update.message.text.split()[1:]
    quality = args[0] if args else update.message.text
    ud = context.user_data
    ud['all_labels'] = get_labels(jw_data, lang)
    if quality in ud['all_labels']:
        context.user_data['quality'] = quality
        set_user_quality(update.message.from_user.id, quality)
        update.message.reply_markdown_v2(
            f'Calidad configurada a\n```\n{quality}\n```', reply_markup=ReplyKeyboardRemove())
    elif quality == '/quality':
        context.user_data['all_labels'] = get_labels(jw_data, lang)
        buttons = list_of_lists(
            [KeyboardButton(q) for q in context.user_data['all_labels']],
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
