import json
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram.constants import MAX_MESSAGE_LENGTH

from models import UserController as uc
from utils import BIBLE_BOOKNAMES, BIBLE_NUM_BOOKALIAS
from utils.decorators import admin, forw


logger = logging.getLogger(__name__)


@admin
def test_data(update: Update, context: CallbackContext) -> None:
    if not context.args:
        data = sorted(context.user_data.keys())
    else:
        varname = context.args[0].split('.')[0]
        attr_keys = '.'.join(context.args[0].split('.')[1:])
        e = f'context.user_data.get("{varname}")' + (('.' + attr_keys) if attr_keys else '')
        data = eval(e)

    try:
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
    except TypeError:
        json_data = str(data)
    except:
        json_data = json.dumps(data, indent=2, ensure_ascii=False, default=lambda x: x.__dict__)
    update.message.reply_markdown_v2(f'```\n{json_data[:MAX_MESSAGE_LENGTH]}```')


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
        ('lang', '[código] Cambia la lengua de señas'),
        ('quality', 'Cambia la calidad de los videos'),
        ('inline', 'Aprende a usar el modo inline'),
        ('feedback', 'Send me your feedback'),
    ] + [
        (cmd, BIBLE_BOOKNAMES[num - 1]) for num, cmd in sorted(BIBLE_NUM_BOOKALIAS.items())
    ]
    context.bot.set_my_commands(commands)

    text = '\n'.join([f'{cmd} - {descrip}' for cmd, descrip in commands])
    update.message.reply_text(text)
    update.message.reply_text('Comandos actualizados')


@forw
def all_fallback(update: Update, context: CallbackContext) -> None:
    return


@admin
def notice(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Envíame los mensajes que quieres que reenvíe. '
        'Pueden ser stickers, gifs, videos, imágenes, lo que sea. '
        'Cuando estés listo, escribe /ok. Para cancelar usa /cancel'
    )
    context.user_data['notices'] = []
    context.user_data['target_user'] = context.args or None
    return 1


def get_notice(update: Update, context: CallbackContext):
    context.user_data['notices'].append(update.message)
    return 1

def send_notice(update: Update, context: CallbackContext):
    users = context.user_data['target_user'] or uc.get_users_id()
    for msg in context.user_data['notices']:
        for user_id in users:
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


@admin
def logs(update: Update, context: CallbackContext):
    try:
        with open('./log.log', 'r', encoding='utf-8') as f:
            data = f.read()
    except FileNotFoundError:
        update.message.reply_text('No hay archivo log')
    else:
        update.message.reply_markdown_v2(f'```{data[-MAX_MESSAGE_LENGTH::]}```')
    return


@admin
def logfile(update: Update, context: CallbackContext):
    try:
        context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=open('./log.log', 'rb'),
        )
    except FileNotFoundError:
        update.message.reply_text('No hay archivo log')


botfather_handler = CommandHandler('commands', paraBotFather)
test_handler = CommandHandler('test', test_data)
info_inline_handler = CommandHandler('inline', info_inline)

all_fallback_handler = MessageHandler(Filters.all, all_fallback)

notice_handler = ConversationHandler(
    entry_points=[CommandHandler('notice', notice)],
    states={
        1: [CommandHandler('ok', send_notice),
            CommandHandler('cancel', cancel),
            MessageHandler(Filters.all, get_notice)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

logs_handler = CommandHandler('logs', logs)
logfile_handler = CommandHandler('logfile', logfile)