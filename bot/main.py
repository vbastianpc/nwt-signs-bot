#!/usr/bin/env python

"""
TODO
[x] Funcion para mandar mensaje a todos. Para novedades
[x] bible.py cambiar a Handlers individuales. Eliminar ConversationHandler.
Falta manejar mejor menu de botones. Borrar o editar.
Si manda botones con capitulos o versiculos, cada boton debe tener la informacion de booknum, chapter y verse

[ ] Agregar emojis a los mensajes informativos
[ ] Aprender a documentar en python
[ ] Hacer REadme.md

"""
import logging

from telegram import Update
from telegram.ext import Updater, CallbackContext

from handlers import handlers
from utils.secret import TOKEN


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
    # dispatcher.add_error_handler(log_error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
