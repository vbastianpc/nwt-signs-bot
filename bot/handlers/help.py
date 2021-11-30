import logging

from telegram import Update
from telegram.ext import CallbackContext
from telegram import ParseMode
from telegram.ext import CommandHandler

from bot.utils.decorators import vip
from bot import MyCommand
from bot.strings import TextGetter
from bot.database import localdatabase as db


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


@vip
def help(update: Update, context: CallbackContext) -> None:
    t = TextGetter(db.get_user(update.effective_user.id).bot_lang)
    update.message.reply_text(
        text=t.help.format(
            MyCommand.SIGNLANGUAGE,
            MyCommand.BOTLANGUAGE,
            MyCommand.FEEDBACK,
            'https://www.jw.org',
            MyCommand.BOOKNAMES,
            context.bot.username,
        ),        
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )
help_handler = CommandHandler(MyCommand.HELP, help)