
from telegram import Update
from telegram import BotCommandScopeChat
from telegram import BotCommandScopeDefault
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler

from bot.utils.decorators import admin
from bot import strings
from bot import AdminCommand
from bot.logs import get_logger
from bot.database import get
from bot.strings import TextTranslator
from bot.secret import ADMIN


logger = get_logger(__name__)

@admin
def reset_commands(update: Update, context: CallbackContext):
    for language_code in strings.botlangs():
        context.bot.set_my_commands(commands=strings.get_commands(language_code), language_code=language_code)

    for user in get.users():
        member = context.bot.get_chat_member(chat_id=user.telegram_user_id, user_id=user.telegram_user_id)
        if member.user.language_code == user.bot_language.code and user.telegram_user_id != ADMIN:
            context.bot.delete_my_commands(BotCommandScopeChat(user.telegram_user_id))
        else:
            context.bot.set_my_commands(commands=strings.get_commands(user.bot_language.code),
                                        scope=BotCommandScopeChat(user.telegram_user_id))

    context.bot.set_my_commands(commands=strings.get_commands(strings.DEFAULT_LANGUAGE),
                                scope=BotCommandScopeDefault())
    user = get.user(ADMIN)
    context.bot.set_my_commands(
        commands=strings.get_commands(user.bot_language.code) + strings.get_admin_commands(user.bot_language.code),
        scope=BotCommandScopeChat(ADMIN))
    update.message.reply_text(TextTranslator(user.bot_language).setcommands)

set_commands_handler = CommandHandler(AdminCommand.SETCOMMANDS, reset_commands)
