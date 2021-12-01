from telegram import Update
from telegram.ext import CallbackContext
from telegram import ParseMode
from telegram.ext import CommandHandler

from bot import get_logger
from bot.utils.decorators import vip
from bot import MyCommand
from bot.strings import TextGetter
from bot.database import localdatabase as db


logger = get_logger(__name__)


@vip
def help(update: Update, context: CallbackContext) -> None:
    t = TextGetter(db.get_user(update.effective_user.id).bot_lang)
    update.message.reply_text(
        text=t.help.format(
            MyCommand.SIGNLANGUAGE,
            MyCommand.BOTLANGUAGE,
            MyCommand.FEEDBACK,
            'https://github.com/vbastianpc/nwt-signs-bot/tree/master/bot/strings/strings',
            MyCommand.BOOKNAMES,
            context.bot.username,
        ),        
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )
help_handler = CommandHandler(MyCommand.HELP, help)