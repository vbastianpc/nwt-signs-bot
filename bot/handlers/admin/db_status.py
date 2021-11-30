from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from bot import AdminCommand

from bot.utils.decorators import admin
from bot.database import report as rdb
from bot.database import localdatabase as db
from bot.strings import TextGetter


@admin
def database_status(update: Update, context: CallbackContext) -> None:
    t = TextGetter(db.get_user(update.effective_user.id).bot_lang)
    update.message.reply_text(
        t.db_summary.format(
            rdb.count_videomarker(),
            rdb.count_sentverse(),
            rdb.count_biblechapter(),
            rdb.count_biblebook(),
            rdb.count_signlanguage(),
            rdb.count_user_brother(),
            rdb.count_user_blocked(),
            rdb.count_user_waiting(),
            rdb.count_user(),
        ),
    parse_mode=ParseMode.MARKDOWN
    )

database_status_handler = CommandHandler(AdminCommand.STATS, database_status)
