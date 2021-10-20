import logging

from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from bot import AdminCommand

from bot.utils.decorators import admin
from bot.database import report as db


@admin
def database_status(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        '<pre>'
        f'{db.count_videomarker():>5} Marcadores guardados\n'
        f'{db.count_sentverse():>5} Versículos enviados\n'
        f'{db.count_biblechapter():>5} Videos consultados\n'
        f'{db.count_biblebook():>5} Libros consultados\n'
        f'{db.count_signlanguage():>5} Lenguas de señas usadas\n\n'
        f'{db.count_user_brother():>5} Usuarios permitidos\n'
        f'{db.count_user_blocked():>5} Usuarios bloqueados\n'
        f'{db.count_user_waiting():>5} Usuarios en lista de espera\n'
        f'{db.count_user():>5} Usuarios en total\n'
        '</pre>',
    parse_mode=ParseMode.HTML
    )

database_status_handler = CommandHandler(AdminCommand.STATS, database_status)
