from math import ceil

from telegram import ChatAction
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

from bot.database import localdatabase as db
from bot.database import report as rdb
from bot.database.schemedb import Language
from bot.utils import list_of_lists
from bot.utils.decorators import vip, forw, log
from bot.secret import ADMIN
from bot import strings
from bot.logs import get_logger
from bot import MyCommand
from bot.strings import TextGetter


logger = get_logger(__name__)

SELECTING_SIGNLANGUAGE = 'SELECTING_SIGNLANGUAGE'
PAGE_SIGNLANGUAGE = 'PAGE_SIGNLANGUAGE'
SELECTING_BOTLANGUAGE = 'SELECTING_BOTLANGUAGE'
PAGE_BOTLANGUAGE = 'PAGE_BOTLANGUAGE'
# yaml = YAML(typ='safe')


@forw
@vip
def show_current_settings(update: Update, context: CallbackContext) -> None:
    db_user = db.get_user(update.effective_user.id)
    t = TextGetter(db.get_user(update.effective_user.id).bot_language.code)
    update.message.reply_text(
        text=t.show_settings.format(
            db_user.signlanguage.meps_symbol,
            db_user.signlanguage.vernacular,
            db_user.bot_language.code,
            strings.get_language(db_user.bot_language.code)['vernacular'],
            MyCommand.SIGNLANGUAGE,
            MyCommand.BOTLANGUAGE
        ),
        parse_mode=ParseMode.MARKDOWN
    )

def build_signlangs():
    return list_of_lists(
        [{
            'text': f'{sign_language.code} - {sign_language.vernacular}',
            'callback_data': f'{SELECTING_SIGNLANGUAGE}|{sign_language.meps_symbol}'
        } for sign_language in sorted(db.get_sign_languages(), key=lambda x: x.code)
        ],
        columns=1
    )    


@forw
@vip
def manage_langs(update: Update, context: CallbackContext):
    db.fetch_languages()
    if context.args:
        set_sign_language(update, context)
    else:
        generate_lang_buttons(update, context)


def generate_lang_buttons(update: Update, context: CallbackContext):
    t = TextGetter(db.get_user(update.effective_user.id).bot_language.code)
    send_buttons(
        message=update.message,
        info_for_buttons=build_signlangs(),
        suffix=PAGE_SIGNLANGUAGE,
        text=t.menu_signlanguage.format(rdb.count_signlanguage()),
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
    kwargs = {'text': text, 'reply_markup': InlineKeyboardMarkup(buttons), 'parse_mode': ParseMode.MARKDOWN}
    try:
        msg = message.edit_text(**kwargs)
    except telegram.error.BadRequest:
        msg = message.reply_text(**kwargs)
    return msg


@forw
def prev_next_signlanguage(update: Update, context: CallbackContext):
    send_buttons(
        message=update.effective_message,
        info_for_buttons=build_signlangs(),
        suffix=PAGE_SIGNLANGUAGE,
        page=int(update.callback_query.data.strip(f'{PAGE_SIGNLANGUAGE}|')),
    )

@forw
def set_sign_language(update: Update, context: CallbackContext, sign_language_code=None) -> int:
    t = TextGetter(db.get_user(update.effective_user.id).bot_language.code)
    if update.callback_query:
        sign_language_code = update.callback_query.data.split('|')[1]
    else:
        sign_language_code = sign_language_code or context.args[0].lower()
    try:
        db_user = db.set_user(update.effective_user.id, sign_language_code=sign_language_code)
    except:
        update.message.reply_text(t.wrong_signlanguage_code)
    else:
        text = t.ok_signlanguage_code.format(sign_language_code, db_user.sign_language.vernacular)
        if update.callback_query:
            update.effective_message.edit_text(text, parse_mode=ParseMode.MARKDOWN)
        else:
            update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)



def build_botlangs():
    return list_of_lists(
        items=[{'text': f'{botlang} - {vernacular}',
         'callback_data': f'{SELECTING_BOTLANGUAGE}|{botlang}'}
        for botlang, vernacular in strings.botlangs_vernacular()],
        columns=1,
    )

@forw
@vip
def show_botlangs(update: Update, context: CallbackContext) -> None:
    t = TextGetter(db.get_user(update.effective_user.id).bot_language.code)
    msg = send_buttons(
        message=update.message,
        info_for_buttons=build_botlangs(),
        suffix=PAGE_BOTLANGUAGE,
        text=t.choose_botlang
    )
    context.user_data['msgbotlang'] = msg
    return 1


