
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.utils.helpers import mention_html
from telegram.error import Unauthorized

from bot import MyCommand
from bot.utils import now
from bot.utils.decorators import vip, admin
from bot.database import get
from bot.database import add
from bot.database import fetch
from bot.database import PATH_DB
from bot.database.schema import User
from bot import AdminCommand
from bot.logs import get_logger
from bot.strings import TextTranslator


logger = get_logger(__name__)


@vip
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
        text=tt.user_added(mention_html(new_telegram_id, f'{new_user.first_name} {new_user.last_name}'),
                           new_telegram_id),
        parse_mode=ParseMode.HTML)

    if not get.edition(new_user.bot_language.code):
        fetch.editions()
    if not get.books(new_user.bot_language.code):
        fetch.books(new_user.bot_language.code)
    tt2 = TextTranslator(new_user.bot_language_code)
    context.bot.send_message(chat_id=new_telegram_id, text=tt2.step_1(new_user.first_name, MyCommand.START))


@vip
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


@vip
@admin
def sending_users(update: Update, _: CallbackContext):
    def print_users(users: list[User], title: str = ''):
        text = ''
        for i, user in enumerate(users, 1):
            text += (
                f'\n{mention_html(user.telegram_user_id, user.first_name.split()[0])} '
                f'{user.sign_language.meps_symbol if user.sign_language else None} '
                f'{user.bot_language.code} '
                f'<code>{user.telegram_user_id}</code>'
                )
            if i % 20 == 0:
                update.message.reply_text(text, parse_mode=ParseMode.HTML)
                text = ''
        if text:
            update.message.reply_text(f'<b>{title}</b>' + text, parse_mode=ParseMode.HTML)
    print_users(get.accepted_users(), 'AUTHORIZED')
    print_users(get.banned_users(), 'DENIED')
    print_users(get.waiting_users(), 'WAITING')


@vip
@admin
def backup(update: Update, context: CallbackContext):
    context.bot.send_document(chat_id=update.effective_chat.id,
                              document=open(PATH_DB, 'rb'),
                              filename= f'{now()} {PATH_DB}')


auth_handler = CommandHandler(AdminCommand.ADD, autorizacion)
delete_user_handler = CommandHandler(AdminCommand.BAN, delete_user)
getting_user_handler = CommandHandler(AdminCommand.USERS, sending_users)
backup_handler = CommandHandler(AdminCommand.BACKUP, backup)
