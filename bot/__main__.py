#!/usr/bin/env python
"""
TODO
ver cambios en database y mudar (agregar columnas, renombrar columnas)
solucionar handler de comandos en diferentes situaciones
/asl mateo 24:14 - Definido, finito. 
/mat 24:14 - Filter.command atajar todos los comandos. Verificar en database

Comandos Scopes mostrando libros booknames por idioma

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
import logging

from telegram.ext import Updater

from bot import TOKEN
from bot.handlers import handlers, error_handler


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
    dispatcher.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()
