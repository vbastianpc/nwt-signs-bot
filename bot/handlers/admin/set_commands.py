import logging

from telegram import Update, ParseMode
from telegram import BotCommand, BotCommandScopeChat
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.utils.helpers import mention_markdown

from bot.utils.decorators import admin
from bot import ADMIN
from bot.booknames import booknames
from bot import strings
from bot import AdminCommand
from bot.database import localdatabase as db


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


@admin
def set_commands(update: Update, context: CallbackContext):
    for botlang in strings.botlangs():
        context.bot.set_my_commands(
            commands=strings.get_commands(botlang) + booknames.get_commands(botlang),
            language_code=botlang
        )
    db_user = db.get_user(update.effective_user.id)
    context.bot.set_my_commands(
        commands=strings.get_commands(db_user.bot_lang) + strings.get_admin_commands(db_user.bot_lang) + booknames.get_commands(db_user.bot_lang),
        scope=BotCommandScopeChat(update.effective_user.id),
    )
    update.message.reply_text('Comandos actualizados')


set_commands_handler = CommandHandler(AdminCommand.SETCOMMANDS, set_commands)
