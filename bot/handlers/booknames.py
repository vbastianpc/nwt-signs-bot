from unidecode import unidecode
from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler

from bot import get_logger
from bot import MyCommand
from bot.database import localdatabase as db
from bot.utils.decorators import forw, vip


logger = get_logger(__name__)

@forw
@vip
def send_booknames(update: Update, context: CallbackContext) -> None:
    db_user = db.get_user(update.effective_user.id)
    db_booknames = db.get_booknames(db_user.bot_lang)
    text = '\n'.join([
        f'{bookname.full_name} /{unidecode(bookname.abbr_name).lower()}'
        for bookname in db_booknames
    ])
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

bookname_handler = CommandHandler(MyCommand.BOOKNAMES, send_booknames)
