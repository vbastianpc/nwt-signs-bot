from pathlib import Path
import logging
import json

from unidecode import unidecode
from telegram import ChatAction
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.error import TelegramError

from bot import CHANNEL_ID
from bot import ADMIN
from bot.jw.jwpubmedia import JWBible
from bot.utils import video
from bot.database import start_database
from bot.database import localdatabase as db
from bot.database.schemedb import SentVerse, Language
from bot.utils import BIBLE_BOOKALIAS_NUM
from bot.utils import list_of_lists
from bot.utils import safechars
from bot.utils import parse_bible_pattern
from bot.utils import seems_bible
from bot.utils import BooknumNotFound
from bot.utils import MultipleBooknumsFound
from bot.utils.decorators import vip, forw, log


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)



def send_booknames(update: Update, context: CallbackContext) -> None:
    db_user = db.get_user(update.effective_user.id)
    db_booknames = db.get_booknames(db_user.bot_lang)
    text = '\n'.join([
        f'{bookname.full_name} /{unidecode(bookname.abbr_name).lower()}'
        for bookname in db_booknames
    ])
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


bookname_handler = CommandHandler('booknames', send_booknames)
