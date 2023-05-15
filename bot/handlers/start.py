
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram.utils.helpers import mention_markdown

from bot import MyCommand
from bot.secret import ADMIN
from bot.secret import LOG_CHANNEL_ID
from bot.logs import get_logger
from bot.utils.decorators import forw
from bot.database import get
from bot.strings import TextTranslator


logger = get_logger(__name__)

TAG_START = '#start'

@forw
def start(update: Update, context: CallbackContext, chat_id: int = None, first_name: str = None) -> None:
    tuser = update.effective_user
    first_name = first_name or tuser.first_name
    user = get.user(chat_id or update.effective_user.id)
    t = TextTranslator(update.effective_user.language_code if user is None else user.bot_language.code)

    if context.args and context.args[0] == 'github':
        context.bot.send_message(
            chat_id=ADMIN,
            text=t.from_github.format(mention_markdown(tuser.id, tuser.first_name)),
            parse_mode=ParseMode.MARKDOWN
        )
    
    if user is None or not user.is_authorized():
        db.set_user(
            update.effective_user.id,
            first_name=update.effective_user.first_name,
            bot_language=get.language(code=update.effective_user.language_code),
            status=user.WAITING
        )
        context.bot.send_message(
            chat_id=ADMIN,
            text=t.waiting_list.format(mention_markdown(tuser.id, tuser.first_name), tuser.id),
            parse_mode=ParseMode.MARKDOWN
        )
        context.bot.send_message(update.effective_user.id, '🔒👤')
        context.bot.send_message(
            chat_id=update.effective_user.id,
            text=t.barrier_to_entry.format(first_name),
            parse_mode=ParseMode.MARKDOWN,
        )
        return 1

    context.bot.send_message(
        chat_id=chat_id if chat_id else update.effective_user.id,
        text=t.greetings.format(first_name, MyCommand.SIGNLANGUAGE, MyCommand.HELP),
        parse_mode=ParseMode.MARKDOWN,
    )


def whois(update: Update, context: CallbackContext):
    tuser = update.effective_user
    t = TextTranslator(tuser.language_code)
    update.message.reply_text(t.wait)
    context.bot.send_message(
        chat_id=ADMIN,
        text=t.introduced_himself.format(TAG_START, mention_markdown(tuser.id, tuser.first_name), tuser.id),
        parse_mode=ParseMode.MARKDOWN,
    )
    context.bot.forward_message(ADMIN, tuser.id, update.message.message_id)
    context.bot.forward_message(LOG_CHANNEL_ID, tuser.id, update.message.message_id)
    return ConversationHandler.END


start_handler = ConversationHandler(
    entry_points=[CommandHandler(MyCommand.START, start)],
    states={
        1: [MessageHandler(Filters.text & (~ Filters.command), whois),
            MessageHandler(Filters.command, lambda x, y: 1)
        ],
    },
    fallbacks=[CommandHandler(MyCommand.CANCEL, lambda x, y: -1)],
    conversation_timeout=600
)

@forw
def all_fallback(update: Update, context: CallbackContext, text: str = None) -> None:
    # TODO text for multiline query. text is specific line dont understand
    user = get.user(update.effective_user.id)
    tt = TextTranslator(user.bot_language.code)
    update.effective_message.reply_text(tt.fallback)
    return

all_fallback_handler = MessageHandler(Filters.all, all_fallback)
