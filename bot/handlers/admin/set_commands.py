
from telegram import Update
from telegram import BotCommandScopeChat
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler

from bot.utils.decorators import admin
from bot.booknames import booknames
from bot import strings
from bot import AdminCommand
from bot import get_logger
from bot.database import localdatabase as db
from bot.strings import TextGetter


logger = get_logger(__name__)


@admin
def set_commands(update: Update, context: CallbackContext):
    for botlang in strings.botlangs():
        context.bot.set_my_commands(
            commands=strings.get_commands(botlang) + booknames.get_commands(botlang),
            language_code=botlang
        )
    db_user = db.get_user(update.effective_user.id)
    context.bot.set_my_commands(
        commands=(
            strings.get_commands(db_user.bot_lang) +
            strings.get_admin_commands(db_user.bot_lang) +
            booknames.get_commands(db_user.bot_lang)
        ),
        scope=BotCommandScopeChat(update.effective_user.id),
    )
    t = TextGetter(db_user.bot_lang)
    update.message.reply_text(t.setcommands)


set_commands_handler = CommandHandler(AdminCommand.SETCOMMANDS, set_commands)
