import json
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.constants import MAX_MESSAGE_LENGTH
from telegram.utils.helpers import mention_markdown

from models import UserController as uc
from utils import BIBLE_BOOKNAMES, BIBLE_NUM_BOOKALIAS, BIBLE_BOOKALIAS_NUM
from utils.decorators import vip, admin, forw

logger = logging.getLogger(__name__)



def test_data(update: Update, context: CallbackContext) -> None:
    data = context.user_data.get(context.args[0]) if context.args else sorted(context.user_data.keys())
    js = json.dumps(data, indent=2)[:MAX_MESSAGE_LENGTH - 10]
    update.message.reply_markdown_v2(f'```\n{js}\n```')


@forw
def info_inline(update: Update, context: CallbackContext) -> None:
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=('Busca y envía pasajes de la Biblia directamente en el chat de un amigo. '
              'Ve a un chat de tus contactos y escribe el nombre del bot seguido de un '
              'texto de la biblia. Por ejemplo:\n\n'
              f'@{context.bot.get_me().username} Mat 24:14'),
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

@admin
def paraBotFather(update: Update, context: CallbackContext):
    commands = [
        ('start', 'Mensaje de bienvenida'),
        ('lang', 'Cambia la lengua de señas'),
        ('quality', 'Cambia la calidad de los videos'),
        ('inline', 'Aprende a usar el modo inline'),
    ] + [
        (cmd, BIBLE_BOOKNAMES[num - 1]) for num, cmd in sorted(BIBLE_NUM_BOOKALIAS.items())
    ]
    context.bot.set_my_commands(commands)

    text = '\n'.join([f'{cmd} - {descrip}' for cmd, descrip in commands])
    update.message.reply_text(text)
    update.message.reply_text('Comandos actualizados')


@forw
def text_fallback(update: Update, context: CallbackContext) -> None:
    fail = update.message.text[0].lower()
    maybe = ['/' + bookalias for bookalias in BIBLE_BOOKALIAS_NUM if bookalias.startswith(fail)]
    if maybe:
        text = 'Usa las abreviaciones de la Biblia para pedirme un versículo.\n\n' \
            '¿Quizá quieres decir... 🤔?\n' \
            + '\n'.join(maybe)
    else:
        text = 'Usa las abreviaciones de la Biblia para pedirme un versículo. '\
            'Presiona o escribe el símbolo slash `/` para conocerlas.'
    update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@forw
def all_fallback(update: Update, context: CallbackContext) -> None:
    return


botfather_handler = CommandHandler('commands', paraBotFather)
test_handler = CommandHandler('test', test_data)
info_inline_handler = CommandHandler('inline', info_inline)

text_fallback_handler = MessageHandler(Filters.text, text_fallback)
all_fallback_handler = MessageHandler(Filters.all, all_fallback)