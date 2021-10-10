from bot.handlers.bible import parse_bible_re_handler
from bot.handlers.bible import parse_bible_cmd_handler
from bot.handlers.bible import chapter_handler
from bot.handlers.bible import verse_handler
from bot.handlers.bible import parse_lang_bible_handler
from bot.handlers.settings import showlangs_handler
from bot.handlers.settings import setlang_handler
from bot.handlers.settings import pagelang_handler
from bot.handlers.inline_bible import inline_handler
from bot.handlers.misc import test_handler
from bot.handlers.misc import info_inline_handler
from bot.handlers.misc import all_fallback_handler
from bot.handlers.misc import notice_handler
from bot.handlers.misc import logs_handler
from bot.handlers.misc import logfile_handler
from bot.handlers.feedback import feedback_handler
from bot.handlers.start import start_handler
from bot.handlers.admin import auth_handler
from bot.handlers.admin import backup_handler
from bot.handlers.admin import delete_user_handler
from bot.handlers.admin import getting_user_handler
from bot.handlers.admin import helper_admin_handler
from bot.handlers.admin import database_status_handler
from bot.handlers.admin.set_commands import botfather_handler
from bot.handlers.admin.set_commands import prepare_commands_handler
from bot.handlers.booknames import bookname_handler

# Order matters
handlers = [
    # basic commands
    start_handler,
    showlangs_handler,
    setlang_handler,
    auth_handler,
    feedback_handler,
    bookname_handler,

    # inline
    pagelang_handler,
    inline_handler,
    info_inline_handler,

    # admin handlers
    test_handler,
    delete_user_handler,
    backup_handler,
    logs_handler,
    logfile_handler,
    notice_handler,
    botfather_handler,
    getting_user_handler,
    helper_admin_handler,
    database_status_handler,
    prepare_commands_handler, # borrar

    # parse bible citation
    parse_lang_bible_handler,
    parse_bible_re_handler,
    parse_bible_cmd_handler,
    chapter_handler,
    verse_handler,

    # fallback
    all_fallback_handler,
]
