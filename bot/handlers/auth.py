import json
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.error import BadRequest, Unauthorized
from telegram.utils.helpers import mention_markdown
from telegram.constants import MAX_MESSAGE_LENGTH

from secret import ADMIN
from decorators import vip, admin, forw
from users import add_user, remove_user, get_users
 

logger = logging.getLogger(__name__)


@vip
def start(update: Update, context: CallbackContext, chat_id: int = None, first_name: str = None) -> None:
    text = (
        f'Hola {first_name if first_name else update.effective_user.first_name}. '
        'Escribe el versículo que necesites y te lo enviaré. Por ejemplo\n\n'
        '`Mat 24:14`\n\n'
        "Usa las abreviaciones de los libros de la Biblia. Escribe o presiona el símbolo slash '`/`' para conocerlas.\n\n"
        'Para cambiar la lengua de señas, usa el comando /lang'
    )
    context.bot.send_message(
        chat_id=chat_id if chat_id else update.effective_chat.id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
    )


@admin
def autorizacion(update: Update, context: CallbackContext):
    if not context.args:
        return
    try:
        new_member_id = int(context.args[0])
        msg = context.bot.send_message(
            chat_id=new_member_id,
            text='Has sido aceptado. Ya puedes usar este bot.',
        )
        add_user(new_member_id, msg.chat.full_name)
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


def permiso(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=ADMIN,
        text=(f'{mention_markdown(update.effective_user.id, update.effective_user.name)} '
              f'`{update.effective_user.id}` Ha solicitado ingresar.'),
        parse_mode=ParseMode.MARKDOWN
    )
    update.message.reply_text('Debes esperar a que tu solicitud sea aceptada')


@admin
def delete_user(update: Update, context: CallbackContext):
    try:
        context.args[0]
    except IndexError:
        update.message.reply_text('Usa /delete [user_id]')
        return
    else:
        state = remove_user(context.args[0])
    if state:
        update.message.reply_text('Usuario eliminado')
    else:
        update.message.reply_text('Usuario no estaba registrado')


@admin
def sending_users(update: Update, context: CallbackContext):
    users = [f'{mention_markdown(user_id, data["name"])} `{user_id}` {data["lang"]} {data["quality"]}'
             for user_id, data in get_users().items()]
    text = ''
    for user in users:
        if len(text+user) + 1 <= MAX_MESSAGE_LENGTH:
            text += user + '\n'
        else:
            update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
            text = ''
    if text: update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@admin
def help_admin(update: Update, context: CallbackContext):
    update.message.reply_text(
        text=(
            '/auth [user_id] - Agrega un nuevo usuario\n'
            '/delete [user_id] - Elimina un usuario\n'
            '/users - Muestra un listado de los usuarios\n'
            '/test [key] - Muestra diccionarios user_data\n'
            '/commands - Setea los comandos para BotFather'
        )
    )

start_handler = CommandHandler('start', start)

auth_handler = CommandHandler('auth', autorizacion)
permiso_handler = CommandHandler('permiso', permiso)
delete_user_handler = CommandHandler('delete', delete_user)
getting_user_handler = CommandHandler('users', sending_users)
helper_admin_handler = CommandHandler('admin', help_admin)