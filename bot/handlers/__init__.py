from bot.handlers.bible import parse_bible_re_handler
from bot.handlers.bible import parse_bible_cmd_handler
from bot.handlers.bible import chapter_handler
from bot.handlers.bible import verse_handler
from bot.handlers.settings import showlangs_handler
from bot.handlers.settings import setlang_handler
from bot.handlers.settings import pagelang_handler
from bot.handlers.inline_bible import inline_handler
from bot.handlers.misc import botfather_handler
from bot.handlers.misc import test_handler
from bot.handlers.misc import info_inline_handler
from bot.handlers.misc import all_fallback_handler
from bot.handlers.misc import notice_handler
from bot.handlers.misc import logs_handler
from bot.handlers.misc import logfile_handler
from bot.handlers.auth import start_handler
from bot.handlers.auth import auth_handler
from bot.handlers.auth import backup_handler
from bot.handlers.auth import delete_user_handler
from bot.handlers.auth import getting_user_handler
from bot.handlers.auth import helper_admin_handler
from bot.handlers.feedback import feedback_handler


# Order matters
handlers = [
    inline_handler,
    start_handler,
    test_handler,
    showlangs_handler,
    setlang_handler,
    pagelang_handler,
    auth_handler,
    feedback_handler,
    info_inline_handler,
    delete_user_handler,
    backup_handler,
    logs_handler,
    logfile_handler,
    notice_handler,
    botfather_handler,
    getting_user_handler,
    helper_admin_handler,
    parse_bible_re_handler,
    parse_bible_cmd_handler,
    chapter_handler,
    verse_handler,
    all_fallback_handler,
]
