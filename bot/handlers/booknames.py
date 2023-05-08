from telegram import Update
from telegram.ext import CallbackContext
from telegram import ParseMode
from telegram.ext import CommandHandler

from bot.logs import get_logger
from bot import MyCommand
from bot.database import localdatabase as db
from bot.utils.decorators import forw, vip


logger = get_logger(__name__)

@forw
@vip
def send_booknames(update: Update, _: CallbackContext) -> None:
    db_user = db.get_user(update.effective_user.id)
    books = db.get_books(db_user.bot_language.id)
    width = max(map(lambda x: len(x.official_abbreviation), books)) + 1
    text = '\n'.join([
        f'{book.official_abbreviation:>{width}} {book.name}'
        for book in books
    ])
    update.message.reply_text(f'<code>{text}</code>', parse_mode=ParseMode.HTML)

bookname_handler = CommandHandler(MyCommand.BOOKNAMES, send_booknames)