@forw
def set_new_botlang(update: Update, context: CallbackContext) -> None:
    db_user = db.get_user(update.effective_user.id)
    context.user_data['msgbotlang'].edit_reply_markup()
    del context.user_data['msgbotlang']
    likely_langcode = update.message.text.lower()
    language = db.get_language(code=likely_langcode)
    
    if not language:
        t = TextGetter(db_user.bot_language.code)
        update.message.reply_text(t.wrong_botlang.format(likely_langcode))
        return -1
    if not db.get_bible(language.meps_symbol):
        context.bot.send_chat_action(update.message.chat_id, ChatAction.TYPING)
        # TODO reply_text fetching bible edition pub language_code
        db.fetch_bible_editions()
    if not db.get_books(language.id):
        # TODO reply text fetching bible booknames language_code
        db.fetch_bible_books(language.meps_symbol)
    db.set_user(
        update.effective_user.id,
        bot_language=language,
        overlay_language=language if db_user.overlay_language else None,
    )
    t = TextGetter('en')
    update.message.reply_text(t.ok_botlang.format(language.code, language.vernacular), parse_mode=ParseMode.MARKDOWN)
    logger.info(f'idioma {language.code!r} configurado para usuario en db')
    set_my_commands(update.effective_user, language)
    return -1


@forw
@log
def set_botlang(update: Update, context: CallbackContext) -> None:
    context.user_data['msgbotlang'].edit_reply_markup()
    del context.user_data['msgbotlang']
    botlang = update.callback_query.data.split('|')[1]
    t = TextGetter(botlang)
    language = db.get_language(code=botlang)
    db_user = db.get_user(update.effective_user.id)
    db.set_user(update.effective_user.id,
                bot_language=language,
                overlay_language=language if db_user.overlay_language else None)
    set_my_commands(update.effective_user, language)
    update.callback_query.answer(f'{language.vernacular} - {language.code}')
    update.effective_message.reply_text(
        text=t.ok_botlang.format(language.vernacular),
        parse_mode=ParseMode.MARKDOWN,
    )
    if not db.get_bible(language.meps_symbol):
        db.fetch_bible_editions()
    if not db.get_books(language.id):
        db.fetch_bible_books(language.meps_symbol)
    return ConversationHandler.END


def set_my_commands(user: User, bot_language: Language) -> None:
    if user.language_code == bot_language.code and user.id != ADMIN:
        user.bot.delete_my_commands(scope=BotCommandScopeChat(user.id))
        logger.info('Comandos BotCommandScopeChat borrados')
        return

    user.bot.set_my_commands(
        commands=(
            strings.get_commands(bot_language.code) +
            (strings.get_admin_commands(bot_language.code) if user.id == ADMIN else [])
        ),
        scope=BotCommandScopeChat(user.id)
    )
    logger.info(f'Comandos BotCommandScopeChat para {user.id} {bot_language.code}')
    


def prev_next_botlang(update: Update, context: CallbackQueryHandler) -> None:
    send_buttons(
        message=update.effective_message,
        info_for_buttons=build_botlangs(),
        suffix=PAGE_SIGNLANGUAGE,
        page=int(update.callback_query.data.strip(f'{PAGE_SIGNLANGUAGE}|')),
    )
    return 1


show_settings_handler = CommandHandler(MyCommand.SETTINGS, show_current_settings)
showlangs_handler = CommandHandler(MyCommand.SIGNLANGUAGE, manage_langs)
setlang_handler = CallbackQueryHandler(set_sign_language, pattern=SELECTING_SIGNLANGUAGE)
pagelang_handler = CallbackQueryHandler(prev_next_signlanguage, pattern=PAGE_SIGNLANGUAGE)

botlang_handler = ConversationHandler(
    entry_points=[CommandHandler(MyCommand.BOTLANGUAGE, show_botlangs)],
    states={
        1: [MessageHandler(Filters.text & (~ Filters.command), set_new_botlang),
            CallbackQueryHandler(set_botlang, pattern=SELECTING_BOTLANGUAGE),
            CallbackQueryHandler(prev_next_botlang, pattern=PAGE_BOTLANGUAGE)]
    },
    fallbacks=[MessageHandler(Filters.command, lambda u, c: -1)]
)
