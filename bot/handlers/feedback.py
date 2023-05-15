from logging import Filter
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.ext import ConversationHandler

from bot.logs import get_logger
from bot import MyCommand
from bot.utils.decorators import forw
from bot.strings import TextTranslator
from bot.database import get


logger = get_logger(__name__)


@forw
def asking_feedback(update: Update, context: CallbackContext):
    t = TextTranslator(get.user(update.effective_user.id).bot_language.code)
    update.message.reply_text(t.feedback_1.format(MyCommand.CANCEL))
    return 1

@forw
def getting_feedback(update: Update, context: CallbackContext):
    t = TextTranslator(get.user(update.effective_user.id).bot_language.code)
    update.message.reply_text(t.feedback_2)
    return ConversationHandler.END

@forw
def cancel_feedback(update: Update, context: CallbackContext):
    t = TextTranslator(get.user(update.effective_user.id).bot_language.code)
    update.message.reply_text(t.feedback_3)
    return ConversationHandler.END

feedback_handler = ConversationHandler(
    entry_points=[CommandHandler(MyCommand.FEEDBACK, asking_feedback)],
    states={1: [MessageHandler(Filters.text & (~ Filters.command), getting_feedback)]},
    fallbacks=[
        CommandHandler(MyCommand.CANCEL, cancel_feedback),
        MessageHandler(Filters.command, lambda x, y: 1)
    ],
)
