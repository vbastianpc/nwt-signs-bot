import logging

from telegram import Update
from telegram.ext import CallbackContext
from telegram import ParseMode
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.ext import ConversationHandler

from bot.utils.decorators import forw
from bot import MyCommand

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


def help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "<b>Idioma</b>\n"
        f"Presiona /{MyCommand.SIGNLANGUAGE} y elige una lengua de señas.\n"
        f"O bien escribe /{MyCommand.SIGNLANGUAGE} y luego el código de la lengua de señas. Por ejemplo:\n"
        f"/{MyCommand.SIGNLANGUAGE} ASL\n\n"
        f"Usa /{MyCommand.BOTLANGUAGE} para cambiar el idioma del bot. También entenderé los nombres de los libros de la Biblia en tu idioma.\n\n\n"
        "",        
        parse_mode=ParseMode.HTML
    )