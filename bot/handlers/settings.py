from math import ceil

from telegram import Update
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ParseMode
from telegram import Message
from telegram import User as TUser
from telegram import ChatAction
from telegram import BotCommandScopeChat
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import ConversationHandler
import telegram.error

from bot.database import get
from bot.database import add
from bot.database import fetch
from bot.database import report as rdb
from bot.database.schema import Language
from bot.utils import list_of_lists
from bot.utils.decorators import vip, forw, log
from bot.utils.browser import browser
from bot.secret import ADMIN
from bot import strings
from bot.utils import how_to_say
from bot.logs import get_logger
from bot import MyCommand
from bot.strings import TextTranslator
from bot import exc


logger = get_logger(__name__)

SELECT_SIGNLANGUAGE = 'SELECT_SIGNLANGUAGE'
PAGE_SIGNLANGUAGE = 'PAGE_SIGNLANGUAGE'
SELECT_BOTLANGUAGE = 'SELECT_BOTLANGUAGE'
PAGE_BOTLANGUAGE = 'PAGE_BOTLANGUAGE'


@forw
@vip
def show_current_settings(update: Update, _: CallbackContext) -> None:
    user = get.user(update.effective_user.id)
    tt = TextTranslator(user.bot_language.code)
    update.message.reply_text(
        text=tt.current_settings(user.sign_language.code,
                                 user.sign_language.vernacular,
                                 user.bot_language.code,
                                 user.bot_language.vernacular,
                                 tt.enabled if user.overlay_language else tt.disabled,
        ),
        parse_mode=ParseMode.HTML
    )


def build_signlangs(update: Update, _: CallbackContext):
    user = get.user(update.effective_user.id)
    res = browser.open(f'https://www.jw.org/{user.bot_language.code}/languages/')
    return list_of_lists(
        [{
            'text': f'{sign_language["symbol"]} - {sign_language["name"]}',
            'callback_data': f'{SELECT_SIGNLANGUAGE}|{sign_language["symbol"]}' # symbol == language_code
        } for sign_language in sorted(
            filter(lambda l: l['isSignLanguage'], res.json()['languages']),
            key=lambda x: x['symbol'])
        ],
        columns=1
    )


@forw
@vip
def show_sign_languages(update: Update, context: CallbackContext):
    update.effective_message.reply_chat_action(ChatAction.TYPING)
    fetch.languages()
    tt = TextTranslator(get.user(update.effective_user.id).bot_language.code)
    send_buttons(
        message=update.message,
        info_for_buttons=build_signlangs(update, context),
        suffix=PAGE_SIGNLANGUAGE,
        text=tt.menu_signlanguage(rdb.count_signlanguage()),
        edit_message=False
    )


def send_buttons(message: Message,
                 info_for_buttons: list,
                 suffix: str,
                 page: int = 1,
                 text: str = None,
                 max_buttons: int = 10,
                 edit_message=True,
                 action=None,
                 ) -> Message:
    """Generic function to split large data into inlinekeyboard pages"""
    if text is None:
        text = message.text
    buttons = []
    data = info_for_buttons[(page - 1) * max_buttons:page * max_buttons]
    if not data:
        return
    for row in data:
        buttons.append([InlineKeyboardButton(**kwargs) for kwargs in row])
    total_pages = ceil(len(info_for_buttons) / max_buttons)
    if page == total_pages == 1:
        pass
    elif page == 1:
        buttons.append([InlineKeyboardButton('-', callback_data='None'),
                        InlineKeyboardButton(f'{page}/{total_pages}', callback_data='None'),
                        InlineKeyboardButton('▶️', callback_data=f'{suffix}|{page + 1}|▶️')])
    elif 1 < page < total_pages:
        buttons.append([InlineKeyboardButton('◀️', callback_data=f'{suffix}|{page - 1}|◀️'),
                        InlineKeyboardButton(f'{page}/{total_pages}', callback_data='None'),
                        InlineKeyboardButton('▶️', callback_data=f'{suffix}|{page + 1}|▶️')])
    elif page == total_pages:
        buttons.append([InlineKeyboardButton('◀️', callback_data=f'{suffix}|{page - 1}|◀️'),
                        InlineKeyboardButton(f'{page}/{total_pages}', callback_data='None'),
                        InlineKeyboardButton('-', callback_data='None')])
    kwargs = {'text': text, 'reply_markup': InlineKeyboardMarkup(buttons), 'parse_mode': ParseMode.HTML}
    if edit_message:
        try:
            return message.edit_text(**kwargs)
        except telegram.error.BadRequest:
            return
    else:
        return message.reply_text(**kwargs)


