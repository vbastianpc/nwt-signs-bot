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

main_fun(1, 2)


PROCEDIMIENTO PARA MODIFICAR BASE DE DATOS EN DB BROWSER SQLITE
    -Borrar todas las views
    OverlayLanguageId
        - En Tablas File y User, Modificar Tabla, Add -> OverlayLanguageId, INTEGER, ForeignKey Language.LanguageId
    BotLanguage
        - En DB Browser Tabla User, Modificar Tabla, BotLanguage -> BotLanguageId
        - Script por cada user
        - En DB Browser Tabla User, Modificar, BotLanguageId -> Integer ForeignKey Language.LanguageId
    BookNamesAbbreviation
        - hacer script para LanguageId
        - db browser

buscar BookNamesAbbreviation


Corrección de bugs:

[x] Filemón, 2 Juan, 3 Juan, Judas (booknums=[57, 63, 64, 65])
    [x] Que entienda, p.ej. Judas 1:17, y Judas 17
        [x] Asumir que chapter=1.
        [x] Revisar regex
    [x] Conseguir versículo de .epub

[x] Corregir si pido Mateo 13, 14, el bot cree que es Mateo 1:3, 4
[ ] /start eliminar "...Pero primero elige una lengua de señas" si ya elegí una lengua de señas
[x] Evaluar la posibilidad de unificar las tablas BibleBook y AbbreviationBibleBook
[x] Eliminar citation de File (?)
[x] Crear canal para logs, interacción usuarios
    [x] Enviar errores para ese canal, no al bot principal
    [x] Canal existente solo para videos, sin mostrar reenviados
    [x] Mensaje de solicitud de ingreso directo al bot, y al canal logs
[-] Multilenguaje descripción
[x] Que se actualicen las lenguas de señas con /signlanguage

[x] Revisar condiciones para enviar versiculos por ID
[x] Overlay
    [ ] Crear conversation_handler. Botones y mostrar si está activo o no.
    [ ] Agregar comando BotCommand multilenguaje.
    [ ] Agregar estado en settings.
    [ ] Explicarlo en help.
[x] Buscar tipografía que tenga todos los idiomas
"""
from telegram.ext import Updater
from bot.secret import TOKEN
from bot.logs import get_logger
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
