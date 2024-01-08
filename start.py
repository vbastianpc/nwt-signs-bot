#!/usr/bin/env python
"""
TODO
https://evertype.com/standards/iso639/sgn.html
solucionar tema session
    - session decorador para thread safe?

def with_session(func):
    session = new_session()
    def image_func(a, b):
        print(f'{a=} {b=}')
        return func(session, a, b)
    return image_func

@with_session
def main_func(session, first, second):
    print(f'{session=} {first=} {second=}')

main_func(1, 2)

[-] Multilenguaje descripción
"""

from telegram.ext import Updater
from bot.secret import TOKEN, ADMIN
from bot.logs import get_logger
from bot.handlers import handlers, error_handler


logger = get_logger(__name__)


if __name__ == '__main__':
    updater = Updater(TOKEN)
    for handler in handlers:
        updater.dispatcher.add_handler(handler)
    updater.dispatcher.add_error_handler(error_handler)
    updater.start_polling()
    updater.bot.send_message(
        chat_id=ADMIN, text='Bot is running 🤖'
    )
    updater.idle()
