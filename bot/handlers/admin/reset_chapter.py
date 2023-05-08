from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler

from bot.utils.decorators import admin
from bot.database import localdatabase as db
from bot import AdminCommand
from bot.logs import get_logger
from bot.strings import TextGetter
from bot.booknames.parse import parse_bible_citation
from bot.booknames.parse import BooknumNotFound, BibleCitationNotFound



logger = get_logger(__name__)


@admin
def reset_chapter(update: Update, context: CallbackContext) -> None:
    if not context.args:
        return
    db_user = db.get_user(update.effective_user.id)
    t = TextGetter(db_user.bot_language.code)
    try:
        book, chapter, _ = parse_bible_citation(' '.join(context.args), db_user.bot_language.id)
        assert chapter is not None
    except (BooknumNotFound, BibleCitationNotFound, AssertionError):
        return
    bible_chapter, files, old_checksum = db.touch_checksum(db_user.signlanguage.meps_symbol, book.booknum, chapter)
    if bible_chapter is not None:
        text = f'{book.full_name} {chapter} {old_checksum}\n' + '\n'.join([s.citation for s in files])
        update.effective_message.reply_text(t.checksum_touched.format(text))
    else:
        update.effective_message.reply_text(t.checksum_failed.format(book.full_name, chapter))


reset_chapter_handler = CommandHandler(AdminCommand.RESET_CHAPTER, reset_chapter)