@forw
def prev_next_signlanguage(update: Update, context: CallbackContext):
    _, page, action = update.callback_query.data.split('|')
    send_buttons(
        message=update.effective_message,
        info_for_buttons=build_signlangs(update, context),
        suffix=PAGE_SIGNLANGUAGE,
        page=int(page),
        action=action
    )


@forw
def set_sign_language(update: Update, context: CallbackContext, sign_language_code=None) -> int:
    user = get.user(update.effective_user.id)
    t = TextTranslator(user.bot_language.code)
    if update.callback_query:
        sign_language_code = update.callback_query.data.split('|')[1]

    user = add.or_update_user(update.effective_user.id,
                              sign_language_code=sign_language_code,
                              sign_language_name=how_to_say(sign_language_code, user.bot_language.code))
    text = t.ok_signlanguage_code(user.sign_language_name)
    if update.callback_query:
        update.effective_message.edit_text(text, parse_mode=ParseMode.HTML)
    else:
        update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

    if not get.edition(language_code=sign_language_code):
        fetch.editions()
    if not get.books(sign_language_code):
        fetch.books(language_code=sign_language_code)


def build_botlangs():
    return list_of_lists(
        items=[{'text': f'{botlang} - {vernacular}',
                'callback_data': f'{SELECT_BOTLANGUAGE}|{botlang}'}
               for botlang, vernacular in strings.botlangs_vernacular()],
        columns=1,
    )


@forw
@vip
def show_botlangs(update: Update, context: CallbackContext) -> None:
    t = TextTranslator(get.user(update.effective_user.id).bot_language.code)
    msg = send_buttons(
        message=update.message,
        info_for_buttons=build_botlangs(),
        suffix=PAGE_BOTLANGUAGE,
        text=t.choose_botlang,
        edit_message=False,
    )
    context.user_data['msgbotlang'] = msg



@forw
@log
def set_bot_language(update: Update, context: CallbackContext, bot_language_code=None) -> None:
    if update.callback_query:
        context.user_data['msgbotlang'].edit_reply_markup()
        del context.user_data['msgbotlang']
        bot_language_code = update.callback_query.data.split('|')[1]
    else:
        bot_language_code = bot_language_code or context.args[0].lower()
    tt = TextTranslator(bot_language_code)
    text = ''
    update.effective_message.reply_chat_action(ChatAction.TYPING)
    user = get.user(update.effective_user.id)
    if not get.edition(language_code=bot_language_code):
        fetch.editions()
    if not get.books(bot_language_code):
        try:
            fetch.books(bot_language_code)
        except exc.EditionNotFound:
            text += tt.no_bible(get.language(code=bot_language_code).vernacular, user.bot_language.vernacular)

    if get.books(bot_language_code):
        user = add.or_update_user(update.effective_user.id,
                                  bot_language_code=bot_language_code,
                                  sign_language_name=how_to_say(user.sign_language.code, bot_language_code),
                                  with_overlay=True if user.overlay_language else False)
        set_my_commands(update.effective_user, user.bot_language)

        if tt.language['code'] != bot_language_code:
            text = tt.no_botlang_but(user.bot_language.vernacular.capitalize(), MyCommand.FEEDBACK) + '\n\n' + text
        else:
            text = tt.ok_botlang(user.bot_language.vernacular.capitalize()) + '\n\n' + text

    if update.callback_query:
        update.effective_message.edit_text(text, parse_mode=ParseMode.HTML)
    else:
        update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
    return ConversationHandler.END


def set_my_commands(user: TUser, bot_language: Language) -> None:
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


def prev_next_botlang(update: Update, _: CallbackQueryHandler) -> None:
    _, page, action = update.callback_query.data.split('|')
    send_buttons(
        message=update.effective_message,
        info_for_buttons=build_botlangs(),
        suffix=PAGE_SIGNLANGUAGE,
        page=int(page),
        action=action,
    )
    return 1


show_settings_handler = CommandHandler(MyCommand.SETTINGS, show_current_settings)

show_signlangs_handler = CommandHandler(MyCommand.SIGNLANGUAGE, show_sign_languages)
set_signlang_handler = CallbackQueryHandler(set_sign_language, pattern=SELECT_SIGNLANGUAGE)
page_signlang_handler = CallbackQueryHandler(prev_next_signlanguage, pattern=PAGE_SIGNLANGUAGE)

show_botlang_handler = CommandHandler(MyCommand.BOTLANGUAGE, show_botlangs)
set_botlang_handler = CallbackQueryHandler(set_bot_language, pattern=SELECT_BOTLANGUAGE)
page_botlang_handler = CallbackQueryHandler(prev_next_botlang, pattern=PAGE_BOTLANGUAGE)