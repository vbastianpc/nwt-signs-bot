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
import telegram.error

from bot.database import session
from bot.database import get
from bot.database import add
from bot.database import fetch
from bot.database import report as rdb
from bot.database.schema import Language
from bot.utils import list_of_lists
from bot.utils.decorators import vip, forw
from bot.utils.browser import browser
from bot.secret import ADMIN
from bot import strings
from bot.utils import how_to_say
from bot.logs import get_logger
from bot import MyCommand
from bot.strings import TextTranslator


logger = get_logger(__name__)

SELECT_LANGUAGE = 'SELECT_LANGUAGE'
PAGE_SIGNLANGUAGE = 'PAGE_SIGNLANGUAGE'
PAGE_BOTLANGUAGE = 'PAGE_BOTLANGUAGE'


@vip
def show_current_settings(update: Update, context: CallbackContext) -> None:
    user = get.user(update.effective_user.id)
    tt: TextTranslator = context.user_data['tt']
    update.message.reply_html(
        text=tt.multiple_signlanguage(
            *(user.sign_language.meps_symbol, user.sign_language.vernacular),
            *(user.sign_language2.meps_symbol, user.sign_language2.vernacular) if user.sign_language2 else ('', ''),
            *(user.sign_language3.meps_symbol, user.sign_language3.vernacular) if user.sign_language3 else ('', '')
        ) + '\n' +
             tt.current_settings(user.bot_language.code,
                                 user.bot_language.vernacular,
                                 tt.enabled if user.overlay_language else tt.disabled,
                                 tt.enabled if user.delogo else tt.disabled
        ),
    )


def build_signlangs(update: Update, _: CallbackContext):
    user = get.user(update.effective_user.id)
    res = browser.open(f'https://www.jw.org/{user.bot_language.code}/languages/')
    return list_of_lists(
        [{
            'text': f'{sl["symbol"]} - {sl["name"]}',
            'callback_data': f'{SELECT_LANGUAGE}|{sl["symbol"]}' # symbol == language_code
        } for sl in sorted(
            filter(lambda l: l['isSignLanguage'], res.json()['languages']),
            key=lambda x: x['symbol']
        )
        ],
        columns=1
    )


@forw
def manage_sign_languages(update: Update, context: CallbackContext):
    if not context.args:
        show_sign_languages(update, context)
        return
    user = get.user(update.effective_user.id)
    args = [*context.args, '', '', ''][:3] # len(args) == 3 -> True
    sl = list(filter(lambda x: x and x.is_sign_language, [get.parse_language(args[0]), get.parse_language(args[1]), get.parse_language(args[2])]))
    sl += [None, None, None]
    user.sign_language_code = sl[0].code if sl[0] else user.sign_language.code
    user.sign_language_code2 = sl[1].code if sl[1] else None
    user.sign_language_code3 = sl[2].code if sl[2] else None
    session.commit()

    tt: TextTranslator = context.user_data['tt']
    update.message.reply_html(
        text=tt.multiple_signlanguage(
            *(user.sign_language.meps_symbol, user.sign_language.vernacular),
            *(user.sign_language2.meps_symbol, user.sign_language2.vernacular) if user.sign_language2 else ('', ''),
            *(user.sign_language3.meps_symbol, user.sign_language3.vernacular) if user.sign_language3 else ('', '')
        ),
    )


def show_sign_languages(update: Update, context: CallbackContext):
    update.effective_message.reply_chat_action(ChatAction.TYPING)
    fetch.languages()
    tt: TextTranslator = context.user_data['tt']
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
                 max_buttons: int = 12,
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
        buttons.append([InlineKeyboardButton('-', callback_data=' '),
                        InlineKeyboardButton(f'{page}/{total_pages}', callback_data=' '),
                        InlineKeyboardButton('▶️', callback_data=f'{suffix}|{page + 1}|▶️')])
    elif 1 < page < total_pages:
        buttons.append([InlineKeyboardButton('◀️', callback_data=f'{suffix}|{page - 1}|◀️'),
                        InlineKeyboardButton(f'{page}/{total_pages}', callback_data=' '),
                        InlineKeyboardButton('▶️', callback_data=f'{suffix}|{page + 1}|▶️')])
    elif page == total_pages:
        buttons.append([InlineKeyboardButton('◀️', callback_data=f'{suffix}|{page - 1}|◀️'),
                        InlineKeyboardButton(f'{page}/{total_pages}', callback_data=' '),
                        InlineKeyboardButton('-', callback_data=' ')])
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
    update.callback_query.answer()
    send_buttons(
        message=update.effective_message,
        info_for_buttons=build_signlangs(update, context),
        suffix=PAGE_SIGNLANGUAGE,
        page=int(page),
        action=action
    )


