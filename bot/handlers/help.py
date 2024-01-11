from pathlib import Path

from telegram import Update
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram import ParseMode
from telegram.ext import CommandHandler

from bot.logs import get_logger
from bot.utils.decorators import vip
from bot import MyCommand
from bot.strings import TextTranslator
from bot.database import get


logger = get_logger(__name__)

@vip
def help(update: Update, context: CallbackContext) -> None:
    tt: TextTranslator = context.user_data['tt']
    update.message.reply_html(
        text=tt.help(
            MyCommand.SIGNLANGUAGE,
            MyCommand.BOTLANGUAGE,
            MyCommand.FEEDBACK,
            'https://github.com/vbastianpc/nwt-signs-bot/tree/master/bot/strings/strings',
            ),
        disable_web_page_preview=True,
    )
    update.message.reply_html(
        text=tt.inline_info(context.bot.name),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(tt.inline_here, switch_inline_query_current_chat='')],
            [InlineKeyboardButton(tt.inline_chat, switch_inline_query='')]
        ])
    )
    msg = update.message.reply_photo(
        photo=context.bot_data.get('overlay_info') or Path('./assets/overlay.jpg').read_bytes(),
        caption=tt.overlay_info(MyCommand.OVERLAY, MyCommand.DELOGO),
        parse_mode=ParseMode.HTML
    )
    context.bot_data['overlay_info'] = max(msg.photo, key=lambda p: p.height).file_id


help_handler = CommandHandler(MyCommand.HELP, help)
