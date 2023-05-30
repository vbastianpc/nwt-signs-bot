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
    total_verses = sum(map(lambda x: x.count_verses, user.files))
    sign_language_codes = list(set(map(lambda x: x.language.code, user.files)))
    total_overlay = sum(map(lambda x: x.count_verses,
                            filter(lambda f: f.overlay_language_code is not None, user.files)))
    if len(sign_language_codes) == 1:
        update.message.reply_text(
            text=tt.stat(total_verses, how_to_say(sign_language_codes[0], user.bot_language.code), total_overlay,
                         *rdb.duration_size(user.id)),
            parse_mode=ParseMode.HTML)
    elif len(sign_language_codes) > 1:
        update.message.reply_text(
            text=tt.stats(total_verses, len(sign_language_codes), total_overlay, *rdb.duration_size(user.id)),
            parse_mode=ParseMode.HTML)
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
            parse_mode=ParseMode.HTML
        )


database_status_handler = CommandHandler(AdminCommand.STATS, stats)
