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
    user = get.user(update.effective_user.id)
    user = add.or_update_user(update.effective_user.id, with_overlay=not user.overlay_language_code)
    tt = TextTranslator(user.bot_language_code)
    update.message.reply_text(tt.overlay_activated if user.overlay_language_code else tt.overlay_deactivated,
                              parse_mode=ParseMode.HTML)

@vip
def toggle_delogo(update: Update, _: CallbackContext) -> None:
    user = get.user(update.effective_user.id)
    user = add.or_update_user(update.effective_user.id, delogo=not user.delogo)
    tt = TextTranslator(user.bot_language_code)
    update.message.reply_text(tt.delogo_activated if user.delogo else tt.delogo_deactivated, parse_mode=ParseMode.HTML)


overlay_handler = CommandHandler(MyCommand.OVERLAY, toggle_overlay)
delogo_handler = CommandHandler(MyCommand.DELOGO, toggle_delogo)
