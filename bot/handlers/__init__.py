from .bible import (parse_bible_re_handler, parse_bible_cmd_handler,
                    chapter_handler, verse_handler)
from .settings import lang_handler, quality_handler
from .inline_bible import inline_handler
from .misc import (botfather_handler, test_handler, info_inline_handler,
                   all_fallback_handler, notice_handler)
from .auth import (start_handler, auth_handler, permiso_handler,
                   delete_user_handler, getting_user_handler, helper_admin_handler)

# Order matters
handlers = [
    inline_handler,
    start_handler,
    test_handler,
    lang_handler,
    quality_handler,
    auth_handler,
    permiso_handler,
    info_inline_handler,
    delete_user_handler,
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
