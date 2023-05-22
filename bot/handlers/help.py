from telegram import Update
from telegram.ext import CallbackContext
from telegram import ParseMode
from telegram.ext import CommandHandler

from bot.logs import get_logger
from bot.utils.decorators import vip, forw
from bot import MyCommand
from bot.strings import TextTranslator
from bot.database import get
from bot.handlers.overlay import overlay_info


logger = get_logger(__name__)

@forw
@vip
def help(update: Update, context: CallbackContext) -> None:
    tt = TextTranslator(get.user(update.effective_user.id).bot_language.code)
    update.message.reply_text(text=tt.help(MyCommand.SIGNLANGUAGE, MyCommand.BOTLANGUAGE, MyCommand.PROTIPS),
                              parse_mode=ParseMode.MARKDOWN)

@forw
@vip
def protips(update: Update, context: CallbackContext) -> None:
    tt = TextTranslator(get.user(update.effective_user.id).bot_language.code)
    update.effective_message.reply_text(
        text=tt.pro_tips(MyCommand.FEEDBACK,
                         'https://github.com/vbastianpc/nwt-signs-bot/tree/master/bot/strings/strings',
                         context.bot.name),
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True)
    overlay_info(update, context)


help_handler = CommandHandler(MyCommand.HELP, help)
protips_handler = CommandHandler(MyCommand.PROTIPS, protips)
