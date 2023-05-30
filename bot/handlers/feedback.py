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
def asking_feedback(update: Update, context: CallbackContext):
    t = TextTranslator(get.user(update.effective_user.id).bot_language.code)
    update.message.reply_text(t.feedback_1(MyCommand.OK))
    context.chat_data['feedback'] = []
    return 1


def getting_feedback(update: Update, context: CallbackContext):
    text = update.message.text or ''
    if text[1:] == MyCommand.OK:
        if context.chat_data['feedback']:
            ok_feedback(update, context)
        else:
            cancel_feedback(update, context)
        del context.chat_data['feedback']
        return ConversationHandler.END
    context.chat_data['feedback'].append(update.message)
    return 1


def ok_feedback(update: Update, context: CallbackContext):
    tt = TextTranslator(get.user(update.effective_user.id).bot_language.code)
    update.message.reply_text(tt.feedback_2)
    msg = context.bot.send_message(
        chat_id=ADMIN,
        text='#feedback\n' + TextTranslator(get.user(ADMIN).bot_language_code).get_feedback(
            mention_html(update.effective_user.id, update.effective_user.full_name),
            escape(update.effective_user.username)),
        parse_mode=ParseMode.HTML
    )
    msg.forward(LOG_CHANNEL_ID)
    for msg in context.chat_data['feedback']:
        msg.forward(ADMIN)
        msg.forward(LOG_CHANNEL_ID)



def cancel_feedback(update: Update, _: CallbackContext):
    tt = TextTranslator(get.user(update.effective_user.id).bot_language.code)
    update.message.reply_text(tt.feedback_3)


feedback_handler = ConversationHandler(
    entry_points=[CommandHandler(MyCommand.FEEDBACK, asking_feedback)],
    states={1: [MessageHandler(Filters.all, getting_feedback)]},
    fallbacks=[],
)
