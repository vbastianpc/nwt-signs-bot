import logging
from math import ceil
from ruamel.yaml import YAML
from pathlib import Path

from telegram import Update
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ParseMode
from telegram import Message
from telegram import User
from telegram import BotCommandScopeChat
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext.filters import Filters
import telegram.error

from bot.jw.jwlanguage import JWLanguage
from bot.database import localdatabase as db
from bot.database import report as rdb
from bot.utils import list_of_lists
from bot.utils.decorators import vip, forw
from bot import strings
from bot import MyCommand
from bot.booknames import booknames


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

SELECTING_SIGNLANGUAGE = 'SELECTING_SIGNLANGUAGE'
PAGE_SIGNLANGUAGE = 'PAGE_SIGNLANGUAGE'
SELECTING_BOTLANGUAGE = 'SELECTING_BOTLANGUAGE'
PAGE_BOTLANGUAGE = 'PAGE_BOTLANGUAGE'
yaml = YAML(typ='safe')


def build_signlangs():
    return list_of_lists(
        [{
            'text': f'{sign_language.code} - {sign_language.vernacular}',
            'callback_data': f'{SELECTING_SIGNLANGUAGE}|{sign_language.code}'
        } for sign_language in db.get_sign_languages()
        ],
        columns=1
    )    


@forw
@vip
def manage_langs(update: Update, context: CallbackContext):
    if context.args:
        set_lang(update, context)
    else:
        generate_lang_buttons(update, context)




def generate_lang_buttons(update: Update, context: CallbackContext):
    text = f'🧏‍♂️ <b>Escoge una lengua de señas</b>\n🌎 Total: <b>{rdb.count_signlanguage()}</b>'
    send_buttons(
        message=update.message,
        info_for_buttons=build_signlangs(),
        suffix=PAGE_SIGNLANGUAGE,
        text=text,
    )


def send_buttons(message: Message, info_for_buttons, suffix: str, page: int=1, text: str=None, max_buttons: int=10) -> Message:
    """Generic function to split large data into inlinekeyboard pages"""
    if text is None:
        text = message.text
    buttons = []
    data = info_for_buttons[(page - 1) * max_buttons:page * max_buttons]
    if not data:
        return
    for row in data:
        buttons.append([InlineKeyboardButton(**kwargs) for kwargs in row])
    total_pages = ceil( len(info_for_buttons) / max_buttons)
    if page != total_pages:
        buttons.append([
            InlineKeyboardButton('◀️', callback_data=f'{suffix}|{page - 1}'),
            InlineKeyboardButton(f'{page}/{total_pages}', callback_data='None'),
            InlineKeyboardButton('▶️', callback_data=f'{suffix}|{page + 1}')
        ])
    kwargs = {'text': text, 'reply_markup': InlineKeyboardMarkup(buttons), 'parse_mode': ParseMode.HTML}
    try:
        msg = message.edit_text(**kwargs)
    except telegram.error.BadRequest:
        msg = message.reply_text(**kwargs)
    return msg


def prev_next_signlanguage(update: Update, context: CallbackContext):
    send_buttons(
        message=update.effective_message,
        info_for_buttons=build_signlangs(),
        suffix=PAGE_SIGNLANGUAGE,
        page=int(update.callback_query.data.strip(f'{PAGE_SIGNLANGUAGE}|')),
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



def build_botlangs():
    return list_of_lists(
        items=[{'text': f'{botlang} - {vernacular}',
         'callback_data': f'{SELECTING_BOTLANGUAGE}|{botlang}'}
        for botlang, vernacular in strings.botlangs_vernacular()],
        columns=1,
    )


def show_botlangs(update: Update, context: CallbackContext) -> None:
    msg = send_buttons(
        message=update.message,
        info_for_buttons=build_botlangs(),
        suffix=PAGE_BOTLANGUAGE,
        text='Escoge un idioma para la interfaz del bot. Si tu idioma no está en la lista escribe su código.'
    )
    context.user_data['msgbotlang'] = msg
    return 1


def set_new_botlang(update: Update, context: CallbackQueryHandler) -> None:
    logger.info('')
    context.user_data['msgbotlang'].edit_reply_markup()
    del context.user_data['msgbotlang']
    likely_langlocale = update.message.text.lower()
    try:
        db_language = booknames.add_booknames(likely_langlocale)
        logger.info(f'Booknames agregados {likely_langlocale!r}')
    except ValueError:
        update.message.reply_text(f'El idioma {likely_langlocale!r} no existe')
    else:
        db.set_user(update.effective_user.id, bot_lang=db_language.locale)
        update.message.reply_text(f'A partir de ahora te entenderé si me pides nombres de libros bíblicos en {db_language.locale} - {db_language.vernacular}.\n'
            f'Si quieres ayudarme a traducir este bot a más idiomas, déjame un comentario en /{MyCommand.FEEDBACK}.')
        logger.info(f'idioma {likely_langlocale!r} configurado para usuario en db')
    set_my_commands(update.effective_user, likely_langlocale, likely_langlocale)
    return -1


def set_botlang(update: Update, context: CallbackContext) -> None:
    context.user_data['msgbotlang'].edit_reply_markup()
    del context.user_data['msgbotlang']
    botlang = update.callback_query.data.split('|')[1]
    db.set_user(update.effective_user.id, bot_lang=botlang)
    logger.info(f'Idioma {botlang} ya existe archivo yaml')
    set_my_commands(update.effective_user, botlang, botlang)
    update.effective_message.reply_text(f'Ahora te hablaré en {botlang!r}')
    return -1


def set_my_commands(user: User, botlang: str, lang_locale: str) -> None:
    if user.language_code == botlang:
        user.bot.delete_my_commands(scope=BotCommandScopeChat(user.id))
        logger.info('Comandos BotCommandScopeChat borrados')
    else:
        user.bot.set_my_commands(
            commands=strings.get_commands(botlang) + booknames.get_commands(lang_locale),
            scope=BotCommandScopeChat(user.id)
        )
        logger.info(f'Comandos BotCommandScopeChat para {user.id} {botlang}')


def prev_next_botlang(update: Update, context: CallbackQueryHandler) -> None:
    send_buttons(
        message=update.effective_message,
        info_for_buttons=build_botlangs(),
        suffix=PAGE_SIGNLANGUAGE,
        page=int(update.callback_query.data.strip(f'{PAGE_SIGNLANGUAGE}|')),
    )
    return 1


showlangs_handler = CommandHandler(MyCommand.SIGNLANGUAGE, manage_langs)
setlang_handler = CallbackQueryHandler(set_lang, pattern=SELECTING_SIGNLANGUAGE)
pagelang_handler = CallbackQueryHandler(prev_next_signlanguage, pattern=PAGE_SIGNLANGUAGE)

botlang_handler = ConversationHandler(
    entry_points=[CommandHandler(MyCommand.BOTLANGUAGE, show_botlangs)],
    states={
        1: [MessageHandler(Filters.text, set_new_botlang),
            CallbackQueryHandler(set_botlang, pattern=SELECTING_BOTLANGUAGE),
            CallbackQueryHandler(prev_next_botlang, pattern=PAGE_BOTLANGUAGE)]
    },
    fallbacks=[CommandHandler('cancel', lambda x, y: -1)]
)
