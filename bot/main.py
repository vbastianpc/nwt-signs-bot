#!/usr/bin/env python

import logging

from telegram import Update
from telegram.ext import Updater, CallbackContext

from handlers import handlers
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
    for handler in handlers:
        dispatcher.add_handler(handler)
    dispatcher.add_error_handler(log_error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
