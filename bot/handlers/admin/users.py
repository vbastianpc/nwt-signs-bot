
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.utils.helpers import mention_markdown
from telegram.error import Unauthorized

from bot import MyCommand
from bot.utils import now
from bot.utils.decorators import admin
from bot.database import get
from bot.database import add
from bot.database import fetch
from bot.database import PATH_DB
from bot.database.schema import User
from bot import AdminCommand
from bot.logs import get_logger
from bot.strings import TextTranslator


logger = get_logger(__name__)


@admin
def autorizacion(update: Update, context: CallbackContext):
    try:
        new_telegram_id = int(context.args[0])
    except (IndexError, ValueError):
        return
    admin_user = get.user(update.effective_user.id)
    tt = TextTranslator(admin_user.bot_language.code)

    if not get.user(new_telegram_id):
        update.message.reply_text(tt.warn_user)
        return

    try:
        context.bot.send_message(chat_id=new_telegram_id, text='🔐')
    except Unauthorized:
        update.message.reply_text(tt.user_stopped_bot)
        return
    
    new_user = add.or_update_user(new_telegram_id, status=User.AUTHORIZED)
    update.message.reply_text(
        text=tt.user_added(mention_markdown(new_telegram_id, f'{new_user.first_name} {new_user.last_name}'),
                           new_telegram_id),
        parse_mode=ParseMode.MARKDOWN)

    if not get.edition(new_user.bot_language.code):
        fetch.editions()
    if not get.books(new_user.bot_language.code):
        fetch.books(new_user.bot_language.code)
    context.bot.send_message(chat_id=new_telegram_id, text=tt.step_1(new_user.first_name, MyCommand.START))


@admin
def delete_user(update: Update, context: CallbackContext):
    t = TextTranslator(get.user(update.effective_user.id).bot_language.code)
    try:
        user = get.user(int(context.args[0]))
    except (IndexError, ValueError):
        update.message.reply_text(t.warn_user)
        return
    add.or_update_user(user.telegram_user_id, status=User.DENIED)
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
    print_users(get.accepted_users(), User.AUTHORIZED)
    print_users(get.banned_users(), User.DENIED)
    print_users(get.waiting_users(), User.WAITING)


@admin
def backup(update: Update, context: CallbackContext):
    context.bot.send_document(chat_id=update.effective_chat.id,
                              document=open(PATH_DB, 'rb'),
                              filename= f'{now()} {PATH_DB}')


auth_handler = CommandHandler(AdminCommand.ADD, autorizacion)
delete_user_handler = CommandHandler(AdminCommand.BAN, delete_user)
getting_user_handler = CommandHandler(AdminCommand.USERS, sending_users)
backup_handler = CommandHandler(AdminCommand.BACKUP, backup)