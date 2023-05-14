from telegram import Update
from telegram.ext import CallbackContext
from telegram import ParseMode
from telegram.ext import CommandHandler

from bot.logs import get_logger
from bot.utils.decorators import vip, forw
from bot import MyCommand
from bot.strings import TextGetter
from bot.database import get


logger = get_logger(__name__)

@forw
@vip
def help(update: Update, context: CallbackContext) -> None:
    t = TextGetter(get.user(update.effective_user.id).bot_language.code)
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