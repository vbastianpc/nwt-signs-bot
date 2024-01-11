from telegram import Update
from telegram import ParseMode
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.ext import ConversationHandler


from bot.logs import get_logger
from bot import MyCommand
from bot.utils.decorators import vip
from bot.strings import TextTranslator
from bot.database import get
from bot.secret import LOG_GROUP_ID


logger = get_logger(__name__)


@vip
def asking_feedback(update: Update, context: CallbackContext):
    tt: TextTranslator = context.user_data['tt']
    update.message.reply_text(tt.feedback_1(MyCommand.OK, MyCommand.CANCEL))
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
    tt: TextTranslator = context.user_data['tt']
    update.message.reply_text(tt.feedback_2)
    user = update.effective_user
    msg = context.bot.send_message(
        chat_id=LOG_GROUP_ID,
        text='#feedback',
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(user.name, url=f'tg://user?id={user.id}')]]
        )
    )
    for msg in context.chat_data['feedback']:
        msg.forward(LOG_GROUP_ID)

def cancel_feedback(update: Update, context: CallbackContext):
    tt: TextTranslator = context.user_data['tt']
    update.message.reply_text(tt.feedback_3)
    return ConversationHandler.END


feedback_handler = ConversationHandler(
    entry_points=[CommandHandler(MyCommand.FEEDBACK, asking_feedback)],
    states={1: [CommandHandler(MyCommand.CANCEL, cancel_feedback), MessageHandler(Filters.all, getting_feedback)]},
    fallbacks=[],
)
