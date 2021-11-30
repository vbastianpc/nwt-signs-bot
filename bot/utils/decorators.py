import logging
from functools import wraps
import json

from telegram import User
from telegram import Update
from telegram.ext import CallbackContext

from bot import ADMIN
from bot import CHANNEL_ID
from bot.database import localdatabase as db


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def vip(func):
    @wraps(func)
    def restricted_func(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        msg = update.message
        if not isinstance(user, User):
            return
        db_user = db.get_user(user.id)
        if db_user is None or not db_user.is_brother():
            logger.info(f'{update.effective_user.mention_markdown_v2()} ha dicho: {update.effective_message.text}')
            context.bot.forward_message(
                chat_id=CHANNEL_ID,
                from_chat_id=update.message.chat.id,
                message_id=update.message.message_id,
            )
            # TODO si el mensaje es command, di que es privado. sino, ignoralo
            if any([ent.type == ent.BOT_COMMAND for ent in update.message.entities]):
                context.bot.send_message(
                    chat_id=user.id,
                    text='Este es un bot privado 🔒👤'
                )
        else:
            return func(update, context, **kwargs)

    return restricted_func


def admin(func):
    @wraps(func)
    def restricted_func(update: Update, context: CallbackContext, **kwargs):
        user = update.effective_user
        if user.id == ADMIN:
            return func(update, context, **kwargs)
        else:
            context.bot.send_message(
                chat_id=user.id,
                text=f'No tienes autorización para esta función',
            )
            context.bot.forward_message(
                CHANNEL_ID,
                user.id,
                update.message.message_id,
            )
    return restricted_func


def forw(func):
    @wraps(func)
    def forward_function(update: Update, context: CallbackContext, **kwargs):
        user = update.effective_user
        if user and user.id != ADMIN:
            context.bot.forward_message(CHANNEL_ID, user.id, update.message.message_id)
        return func(update, context, **kwargs)
    return forward_function


def log(func):
    @wraps(func)
    def log_function(update: Update, context: CallbackContext, **kwargs):
        user = update.effective_user
        payload = update.callback_query.data if update.callback_query else update.message.text
        logger.info(f'{user.id} {user.full_name} {payload}')
        return func(update, context, **kwargs)
    return log_function
