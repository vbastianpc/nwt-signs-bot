from bot.handlers.bible import book_handler
from bot.handlers.bible import chapter_handler
from bot.handlers.bible import verse_handler
from bot.handlers.bible import parse_bible_handler
from bot.handlers.bible import show_books_handler
from bot.handlers.bible import fallback_query_handler
from bot.handlers.settings import show_settings_handler
from bot.handlers.settings import show_signlangs_handler
from bot.handlers.settings import set_lang_handler
from bot.handlers.settings import page_signlang_handler
from bot.handlers.settings import show_botlang_handler
from bot.handlers.settings import page_botlang_handler
from bot.handlers.help import help_handler
from bot.handlers.inline_bible import inline_handler
from bot.handlers.admin.logs import test_handler
from bot.handlers.feedback import feedback_handler
from bot.handlers.start import start_handler
from bot.handlers.start import all_fallback_handler
from bot.handlers.booknames import bookname_handler
from bot.handlers.overlay import overlay_handler
from bot.handlers.overlay import delogo_handler
from bot.handlers.admin import backup_handler
from bot.handlers.admin import delete_user_handler
from bot.handlers.admin import getting_user_handler
from bot.handlers.admin import database_status_handler
from bot.handlers.admin import env_handler
from bot.handlers.admin import replace_db_handler
from bot.handlers.admin import restart_handler
from bot.handlers.admin import git_handler
# from bot.handlers.admin import reset_chapter_handler 
from bot.handlers.admin.set_commands import set_commands_handler
from bot.handlers.admin.logs import notice_handler
from bot.handlers.admin.logs import flushlogs_handler
from bot.handlers.admin.logs import error_handler

# Order matters
handlers = [

    # Command Handlers
    feedback_handler,
    bookname_handler,
    help_handler,
    overlay_handler,
    delogo_handler,
    show_settings_handler,
    show_botlang_handler,
    show_signlangs_handler,
    show_books_handler,

    env_handler,
    restart_handler,

    # Callback Query Handlers
    page_signlang_handler,
    page_botlang_handler,
    set_lang_handler,

    # inline
    inline_handler,

    # admin handlers
    test_handler,
    delete_user_handler,
    backup_handler,
    flushlogs_handler,
    set_commands_handler,
    getting_user_handler,
    database_status_handler,
    notice_handler,
    replace_db_handler,
    git_handler,

    # reset_chapter_handler,

    start_handler,
    
    # parse bible citation
    parse_bible_handler,
    book_handler,
    chapter_handler,
    verse_handler,

    # fallback all
    all_fallback_handler,
    fallback_query_handler,
]
