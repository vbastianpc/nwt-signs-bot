import json
import logging

from telegram import Update
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler

from bot.utils.decorators import admin, forw
from bot import MyCommand

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


@forw
def info_inline(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=('Busca y envía pasajes de la Biblia directamente en el chat de un amigo. '
              'Ve a un chat de tus contactos y escribe el nombre del bot seguido de un '
              'texto de la biblia. Por ejemplo:\n\n'
              f'@{context.bot.get_me().username} Mat 24:14\n\n'
              'Te mostraré los versículos que ya hayan sido utilizados antes.'
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text='Probar modo inline en chat de un amigo',
                switch_inline_query='',
            )],
            [InlineKeyboardButton(
                text='Probar modo inline aquí mismo',
                switch_inline_query_current_chat=''
            )]
        ]),
    )


info_inline_handler = CommandHandler(MyCommand.INLINE, info_inline)