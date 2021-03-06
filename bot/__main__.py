#!/usr/bin/env python
"""
TODO
solucionar tema SESSION
    - SESSION decorador para thread safe?

def with_session(func):
    session = new_session()
    def image_func(a, b):
        print(f'{a=} {b=}')
        return func(session, a, b)
    return image_func

@with_session
def main_func(session, first, second):
    print(f'{session=} {first=} {second=}')

main_fun(1, 2)

"""
from telegram.ext import Updater
from bot import TOKEN, get_logger
from bot.handlers import handlers, error_handler


logger = get_logger(__name__)


if __name__ == '__main__':
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    for handler in handlers:
        dispatcher.add_handler(handler)
    dispatcher.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()
