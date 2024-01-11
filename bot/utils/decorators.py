from functools import wraps
from html import escape
from typing import TypeVar, ParamSpec
from collections.abc import Callable

import telegram
from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
import telegram.error

from bot import MyCommand, AdminCommand
from bot.logs import get_logger
from bot.secret import ADMIN
from bot.secret import LOG_GROUP_ID
from bot.secret import TOPIC_WAITING
from bot.secret import TOPIC_USE
from bot.database import get, add
from bot.database.schema import User
from bot.strings import TextTranslator
from bot.utils import dt_now



logger = get_logger(__name__)


T = TypeVar('T')
P = ParamSpec('P')


def vip(func: Callable[P, T], log=True) -> Callable[P, T]:
    @wraps(func)
    def restricted_func(update: Update, context: CallbackContext, *args: P.args, **kwargs: P.kwargs) -> T | None:
        print('vip')
        tuser = update.effective_user
        if not isinstance(tuser, telegram.User):
            return None
        if log:
            logger.info(f'{update.effective_user.mention_html()}: {update.effective_message.text}')
        user = get.user(tuser.id)
        bot_language_code = user.bot_language_code if user else tuser.language_code if get.language(code=tuser.language_code) else 'en'
        context.user_data['tt'] = tt = TextTranslator(bot_language_code)
        if not user:
            update.effective_message.reply_html(tt.hi(escape(tuser.first_name or tuser.full_name)) + ' ' + tt.barrier_to_entry,
                                      disable_web_page_preview=True)
            tt_admin = TextTranslator(get.user(ADMIN).bot_language_code)
            context.bot.send_message(
                chat_id=LOG_GROUP_ID,
                message_thread_id=TOPIC_WAITING,
                text=(f'<pre><code class="language-python">'
                    f'full_name: {tuser.full_name}\nlanguage_code: {tuser.language_code}\nusername: {tuser.username}'
                    f'</code></pre>\n{tt_admin.waiting_list}'),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f'Add {tuser.full_name}', url=f'{context.bot.link}?start={tuser.id}')],
                    [InlineKeyboardButton(f'View {tuser.full_name}', url=f'tg://user?id={tuser.id}')],
                ])
            )

        user = add.or_update_user(
            tuser.id,
            first_name=tuser.first_name,
            last_name=tuser.last_name,
            user_name=tuser.username,
            is_premium=tuser.is_premium,
            bot_language_code=bot_language_code,
            status=User.WAITING if not user else user.status,
            last_active_datetime=dt_now()
        )
        if log:
            context.bot.forward_message(
                chat_id=LOG_GROUP_ID,
                message_thread_id=TOPIC_WAITING if not user.is_authorized() else TOPIC_USE,
                from_chat_id=update.message.chat.id,
                message_id=update.message.message_id,
                disable_notification=True
            )
        if not user.is_authorized():
            update.effective_message.reply_text(tt.wait)
            return None

        if user.is_authorized() and not user.sign_language:
            from bot.handlers.settings import set_language, manage_sign_languages
            if update.message.text.startswith('/'):
                command = update.message.text[1:]
                if command == MyCommand.SIGNLANGUAGE:
                    manage_sign_languages(update, context)
                elif command in list(MyCommand) + list(AdminCommand):
                    update.message.reply_html(tt.select_sl(MyCommand.SIGNLANGUAGE))
                else:
                    set_language(update, context)
            else:
                update.message.reply_html(tt.select_sl(MyCommand.SIGNLANGUAGE))
            return None

        if user.is_authorized() and update.message.chat.id > 0:
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
