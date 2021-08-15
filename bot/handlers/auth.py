import json
import logging

from telegram import Update, ParseMode, User, chat, parsemode
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          MessageHandler, Filters)
from telegram.error import BadRequest, Unauthorized
from telegram.ext.messagehandler import MessageHandler
from telegram.utils.helpers import mention_markdown
from telegram.constants import MAX_MESSAGE_LENGTH

from utils.secret import ADMIN
from utils.decorators import admin, forw
from models import UserController as uc
 

logger = logging.getLogger(__name__)


@forw
def start(update: Update, context: CallbackContext, chat_id: int = None, first_name: str = None) -> None:
    user = update.effective_user
    first_name = first_name or user.first_name
    text = f'Hola {first_name}. '
    if context.args:
        context.bot.send_message(
            chat_id=ADMIN,
            text=f'{mention_markdown(user.id, user.first_name)} entró desde {context.args[0]}',
            parse_mode=ParseMode.MARKDOWN
        )
    if user.id in uc.get_users_id():
        text += (
            '\n\nEscribe el pasaje de la Biblia que necesites, por ejemplo\n\n'
            'Mateo 24:14\n'
            'Apocalipsis 21:3, 4\n'
            '2 Timoteo 3:1-5\n'
            'Rom 14:3-5, 23\n'
            'Sal 83\n'
            'Deut\n\n'
            'Usa /lang para cambiar tu lengua de señas.\n'
            'Usa /quality para cambiar la calidad de tus videos.'
        )
    else:
        text += 'Este es un bot privado 🔐👤\n\nCuéntame quién eres y por qué quieres usar este bot'
        context.bot.send_message(
            chat_id=ADMIN,
            text=f'{mention_markdown(user.id, user.first_name)} ha sido bloqueado.',
            parse_mode=ParseMode.MARKDOWN
        )

    context.bot.send_message(
        chat_id=chat_id if chat_id else update.effective_chat.id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
    )
    if not user.id in uc.get_users_id():
        return 1


def whois(update: Update, context: CallbackContext):
    update.message.reply_text('Bien. Espera a que el administrador te acepte.')
    user = update.effective_user
    context.bot.send_message(
        chat_id=ADMIN,
        text=f'{user.id} {mention_markdown(user.id, user.first_name)} ha dejado una nota.',
        parse_mode=ParseMode.MARKDOWN,
    )
    context.bot.forward_message(
        ADMIN,
        update.effective_user.id,
        update.message.message_id
    )
    return ConversationHandler.END


@admin
def autorizacion(update: Update, context: CallbackContext):
    if not context.args:
        return
    try:
        new_member_id = int(context.args[0])
        msg = context.bot.send_message(
            chat_id=new_member_id,
            text=f'Has sido aceptado.',
        )
        uc.add_user(new_member_id, msg.chat.full_name)
        start(
            update,
            context,
            chat_id=new_member_id,
            first_name=msg.chat.first_name
        )
    except BadRequest:
        update.message.reply_text('Parece que el id no es correcto')
    except Unauthorized:
        update.message.reply_text(
            text=(f'{mention_markdown(new_member_id, str(new_member_id))} no ha podido'
                  ' ser aceptado porque ha bloqueado al bot'),
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        update.message.reply_text(
            text=f'{mention_markdown(new_member_id, msg.chat.full_name)} ha sido aceptado',
            parse_mode=ParseMode.MARKDOWN,
        )


@admin
def delete_user(update: Update, context: CallbackContext):
    try:
        context.args[0]
    except IndexError:
        update.message.reply_text('Usa /delete [user_id]')
        return
    else:
        state = uc.remove_user(int(context.args[0]))
    if state:
        update.message.reply_text('Usuario eliminado')
    else:
        update.message.reply_text('Usuario no estaba registrado')


@admin
def sending_users(update: Update, context: CallbackContext):
    users = uc.pretty_users()
    text = ''
    for user in users:
        if len(text+user) + 1 <= MAX_MESSAGE_LENGTH:
            text += user + '\n'
        else:
            update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            text = ''
    if text:
        update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@admin
def help_admin(update: Update, context: CallbackContext):
    update.message.reply_text(
        text=(
            '/auth [user_id] - Agrega un nuevo usuario\n'
            '/delete [user_id] - Elimina un usuario\n'
            '/users - Muestra un listado de los usuarios\n'
            '/test [key] - Muestra diccionarios user_data\n'
            '/commands - Setea los comandos para BotFather\n'
            '/notice [user_id1 user_id2] - Enviar mensajes\n'
            '/backup - Realizar copia de seguridad\n'
            '/logs - Muestra últimos logs\n'
            '/logfile - Envía el archivo completo de logs'
        )
    )

@admin
def backup(update: Update, context: CallbackContext):
    context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open('./jw_data.json', 'rb'),
    )
    context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open('./users.json', 'rb'),
    )


start_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={1: [MessageHandler(Filters.text, whois)]},
    fallbacks=[CommandHandler('cancel', lambda x, y: -1)]
)
auth_handler = CommandHandler('auth', autorizacion)
delete_user_handler = CommandHandler('delete', delete_user)
getting_user_handler = CommandHandler('users', sending_users)
helper_admin_handler = CommandHandler('admin', help_admin)
backup_handler = CommandHandler('backup', backup)