def build_botlangs():
    return list_of_lists(
        items=[{'text': f'{botlang} - {vernacular}',
                'callback_data': f'{SELECT_LANGUAGE}|{botlang}'}
               for botlang, vernacular in strings.botlangs_vernacular()],
        columns=1,
    )


@vip
def show_botlangs(update: Update, context: CallbackContext) -> None:
    tt: TextTranslator = context.user_data['tt']
    send_buttons(
        message=update.message,
        info_for_buttons=build_botlangs(),
        suffix=PAGE_BOTLANGUAGE,
        text=tt.choose_botlang,
        edit_message=False,
    )


@forw
def set_language(update: Update, context: CallbackContext, code_or_meps: str = None) -> int:
    user = get.user(update.effective_user.id)
    update.effective_message.reply_chat_action(ChatAction.TYPING)
    if update.callback_query:
        code_or_meps = update.callback_query.data.split('|')[1]
        update.callback_query.answer('👋')
    else:
        code_or_meps = code_or_meps or update.message.text[1:] # /SCH

    language = get.parse_language(code_or_meps)
    context.user_data['tt'] = tt = TextTranslator(user.bot_language.code)
    if not language:
        update.effective_message.reply_html(tt.not_language(code_or_meps))
        return
    if language.is_sign_language:
        language_name = how_to_say(language.code, user.bot_language.code)
        user = add.or_update_user(update.effective_user.id, sign_language_code=language.code)
        text = tt.ok_signlanguage_code(language_name)
        update.effective_message.reply_html(text)
    else: # bot language
        context.user_data['tt'] = tt = TextTranslator(language.code)
        language_name = how_to_say(language.code, language.code)
        user = add.or_update_user(update.effective_user.id, bot_language_code=language.code, with_overlay=bool(user.overlay_language_code))
        if tt.language['code'] == language.code:
            text = tt.ok_botlang(language_name)
        else:
            text = tt.no_botlang_but(how_to_say(language.code, 'en'), MyCommand.FEEDBACK)
        update.effective_message.reply_html(text)
        set_my_commands(update.effective_user, user.bot_language)

    fetch.editions(language.code)
    fetch.hebrew_greek(language.code)
    try:
        fetch.books(language.code)
    except:
        update.effective_message.reply_html(tt.no_bible(language.name, 'english'))
        add.or_update_user(update.effective_user.id, bot_language_code='en')
    return


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

@forw
def prev_next_botlang(update: Update, _: CallbackQueryHandler) -> None:
    _, page, action = update.callback_query.data.split('|')
    send_buttons(
        message=update.effective_message,
        info_for_buttons=build_botlangs(),
        suffix=PAGE_SIGNLANGUAGE,
        page=int(page),
        action=action,
    )


show_settings_handler = CommandHandler(MyCommand.SETTINGS, show_current_settings)
set_lang_handler = CallbackQueryHandler(set_language, pattern=SELECT_LANGUAGE)

show_signlangs_handler = CommandHandler(MyCommand.SIGNLANGUAGE, manage_sign_languages)
page_signlang_handler = CallbackQueryHandler(prev_next_signlanguage, pattern=PAGE_SIGNLANGUAGE)

show_botlang_handler = CommandHandler(MyCommand.BOTLANGUAGE, show_botlangs)
page_botlang_handler = CallbackQueryHandler(prev_next_botlang, pattern=PAGE_BOTLANGUAGE)
