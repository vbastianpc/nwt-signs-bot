import logging
from functools import wraps

from telegram import Update, User
from telegram.ext import CallbackContext

from utils.secret import ADMIN, CHANNEL_ID
from models import UserController as uc


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def vip(func):
    @wraps(func)
    def restricted_func(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        if not isinstance(user, User):
            logger.info('¿Quién trajo este usuario?')
            return
        if user.id in uc.get_users_id():
            return func(update, context, **kwargs)
        elif not update.inline_query:
            context.bot.send_message(
                chat_id=user.id,
                text='Presiona /start para comenzar'
            )
            context.bot.forward_message(
                CHANNEL_ID,
                user.id,
                update.message.message_id,
            )
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
