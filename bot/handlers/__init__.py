from handlers.bible import parse_handler
from handlers.settings import lang_handler, quality_handler
from handlers.inline_bible import inline_handler, inline_fallback_handler
from handlers.misc import (botfather_handler, test_handler, info_inline_handler,
                           text_fallback_handler, all_fallback_handler)
from handlers.auth import (start_handler, auth_handler, permiso_handler,
                           delete_user_handler, getting_user_handler, helper_admin_handler)

# Order matters
handlers = [
    parse_handler,
    inline_handler,
    inline_fallback_handler,
    start_handler,
    test_handler,
    lang_handler,
    quality_handler,
    auth_handler,
    permiso_handler,
    info_inline_handler,
    delete_user_handler,
    botfather_handler,
    getting_user_handler,
    helper_admin_handler,
    text_fallback_handler,
    all_fallback_handler,
]
