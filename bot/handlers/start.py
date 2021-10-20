import logging

from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.ext.messagehandler import MessageHandler
from telegram.utils.helpers import mention_markdown

from bot import MyCommand
from bot import ADMIN
from bot import CHANNEL_ID
from bot.utils.decorators import forw
from bot.database import localdatabase as db


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

TAG_START = '#start'

@forw
def start(update: Update, context: CallbackContext, chat_id: int = None, full_name: str = None) -> None:
    user = update.effective_user
    full_name = full_name or user.first_name
    text = f'Hola {full_name} 👋🏼📖'
    if context.args:
        context.bot.send_message(
            chat_id=ADMIN,
            text=f'{mention_markdown(user.id, user.full_name)} entró desde {context.args[0]}',
            parse_mode=ParseMode.MARKDOWN
        )
    
    db_user = db.get_user(chat_id or update.effective_user.id)
    if db_user is None or not db_user.is_brother():
        db.add_waiting_user(update.effective_user.id, update.effective_user.full_name, update.effective_user.language_code)
        text += 'Este es un bot privado 🔐👤\n\nCuéntame quién eres y por qué quieres usar este bot'
        context.bot.send_message(
            chat_id=ADMIN,
            text=f'{mention_markdown(user.id, user.first_name)} `{user.id}` ha sido bloqueado.',
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
            '\nTe doy la bienvenida al bot de *La Biblia en Lengua de Señas*\n\n'
            'Pídeme un pasaje de la Biblia y te enviaré un video. Por ejemplo\n\n'
            'Mateo 24:14\n'
            'Apocalipsis 21:3, 4\n'
            '2 Timoteo 3:1-5\n'
            'Rom 14:3-5, 23\n'
            'Sal 83\n'
            'Deut\n\n'
            f'Usa /{MyCommand.SIGNLANGUAGE} para elegir una lengua de señas.'
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
        text=f'{TAG_START} {mention_markdown(user.id, user.first_name)} `{user.id}` ha dejado una nota.',
        parse_mode=ParseMode.MARKDOWN,
    )
    context.bot.forward_message(
        CHANNEL_ID,
        update.effective_user.id,
        update.message.message_id
    )
    return ConversationHandler.END


start_handler = ConversationHandler(
    entry_points=[CommandHandler(MyCommand.START, start)],
    states={1: [MessageHandler(Filters.text, whois)]},
    fallbacks=[CommandHandler('cancel', lambda x, y: -1)]
)

@forw
def all_fallback(update: Update, context: CallbackContext) -> None:
    return

all_fallback_handler = MessageHandler(Filters.all, all_fallback)
