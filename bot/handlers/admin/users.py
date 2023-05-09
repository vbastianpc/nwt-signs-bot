
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.utils.helpers import mention_markdown
from telegram.error import Unauthorized
from telegram import BotCommandScopeChat

from bot.utils import now
from bot.utils.decorators import admin
from bot.database import localdatabase as db
from bot.database import PATH_DB
from bot.database.schemedb import User
from bot.handlers.start import start
from bot import AdminCommand
from bot.logs import get_logger
from bot import strings
from bot.strings import TextGetter
from bot.strings import botlangs
from bot.booknames import booknames
from bot.database.schemedb import User



logger = get_logger(__name__)


@admin
def autorizacion(update: Update, context: CallbackContext):
    try:
        new_member_id = int(context.args[0])
    except:
        return
    t = TextGetter(db.get_user(update.effective_user.id).bot_language.code)

    if not db.get_user(new_member_id):
        update.message.reply_text(t.warn_user)
        return

    try:
        context.bot.send_message(chat_id=new_member_id, text='🔐')
    except Unauthorized:
        update.message.reply_text(t.user_stopped_bot)
        return
    
    new_db_user = db.set_user(new_member_id, status=User.AUTHORIZED)
    update.message.reply_text(
        text=t.user_added.format(mention_markdown(new_member_id, new_db_user.full_name)),
        parse_mode=ParseMode.MARKDOWN,
    )
    if not db.get_bible(new_db_user.bot_language.code):
        db.fetch_bible_books(new_db_user.bot_language)

    start(
        update,
        context,
        chat_id=new_member_id,
        full_name=new_db_user.full_name
    )


@admin
def delete_user(update: Update, context: CallbackContext):
    t = TextGetter(db.get_user(update.effective_user.id).bot_language.code)
    try:
        user_id = int(context.args[0])
    except IndexError:
        return

    if not db.get_user(user_id):
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
                f'\n{mention_markdown(user.telegram_user_id, user.full_name.split()[0])} '
                f'{user.signlanguage.meps_symbol if user.signlanguage else None} '
                f'{user.bot_language.name} '
                f'`{user.telegram_user_id}`'
                )
            if i % 10 == 0:
                update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
                text = ''
        if text:
            update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    print_users(db.get_accepted_users(), "ACCEPTED")
    print_users(db.get_banned_users(), 'BANNED')
    print_users(db.get_waiting_users(), 'WAITING')

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