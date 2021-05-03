import json
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram.constants import MAX_MESSAGE_LENGTH

from models import UserController as uc
from utils import BIBLE_BOOKNAMES, BIBLE_NUM_BOOKALIAS, BIBLE_BOOKALIAS_NUM
from utils.decorators import vip, admin, forw

logger = logging.getLogger(__name__)


@admin
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
@vip
def text_fallback(update: Update, context: CallbackContext) -> None:
    fail = update.message.text[0].lower() if update.message.text else None
    if fail is None:
        logger.warning('%s', update.message)
    maybe = [
        f'/{bookalias} - {BIBLE_BOOKNAMES[booknum - 1]}'
        for bookalias, booknum in BIBLE_BOOKALIAS_NUM.items() if bookalias.startswith(fail)
    ]
    if maybe:
        text = 'Puedes usar las abreviaciones de la Biblia para pedirme un versículo. ' \
            'Puedes ver el listado completo escribiendo o presionando el símbolo slash `/`\n\n' \
            '¿Quizá quieres decir... 🤔?\n' \
            + '\n'.join(maybe)
        update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@forw
def all_fallback(update: Update, context: CallbackContext) -> None:
    return


@admin
def notice(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Envíame los mensajes que quieres que reenvíe a todos los usuarios. '
        'Pueden ser stickers, gifs, videos, imágenes, lo que sea. '
        'Cuando estés listo, escribe /ok. Para cancelar usa /cancel'
    )
    context.user_data['notices'] = []
    return 1


def get_notice(update: Update, context: CallbackContext):
    context.user_data['notices'].append(update.message)
    return 1

def send_notice(update: Update, context: CallbackContext):
    for msg in context.user_data['notices']:
        for user_id in uc.get_users_id():
            context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=update.effective_user.id,
                message_id=msg.message_id,
            )
    update.message.reply_text('Mensajes enviados')
    del context.user_data['notices']
    return -1

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text('No enviaré nada.')
    del context.user_data['notices']
    return -1


botfather_handler = CommandHandler('commands', paraBotFather)
test_handler = CommandHandler('test', test_data)
info_inline_handler = CommandHandler('inline', info_inline)

text_fallback_handler = MessageHandler(Filters.text, text_fallback)
all_fallback_handler = MessageHandler(Filters.all, all_fallback)

notice_handler = ConversationHandler(
    entry_points=[CommandHandler('notice', notice)],
    states={
        1: [CommandHandler('ok', send_notice),
            MessageHandler(Filters.all, get_notice)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)
