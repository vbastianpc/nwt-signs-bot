import logging

from telegram import Update, ParseMode
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          MessageHandler, Filters)
from telegram.ext.messagehandler import MessageHandler
from telegram.utils.helpers import mention_markdown
from telegram.constants import MAX_MESSAGE_LENGTH

from bot import ADMIN
from bot import CHANNEL_ID
from bot.utils.decorators import admin, forw
from bot.database import localdatabase as db
 

logger = logging.getLogger(__name__)
TAG_AUTH = '#auth'

@forw
def start(update: Update, context: CallbackContext, chat_id: int = None, full_name: str = None) -> None:
    user = update.effective_user
    full_name = full_name or user.first_name
    text = f'Hola {full_name}. '
    if context.args:
        context.bot.send_message(
            chat_id=ADMIN,
            text=f'{mention_markdown(user.id, user.full_name)} entró desde {context.args[0]}',
            parse_mode=ParseMode.MARKDOWN
        )
    logger.info(f'{update.effective_user=} {chat_id=}')
    
    db_user = db.get_user(chat_id or update.effective_user.id)
    if db_user is None or not db_user.is_brother():
        db.add_waiting_user(update.effective_user.id, update.effective_user.full_name)
        text += 'Este es un bot privado 🔐👤\n\nCuéntame quién eres y por qué quieres usar este bot'
        context.bot.send_message(
            chat_id=ADMIN,
            text=f'{TAG_AUTH} {mention_markdown(user.id, user.first_name)} `{user.id}` ha sido bloqueado.',
            parse_mode=ParseMode.MARKDOWN
        )
        context.bot.send_message(
            chat_id=update.effective_user.id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
        )
        return 1
    else:
        text += (
            '\n\nEscribe el pasaje de la Biblia que necesites, por ejemplo\n\n'
            'Mateo 24:14\n'
            'Apocalipsis 21:3, 4\n'
            '2 Timoteo 3:1-5\n'
            'Rom 14:3-5, 23\n'
            'Sal 83\n'
            'Deut\n\n'
            'Presiona /lang para elegir una lengua de señas.\n'
        )

    context.bot.send_message(
        chat_id=chat_id if chat_id else update.effective_user.id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
    )


def whois(update: Update, context: CallbackContext):
    update.message.reply_text('Bien. Espera a que el administrador te acepte.')
    user = update.effective_user
    context.bot.send_message(
        chat_id=ADMIN,
        text=f'{TAG_AUTH} {mention_markdown(user.id, user.first_name)} `{user.id}` ha dejado una nota.',
        parse_mode=ParseMode.MARKDOWN,
    )
    context.bot.forward_message(
        CHANNEL_ID,
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
        db_user = db.set_user(new_member_id, brother=True)
    except Exception as e:
        logger.error(e)
        return
    else:
        context.bot.send_message(
            chat_id=new_member_id,
            text=f'🔐',
        )
    update.message.reply_text(
        text=f'{mention_markdown(new_member_id, db_user.full_name)} ha sido aceptado',
        parse_mode=ParseMode.MARKDOWN,
    )
    start(
        update,
        context,
        chat_id=new_member_id,
        full_name=db_user.full_name
    )


@admin
def delete_user(update: Update, context: CallbackContext):
    try:
        db.set_user(int(context.args[0]), blocked=True)
    except IndexError:
        update.message.reply_text('Usa /delete [user_id]')
    except:
        update.message.reply_text('El usuario no estaba registrado en la base de datos')
    else:
        update.message.reply_text('Usuario bloqueado')


@admin
def sending_users(update: Update, context: CallbackContext):
    users = db.get_all_users()
    text = ''
    for i, user in enumerate(users):
        format_user = f'{mention_markdown(user.telegram_user_id, user.full_name)} {user.parent.lang_code} `{user.telegram_user_id}`\n'
        if i % 10 == 0:
            update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            text = ''
        else:
            text += format_user
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