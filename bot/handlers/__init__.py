from handlers.bible import parse_handler
from handlers.settings import lang_handler, quality_handler
from handlers.inline_bible import inline_handler, inline_fallback_handler
from handlers.misc import (botfather_handler, test_handler, info_inline_handler,
                           text_fallback_handler, all_fallback_handler)
from handlers.auth import (start_handler, auth_handler, permiso_handler,
                           delete_user_handler, getting_user_handler, helper_admin_handler)