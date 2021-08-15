import logging

from telegram import Update
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters, ConversationHandler

from utils.decorators import forw


logger = logging.getLogger(__name__)


@forw
def asking_feedback(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Do you have any suggestions? Something it's wrong? "
        "You can /cancel this conversation anyway"
    )
    return 1

@forw
def getting_feedback(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Thank you very much for your time. Your feedback is highly appreciated."
    )
    return ConversationHandler.END

@forw
def cancel_feedback(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Oops. Do not worry about that. Send me a suggestion whenever you want.'
    )
    return ConversationHandler.END

feedback_handler = ConversationHandler(
    entry_points=[CommandHandler('feedback', asking_feedback)],
    states={1: [MessageHandler(~Filters.text('/cancel'), getting_feedback)]},
    fallbacks=[CommandHandler('cancel', cancel_feedback)],
)