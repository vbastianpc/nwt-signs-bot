import logging

from telegram import Update, ParseMode
from telegram import BotCommand, BotCommandScopeChat
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.utils.helpers import mention_markdown

from bot.utils.decorators import admin
from bot.utils import BIBLE_BOOKNAMES, BIBLE_NUM_BOOKALIAS
from bot import ADMIN


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


@admin
def paraBotFather(update: Update, context: CallbackContext):
    commands = [
        ('start', 'Mensaje de bienvenida'),
        ('lang', '[código] Cambia la lengua de señas'),
        ('inline', 'Aprende a usar el modo inline'),
        ('feedback', 'Send me your feedback'),
    ] + [
        (cmd, BIBLE_BOOKNAMES[num - 1]) for num, cmd in sorted(BIBLE_NUM_BOOKALIAS.items())
    ]
    context.bot.set_my_commands(commands)

    text = '\n'.join([f'{cmd} - {descrip}' for cmd, descrip in commands])
    update.message.reply_text(text)
    update.message.reply_text('Comandos actualizados')


# @admin
def prepare_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(update.effective_user.language_code)
    context.bot.set_my_commands(
        commands=[BotCommand('admin', 'Solo se ve si eres admin, no importa tu idioma')],
        scope=BotCommandScopeChat(ADMIN),
    )
    context.bot.set_my_commands(
        commands=[BotCommand('italiano', 'Solo se ve si eres italiano')],
        language_code='it'
    )


botfather_handler = CommandHandler('commands', paraBotFather)
prepare_commands_handler = CommandHandler('prepare', prepare_command)
