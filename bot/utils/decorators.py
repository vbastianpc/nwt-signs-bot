from functools import wraps
import json

from telegram import User
from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext
import telegram.error

from bot.logs import get_logger
from bot.secret import ADMIN
from bot.secret import LOG_CHANNEL_ID
from bot.database import localdatabase as db


logger = get_logger(__name__)


def vip(func):
    @wraps(func)
    def restricted_func(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        if not isinstance(user, User):
            return
        db_user = db.get_user(user.id)
        if db_user is None or not db_user.is_authorized():
            logger.info(f'{update.effective_user.mention_markdown_v2()}: {update.effective_message.text}')
            context.bot.forward_message(
                chat_id=LOG_CHANNEL_ID,
                from_chat_id=update.message.chat.id,
                message_id=update.message.message_id,
            )
            return
        else:
            return func(update, context, *args, **kwargs)

    return restricted_func


def admin(func):
    @wraps(func)
    def restricted_func(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        if user.id != ADMIN:
            context.bot.forward_message(LOG_CHANNEL_ID, user.id, update.effective_message.message_id)
            return
        return func(update, context, *args, **kwargs)
    return restricted_func


def forw(func):
    @wraps(func)
    def forward_function(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        if user and user.id != ADMIN:
            if update.callback_query:
                context.bot.send_message(
                    chat_id=LOG_CHANNEL_ID,
                    text=f'{update.effective_user.mention_html()}\n{update.callback_query.data}',
                    parse_mode=ParseMode.HTML
                    )
            else:
                try:
                    context.bot.forward_message(LOG_CHANNEL_ID, user.id, update.effective_message.message_id)
                except telegram.error.BadRequest:
                    context.bot.send_message(LOG_CHANNEL_ID, update.effective_user.mention_html(), parse_mode=ParseMode.HTML)
                    context.bot.copy_message(LOG_CHANNEL_ID, user.id, update.effective_message.message_id)

        return func(update, context, *args, **kwargs)
    return forward_function


def log(func):
    @wraps(func)
    def log_function(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        payload = update.callback_query.data if update.callback_query else update.effective_message.text
        logger.info(f'{user.id} {user.full_name} {payload}')
        return func(update, context, *args, **kwargs)
    return log_function
