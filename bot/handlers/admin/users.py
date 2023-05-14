
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.utils.helpers import mention_markdown
from telegram.error import Unauthorized

from bot.utils import now
from bot.utils.decorators import admin
from bot.database import get
from bot.database import fetch
from bot.database import PATH_DB
from bot.database.schema import User
from bot.handlers.start import start
from bot import AdminCommand
from bot.logs import get_logger
from bot.strings import TextGetter
from bot.database.schema import User



logger = get_logger(__name__)


@admin
def autorizacion(update: Update, context: CallbackContext):
    try:
        new_member_id = int(context.args[0])
    except:
        return
    t = TextGetter(get.user(update.effective_user.id).bot_language.code)

    if not get.user(new_member_id):
        update.message.reply_text(t.warn_user)
        return

    try:
        context.bot.send_message(chat_id=new_member_id, text='🔐')
    except Unauthorized:
        update.message.reply_text(t.user_stopped_bot)
        return
    
    new_db_user = db.set_user(new_member_id, status=User.AUTHORIZED)
    update.message.reply_text(
        text=t.user_added.format(mention_markdown(new_member_id, new_db_user.first_name)),
        parse_mode=ParseMode.MARKDOWN,
    )
    if not get.edition(new_db_user.bot_language.code):
        fetch.bible_books(new_db_user.bot_language.code)

    start(
        update,
        context,
        chat_id=new_member_id,
        first_name=new_db_user.first_name
    )


@admin
def delete_user(update: Update, context: CallbackContext):
    t = TextGetter(get.user(update.effective_user.id).bot_language.code)
    try:
        user_id = int(context.args[0])
    except IndexError:
        return

    if not get.user(user_id):
        update.message.reply_text(t.warn_user)
        return
    db.set_user(user_id, status=User.DENIED)
    update.message.reply_text(t.user_banned)


@admin
def sending_users(update: Update, context: CallbackContext):
    def print_users(users: User, title: str = ''):
        text = f'*{title}*'
        for i, user in enumerate(users, 1):
            text += (
                f'\n{mention_markdown(user.telegram_user_id, user.first_name.split()[0])} '
                f'{user.signlanguage.meps_symbol if user.signlanguage else None} '
                f'{user.bot_language.name} '
                f'`{user.telegram_user_id}`'
                )
            if i % 10 == 0:
                update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
                text = ''
        if text:
            update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    print_users(get.accepted_users(), "ACCEPTED")
    print_users(get.banned_users(), 'BANNED')
    print_users(get.waiting_users(), 'WAITING')

@admin
def backup(update: Update, context: CallbackContext):
    context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=open(PATH_DB, 'rb'),
        filename= f'{now()} {PATH_DB}'
    )


auth_handler = CommandHandler(AdminCommand.ADD, autorizacion)
delete_user_handler = CommandHandler(AdminCommand.BAN, delete_user)
getting_user_handler = CommandHandler(AdminCommand.USERS, sending_users)
backup_handler = CommandHandler(AdminCommand.BACKUP, backup)