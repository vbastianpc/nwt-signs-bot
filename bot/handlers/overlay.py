
from telegram import Update
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext.filters import Filters

from bot.database import localdatabase as db
from bot.utils.decorators import vip
from bot.utils.decorators import forw
from bot import MyCommand
from bot.strings import TextGetter



@vip
def menu_overlay(update: Update, context: CallbackContext) -> None:
    t = TextGetter(update.effective_user.language_code)
    db_user = db.get_user(update.effective_user.id)

    msg = update.message.reply_text(
        text=(
            t.overlay_description + '\n\n' + 
            (t.overlay_deactivated if db_user.overlay_language is None else t.overlay_activated)
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(t.yes, callback_data='YES')],
            [InlineKeyboardButton(t.no, callback_data='NO')]
        ]),
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data['message_id'] = msg.message_id
    return 1

@forw
def with_overlay(update: Update, context: CallbackContext) -> None:
    db_user = db.get_user(update.effective_user.id)
    db.set_user(update.effective_user.id, overlay_language=db_user.bot_language)
    t = TextGetter(update.effective_user.language_code)
    context.bot.edit_message_text(
        message_id=context.user_data['message_id'],
        chat_id=update.effective_chat.id,
        text=t.overlay_activated,
        parse_mode=ParseMode.MARKDOWN
    )
    return -1

@forw
def without_overlay(update: Update, context: CallbackContext) -> None:
    db.set_user(update.effective_user.id, overlay_language=False)
    t = TextGetter(update.effective_user.language_code)
    context.bot.edit_message_text(
        message_id=context.user_data['message_id'],
        chat_id=update.effective_chat.id,
        text=t.overlay_deactivated,
        parse_mode=ParseMode.MARKDOWN
    )
    return -1



overlay_handler = ConversationHandler(
    entry_points=[CommandHandler(MyCommand.OVERLAY, menu_overlay)],
    states={
        1: [CallbackQueryHandler(with_overlay, pattern='YES'),
            CallbackQueryHandler(without_overlay, pattern='NO')]
    },
    fallbacks=[MessageHandler(Filters.command, lambda u, c: -1)]
)