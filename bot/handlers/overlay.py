from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler

from bot.database import get
from bot.database import add
from bot.utils.decorators import vip
from bot import MyCommand
from bot.strings import TextTranslator
from bot.utils import how_to_say




@vip
def toggle_overlay(update: Update, context: CallbackContext) -> None:
    user = get.user(update.effective_user.id)
    tt: TextTranslator = context.user_data['tt']
    if (context.args
            and (overlay_language := get.parse_language(code_or_meps=context.args[0]))
            and overlay_language
            and not overlay_language.is_sign_language):
        user = add.or_update_user(update.effective_user.id, overlay_language_code=overlay_language.code)
        update.message.reply_html(f'{tt.overlay_activated} {how_to_say(overlay_language.code, user.bot_language_code).capitalize()}')
    else:
        user = add.or_update_user(update.effective_user.id, with_overlay=not user.overlay_language_code)
        update.message.reply_html(tt.overlay_activated if user.overlay_language_code else tt.overlay_deactivated)
        

@vip
def toggle_delogo(update: Update, context: CallbackContext) -> None:
    user = get.user(update.effective_user.id)
    user = add.or_update_user(update.effective_user.id, delogo=not user.delogo)
    tt: TextTranslator = context.user_data['tt']
    update.message.reply_text(tt.delogo_activated if user.delogo else tt.delogo_deactivated, parse_mode=ParseMode.HTML)


overlay_handler = CommandHandler(MyCommand.OVERLAY, toggle_overlay)
delogo_handler = CommandHandler(MyCommand.DELOGO, toggle_delogo)
