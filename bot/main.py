#!/usr/bin/env python

import logging

from telegram import Update
from telegram.ext import Updater, CallbackContext

from handlers import (
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
)
from secret import TOKEN


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def log_error(_: Update, context: CallbackContext) -> None:
    logger.error(context.error)


def main() -> None:
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
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
    for handler in handlers:
        dispatcher.add_handler(handler)
    dispatcher.add_error_handler(log_error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
