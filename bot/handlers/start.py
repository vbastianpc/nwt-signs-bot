
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.utils.helpers import mention_markdown

from bot import MyCommand
from bot.handlers.settings import show_sign_languages
from bot.handlers.settings import set_sign_language
from bot.handlers.settings import prev_next_signlanguage
from bot.handlers.settings import SELECT_SIGNLANGUAGE
from bot.handlers.settings import PAGE_SIGNLANGUAGE
from bot.secret import ADMIN
from bot.secret import LOG_CHANNEL_ID
from bot.logs import get_logger
from bot.utils.decorators import forw
from bot.database import get
from bot.database import add
from bot.strings import TextTranslator
from bot.database.schema import User


logger = get_logger(__name__)

TAG_START = '#start'

@forw
def start(update: Update, _: CallbackContext) -> None:
    tuser = update.effective_user
    user = get.user(update.effective_user.id)
    tt = TextTranslator(user.bot_language.code if user else tuser.language_code)
    if user and user.is_authorized() and user.sign_language:
        update.message.reply_text(tt.start)
        return -1
    if user and user.is_authorized() and not user.sign_language:
        update.message.reply_text(tt.step_2(MyCommand.SIGNLANGUAGE), parse_mode=ParseMode.MARKDOWN)
        return 3
    elif not user:
        add.or_update_user(tuser.id,
                           first_name=tuser.first_name,
                           last_name=tuser.last_name,
                           user_name=tuser.username,
                           is_premium=tuser.is_premium,
                           bot_language_code=tuser.language_code,
                           status=User.WAITING)
    update.message.reply_text(tt.barrier_to_entry(tuser.first_name or tuser.full_name),
                              parse_mode=ParseMode.MARKDOWN,
                              disable_web_page_preview=True)
    return 1


def whois(update: Update, context: CallbackContext):
    tuser = update.effective_user
    t = TextTranslator(tuser.language_code)
    update.message.reply_text(t.wait)
    msg = context.bot.send_message(
        chat_id=ADMIN,
        text=t.introduced_himself(TAG_START, mention_markdown(tuser.id, tuser.full_name), tuser.id),
        parse_mode=ParseMode.MARKDOWN,
    )
    context.bot.forward_message(chat_id=ADMIN, from_chat_id=tuser.id, message_id=update.effective_message.message_id)
    context.bot.forward_message(chat_id=LOG_CHANNEL_ID, from_chat_id=ADMIN, message_id=msg.message_id)
    context.bot.forward_message(LOG_CHANNEL_ID, tuser.id, update.message.message_id)
    return 2


def start_set_sign_language(update: Update, context: CallbackContext) -> None:
    tt = TextTranslator(update.effective_user.language_code)
    if update.callback_query:
        set_sign_language(update, context)
    else:
        like_code_or_meps = update.message.text.strip('/')
        language = get.parse_language(like_code_or_meps)
        if language and language.is_sign_language:
            set_sign_language(update, context, language.code)
        elif language:
            update.message.reply_text(tt.not_signlanguage(language.vernacular), parse_mode=ParseMode.MARKDOWN)
            return
        else:
            update.message.reply_text(tt.not_language(like_code_or_meps), parse_mode=ParseMode.MARKDOWN)
            return
    update.message.reply_text(tt.step_3(MyCommand.HELP))
    return -1



start_handler = ConversationHandler(
    entry_points=[CommandHandler(MyCommand.START, start)],
    states={1: [MessageHandler(Filters.text & (~ Filters.command), whois)],
            2: [MessageHandler(Filters.all, lambda x, y: 2)],  # infinite loop
            3: [CallbackQueryHandler(prev_next_signlanguage, pattern=PAGE_SIGNLANGUAGE),
                CallbackQueryHandler(start_set_sign_language, pattern=SELECT_SIGNLANGUAGE),
                CommandHandler(MyCommand.SIGNLANGUAGE, show_sign_languages),
                MessageHandler(Filters.text, start_set_sign_language)
                ]},
    fallbacks=[MessageHandler(Filters.all, lambda x, y: 1)],
    conversation_timeout=600,
    allow_reentry=True
)

@forw
def all_fallback(update: Update, context: CallbackContext, text: str = None) -> None:
    # TODO text for multiline query. text is specific line dont understand
    user = get.user(update.effective_user.id)
    tt = TextTranslator(user.bot_language.code)
    update.effective_message.reply_text(tt.fallback(MyCommand.HELP))
    return

all_fallback_handler = MessageHandler(Filters.all, all_fallback)
