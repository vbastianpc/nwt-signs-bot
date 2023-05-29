from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler

from bot.database import get
from bot.database import add
from bot.utils.decorators import vip
from bot import MyCommand
from bot.strings import TextTranslator



@vip
def toggle_overlay(update: Update, _: CallbackContext) -> None:
    tt = TextTranslator(update.effective_user.language_code)
    user = get.user(update.effective_user.id)
    user = add.or_update_user(update.effective_user.id,
                              with_overlay=False if user.overlay_language_code else True)
    update.message.reply_text(tt.overlay_activated if user.overlay_language_code else tt.overlay_deactivated,
                              parse_mode=ParseMode.HTML)


overlay_handler = CommandHandler(MyCommand.OVERLAY, toggle_overlay)
