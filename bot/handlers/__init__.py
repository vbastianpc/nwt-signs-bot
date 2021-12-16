from bot.handlers.bible import parse_bible_text_handler
from bot.handlers.bible import chapter_handler
from bot.handlers.bible import verse_handler
from bot.handlers.bible import parse_lang_bible_handler
from bot.handlers.settings import show_settings_handler
from bot.handlers.settings import showlangs_handler
from bot.handlers.settings import setlang_handler
from bot.handlers.settings import pagelang_handler
from bot.handlers.settings import botlang_handler
from bot.handlers.help import help_handler
from bot.handlers.inline_bible import inline_handler
from bot.handlers.admin.logs import test_handler
from bot.handlers.feedback import feedback_handler
from bot.handlers.start import start_handler
from bot.handlers.start import all_fallback_handler
from bot.handlers.booknames import bookname_handler
from bot.handlers.admin import auth_handler
from bot.handlers.admin import backup_handler
from bot.handlers.admin import delete_user_handler
from bot.handlers.admin import getting_user_handler
from bot.handlers.admin import database_status_handler
from bot.handlers.admin import reset_chapter_handler
from bot.handlers.admin.set_commands import set_commands_handler
from bot.handlers.admin.logs import notice_handler
from bot.handlers.admin.logs import logs_handler
from bot.handlers.admin.logs import logfile_handler
from bot.handlers.admin.logs import error_handler

# Order matters
handlers = [
    # conversation handler
    feedback_handler,
    botlang_handler,
    start_handler,
    notice_handler,

    # basic commands
    showlangs_handler,
    setlang_handler,
    pagelang_handler,
    auth_handler,
    bookname_handler,
    help_handler,
    show_settings_handler,

    # inline
    inline_handler,

    # admin handlers
    test_handler,
    delete_user_handler,
    backup_handler,
    logs_handler,
    logfile_handler,
    set_commands_handler,
    getting_user_handler,
    database_status_handler,
    reset_chapter_handler,

    # parse bible citation
    parse_lang_bible_handler, # fallback commands
    chapter_handler,
    verse_handler,
    parse_bible_text_handler,

    # fallback all
    all_fallback_handler,
]
