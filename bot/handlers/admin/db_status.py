from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from bot import AdminCommand

from bot.secret import ADMIN
from bot.utils.decorators import vip
from bot.database import report as rdb
from bot.database import get
from bot.strings import TextTranslator
from bot.utils import how_to_say


@vip
def stats(update: Update, _: CallbackContext) -> None:
    user = get.user(update.effective_user.id)
    tt = TextTranslator(user.bot_language.code)
    data = rdb.stats_user(update.effective_user.id)
    total = sum(map(lambda x: x[1], data))
    if len(data) == 1:
        language = get.language(code=data[0][0])
        update.message.reply_text(tt.stat(total, how_to_say(language.code, user.bot_language.code)), parse_mode=ParseMode.MARKDOWN)
    elif len(data) > 1:
        update.message.reply_text(tt.stats(total, len(data)), parse_mode=ParseMode.MARKDOWN)
        text = '\n'.join([f'{code} - {count}' for code, count in data])
        update.message.reply_text(text)
    if update.effective_user.id == ADMIN:
        update.message.reply_text(
            tt.db_summary(
                rdb.count_videomarker(),
                rdb.count_sentverse(),
                rdb.count_biblechapter(),
                rdb.count_biblebook(),
                rdb.count_signlanguage(),
                rdb.count_user_brother(),
                rdb.count_user_blocked(),
                rdb.count_user_waiting(),
                rdb.count_user()
            ),
            parse_mode=ParseMode.MARKDOWN
        )


database_status_handler = CommandHandler(AdminCommand.STATS, stats)
