from functools import wraps

from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.utils.helpers import mention_markdown

from utils.secret import ADMIN, CHANNEL_ID
from models import UserController as uc


def vip(func):
    @wraps(func)
    def restricted_func(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        if user.id in uc.get_users_id():
            return func(update, context, **kwargs)
        elif not update.inline_query:
            context.bot.send_message(
                chat_id=user.id,
                text='Primero pide /permiso para ingresar al bot'
            )
            context.bot.send_message(
                chat_id=ADMIN,
                text=f'{mention_markdown(user.id, user.name)} `{user.id}` ha sido bloqueado',
                parse_mode=ParseMode.MARKDOWN,
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
                chat_id=ADMIN,
                text=f'{user.name} {user.id} Ha intentado entrar pero no es admin',
            )
            context.bot.send_message(
                chat_id=user.id,
                text=f'No tienes autorización para esta función',
            )
    return restricted_func


def forw(func):
    @wraps(func)
    def forward_log_function(update: Update, context: CallbackContext, **kwargs):
        user = update.effective_user
        if user.id != ADMIN:
            context.bot.forward_message(CHANNEL_ID, user.id, update.message.message_id)
        return func(update, context, **kwargs)
    return forward_log_function