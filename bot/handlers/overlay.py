from pathlib import Path

from telegram import Update
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler

from bot.database import get
from bot.database import add
from bot.utils.decorators import vip
from bot.utils.decorators import forw
from bot import MyCommand
from bot.strings import TextTranslator



@vip
def toggle_overlay(update: Update, _: CallbackContext) -> None:
    tt = TextTranslator(update.effective_user.language_code)
    user = get.user(update.effective_user.id)
    user = add.or_update_user(update.effective_user.id,
                              with_overlay=False if user.overlay_language_id else True)
    update.message.reply_text(tt.overlay_activated if user.overlay_language_id else tt.overlay_deactivated,
                              parse_mode=ParseMode.MARKDOWN)
    


@vip
def overlay_info(update: Update, context: CallbackContext) -> None:
    user = get.user(update.effective_user.id)
    tt = TextTranslator(user.bot_language.code)
    msg = context.bot.send_photo(
        update.effective_user.id,
        photo=context.bot_data.get('overlay_info') or Path('./assets/overlay.jpg').read_bytes(),
        caption=tt.overlay_info(MyCommand.OVERLAY),
        parse_mode=ParseMode.MARKDOWN
    )
    context.bot_data['overlay_info'] = max(msg.photo, key=lambda p: p.height).file_id

overlay_handler = CommandHandler(MyCommand.OVERLAY, toggle_overlay)
overlay_info_handler = CommandHandler(MyCommand.OVERLAYINFO, overlay_info)
