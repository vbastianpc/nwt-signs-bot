from html import escape

from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.ext import ConversationHandler
from telegram.utils.helpers import mention_html


from bot.logs import get_logger
from bot import MyCommand
from bot.utils.decorators import forw, vip
from bot.strings import TextTranslator
from bot.database import get
from bot.secret import ADMIN, LOG_CHANNEL_ID


logger = get_logger(__name__)


@vip
@forw
def asking_feedback(update: Update, _: CallbackContext):
    t = TextTranslator(get.user(update.effective_user.id).bot_language.code)
    update.message.reply_text(t.feedback_1(MyCommand.CANCEL))
    return 1

@forw
def getting_feedback(update: Update, context: CallbackContext):
    t = TextTranslator(get.user(update.effective_user.id).bot_language.code)
    update.message.reply_text(t.feedback_2)
    context.bot.send_message(
        chat_id=ADMIN,
        text=TextTranslator(get.user(ADMIN).bot_language_code).get_feedback(
            mention_html(update.effective_user.id, update.effective_user.full_name),
            escape(update.effective_user.username)),
        parse_mode=ParseMode.HTML
    )
    context.bot.forward_message(chat_id=ADMIN, from_chat_id=update.effective_user.id,
                                message_id=update.effective_message.message_id)
    context.bot.forward_message(chat_id=LOG_CHANNEL_ID, from_chat_id=update.effective_user.id,
                                message_id=update.effective_message.message_id)
    return ConversationHandler.END

@forw
def cancel_feedback(update: Update, _: CallbackContext):
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
