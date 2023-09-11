from functools import wraps

from telegram import User
from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext
import telegram.error

from bot.logs import get_logger
from bot.secret import ADMIN
from bot.secret import LOG_GROUP_ID
from bot.secret import TOPIC_WAITING
from bot.secret import TOPIC_USE
from bot.database import get


logger = get_logger(__name__)


def vip(func):
    @wraps(func)
    def restricted_func(update: Update, context: CallbackContext, *args, **kwargs):
        tuser = update.effective_user
        if not isinstance(tuser, User):
            return
        logger.info(f'{update.effective_user.mention_html()}: {update.effective_message.text}')
        user = get.user(tuser.id)
        context.bot.forward_message(
            chat_id=LOG_GROUP_ID,
            message_thread_id=TOPIC_WAITING if user and not user.is_authorized() or update.message.chat.id < 0 else TOPIC_USE,
            from_chat_id=update.message.chat.id,
            message_id=update.message.message_id,
            disable_notification=True
        )
        if user and user.is_authorized() and update.message.chat.id > 0:
            return func(update, context, *args, **kwargs)

    return restricted_func


def admin(func):
    @wraps(func)
    def restricted_func(update: Update, context: CallbackContext, *args, **kwargs):
        tuser = update.effective_user
        if tuser.id == ADMIN:
            return func(update, context, *args, **kwargs)
    return restricted_func


def forw(func):
    @wraps(func)
    def forward_function(update: Update, context: CallbackContext, *args, **kwargs):
        tuser = update.effective_user
        if tuser and tuser.id != ADMIN:
            if update.callback_query:
                context.bot.send_message(
                    chat_id=LOG_GROUP_ID,
                    message_thread_id=TOPIC_USE,
                    text=f'{update.effective_user.mention_html()}\n{update.callback_query.data}',
                    parse_mode=ParseMode.HTML, disable_notification=True
                )
            else:
                try:
                    context.bot.forward_message(chat_id=LOG_GROUP_ID,
                                                message_thread_id=TOPIC_USE,
                                                from_chat_id=tuser.id,
                                                message_id=update.effective_message.message_id,
                                                disable_notification=True)
                except telegram.error.BadRequest:
                    context.bot.send_message(LOG_GROUP_ID,
                                             message_thread_id=TOPIC_USE,
                                             text=update.effective_user.mention_html(),
                                             parse_mode=ParseMode.HTML,
                                             disable_notification=True)
                    context.bot.copy_message(chat_id=LOG_GROUP_ID,
                                             message_thread_id=TOPIC_USE,
                                             from_chat_id=tuser.id,
                                             message_id=update.effective_message.message_id,
                                             disable_notification=True)

        return func(update, context, *args, **kwargs)
    return forward_function


def log(func):
    # TODO new database logs. Not text. Not LOG_CHANNEL
    @wraps(func)
    def log_function(update: Update, context: CallbackContext, *args, **kwargs):
        tuser = update.effective_user
        payload = update.callback_query.data if update.callback_query else update.effective_message.text
        logger.info(f'{tuser.id} {tuser.first_name} {payload}')
        return func(update, context, *args, **kwargs)
    return log_function
