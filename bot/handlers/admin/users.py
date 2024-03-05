import io
from datetime import datetime

from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.utils.helpers import mention_html
from telegram.error import Unauthorized

from bot import MyCommand
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
def delete_user(update: Update, context: CallbackContext):
    tt: TextTranslator = context.user_data['tt']
    try:
        user = get.user(int(context.args[0]))
    except (IndexError, ValueError):
        update.message.reply_text(tt.warn_user)
        return
    add.or_update_user(user.telegram_user_id, status=User.DENIED)
    update.message.reply_text(tt.user_banned)


@vip
@admin
def sending_users(update: Update, _: CallbackContext):
    table = ('<tr>'
        '<th>id</th>'
        '<th>FullName</th>'
        '<th>UserName</th>'
        '<th>IsPremium</th>'
        '<th>SL1</th>'
        '<th>SL2</th>'
        '<th>SL3</th>'
        '<th>BL</th>'
        '<th>Overlay</th>'
        '<th>Status</th>'
        '<th>AddedDatetime</th>'
        '<th>LastActive</th>'
        '<th>Delogo</th>'
        '</tr>'
    )
    users = get.users()
    for u in users:
        row = ''.join([f'<td>{c}</td>' for c in [
            u.id,
            mention_html(u.telegram_user_id, u.full_name),
            u.user_name,
            u.is_premium or '',
            u.sign_language_code or '',
            u.sign_language_code2 or '',
            u.sign_language_code3 or '',
            u.bot_language_code,
            u.overlay_language_code or '',
            u.status,
            u.added_datetime or '',
            u.last_active_datetime or '',
            int(u.delogo),
        ]])
        table += f'<tr>{row}</tr>'
    html = ('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
            table,
            td,
            th {
                border: 1px solid;
                width: 100%;
                border-collapse: collapse;
                font-family: helvetica;
            }

            th {
                background: white;
                position: sticky;
                top: 0;
                box-shadow: 0 2px 2px -1px rgba(0, 0, 0, 0.4);
            }
            </style>
        </head>'''
        f'<body><table>{table}</table></body></html>'
    )
    update.message.reply_document(io.StringIO(html), filename='users.html')


@vip
@admin
def backup(update: Update, context: CallbackContext):
    context.bot.send_document(chat_id=update.effective_chat.id,
                              document=open(PATH_DB, 'rb'),
                              filename= f'{datetime.now().isoformat(sep=" ", timespec="seconds")} {PATH_DB}')


delete_user_handler = CommandHandler(AdminCommand.BAN, delete_user)
getting_user_handler = CommandHandler(AdminCommand.USERS, sending_users)
backup_handler = CommandHandler(AdminCommand.BACKUP, backup)
