
from telegram import Update
from telegram import BotCommandScopeChat
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler

from bot.utils.decorators import admin
from bot import strings
from bot import AdminCommand
from bot.logs import get_logger
from bot.database import localdatabase as db
from bot.strings import TextGetter


logger = get_logger(__name__)


@admin
def set_commands(update: Update, context: CallbackContext):
    for botlang in strings.botlangs():
        context.bot.set_my_commands(
            commands=strings.get_commands(botlang),
            language_code=botlang
        )
    db_user = db.get_user(update.effective_user.id)
    context.bot.set_my_commands(
        commands=(
            strings.get_commands(db_user.bot_language.code) +
            strings.get_admin_commands(db_user.bot_language.code)
        ),
        scope=BotCommandScopeChat(update.effective_user.id),
    )
    t = TextGetter(db_user.bot_language.code)
    update.message.reply_text(t.setcommands)
# TODO eliminar botcommands de todos los scope=BotCommandScopeChat(telegram_user_id)

set_commands_handler = CommandHandler(AdminCommand.SETCOMMANDS, set_commands)
