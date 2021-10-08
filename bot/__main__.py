#!/usr/bin/env python
"""
Agregar handler para actualizar lenguas
"""
import logging

from telegram import Update
from telegram.ext import Updater, CallbackContext

from bot import TOKEN
from bot.handlers import handlers


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)



if __name__ == '__main__':
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    for handler in handlers:
        dispatcher.add_handler(handler)
    updater.start_polling()
    updater.idle()
