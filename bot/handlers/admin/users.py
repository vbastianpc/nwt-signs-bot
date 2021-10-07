import logging

from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.utils.helpers import mention_markdown

from bot.utils.decorators import admin
from bot.database import localdatabase as db
from bot.database import PATH_DB
from bot.handlers.start import start


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


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
    update.message.reply_text(
        text=f'{mention_markdown(new_member_id, db_user.full_name)} ha sido aceptado',
        parse_mode=ParseMode.MARKDOWN,
    )
    context.bot.send_message(chat_id=new_member_id, text=f'🔐')
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
    for i, user in enumerate(users, 1):
        text += f'{mention_markdown(user.telegram_user_id, user.full_name)} {user.lang_code} `{user.telegram_user_id}`\n'
        if i % 10 == 0:
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
        document=open(PATH_DB, 'rb'),
        filename= f'{db.now()} {PATH_DB}'
    )


auth_handler = CommandHandler('auth', autorizacion)
delete_user_handler = CommandHandler('delete', delete_user)
getting_user_handler = CommandHandler('users', sending_users)
helper_admin_handler = CommandHandler('admin', help_admin)
backup_handler = CommandHandler('backup', backup)