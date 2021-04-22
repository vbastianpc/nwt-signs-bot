import logging
from functools import wraps


from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.utils.helpers import mention_markdown

from secret import ADMIN, CHANNEL_ID
from users import get_users

logger = logging.getLogger(__name__)


def vip(func):
    @wraps(func)
    def restricted_func(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        if str(user.id) in get_users():
            if not update.inline_query:
                logger.info('%s %d tiene autorización', user.name, user.id)
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
            logger.info('%s %d ha sido bloqueado', user.name, user.id)
        else:
            logger.warning('Qué hago aquí?')

    return restricted_func


def admin(func):
    @wraps(func)
    def restricted_func(update: Update, context: CallbackContext, **kwargs):
        user = update.effective_user
        if user.id == ADMIN:
            logger.info('%s %s tiene autorización', user.name, user.id)
            return func(update, context, **kwargs)
        else:
            logger.info('%s %s Ha intentado entrar pero no es admin',
                        user.name, user.id)
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
        text = update.effective_message.text if update.effective_message else ''
        if user.id != ADMIN:
            logger.info('%s (%s): %s', user.name, user.id, text)
            context.bot.forward_message(CHANNEL_ID ,user.id, update.message.message_id)
        return func(update, context, **kwargs)
    return forward_log_function