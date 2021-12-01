
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram.utils.helpers import mention_markdown

from bot import MyCommand
from bot import ADMIN
from bot import CHANNEL_ID
from bot import get_logger
from bot.utils.decorators import forw
from bot.database import localdatabase as db
from bot.strings import TextGetter


logger = get_logger(__name__)

TAG_START = '#start'

@forw
def start(update: Update, context: CallbackContext, chat_id: int = None, full_name: str = None) -> None:
    user = update.effective_user
    full_name = full_name or user.first_name
    db_user = db.get_user(chat_id or update.effective_user.id)
    t = TextGetter(update.effective_user.language_code if db_user is None else db_user.bot_lang)

    if context.args and context.args[0] == 'github':
        context.bot.send_message(
            chat_id=ADMIN,
            text=t.from_github.format(mention_markdown(user.id, user.full_name)),
            parse_mode=ParseMode.MARKDOWN
        )
    
    if db_user is None or not db_user.is_brother():
        db.add_waiting_user(update.effective_user.id, update.effective_user.full_name, update.effective_user.language_code)
        context.bot.send_message(
            chat_id=ADMIN,
            text=t.waiting_list.format(mention_markdown(user.id, user.first_name), user.id),
            parse_mode=ParseMode.MARKDOWN
        )
        context.bot.send_message(update.effective_user.id, '🔒👤')
        context.bot.send_message(
            chat_id=update.effective_user.id,
            text=t.barrier_to_entry.format(full_name),
            parse_mode=ParseMode.MARKDOWN,
        )
        return 1

    context.bot.send_message(
        chat_id=chat_id if chat_id else update.effective_user.id,
        text=t.greetings.format(user.first_name, MyCommand.SIGNLANGUAGE, MyCommand.HELP),
        parse_mode=ParseMode.MARKDOWN,
    )


def whois(update: Update, context: CallbackContext):
    user = update.effective_user
    t = TextGetter(user.language_code)
    update.message.reply_text(t.wait)
    context.bot.send_message(
        chat_id=ADMIN,
        text=t.introduced_himself.format(TAG_START, mention_markdown(user.id, user.first_name), user.id),
        parse_mode=ParseMode.MARKDOWN,
    )
    context.bot.forward_message(
        CHANNEL_ID,
        user.id,
        update.message.message_id
    )
    return ConversationHandler.END


start_handler = ConversationHandler(
    entry_points=[CommandHandler(MyCommand.START, start)],
    states={
        1: [MessageHandler(Filters.text & (~ Filters.command), whois),
            MessageHandler(Filters.command, lambda x, y: 1)
        ],
    },
    fallbacks=[CommandHandler(MyCommand.CANCEL, lambda x, y: -1)]
)

@forw
def all_fallback(update: Update, context: CallbackContext) -> None:
    return

all_fallback_handler = MessageHandler(Filters.all, all_fallback)
