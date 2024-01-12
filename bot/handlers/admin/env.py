import os
import sys
from subprocess import run
from pathlib import Path

from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from telegram.ext import ConversationHandler
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext.filters import Filters

from bot import AdminCommand, MyCommand, PATH_ROOT
from bot.utils.decorators import vip, admin
from bot.strings import TextTranslator


@vip
@admin
def send_env_file(update: Update, context: CallbackContext):
    with open(PATH_ROOT / '.env', encoding='utf-8') as f:
        env = f.read()
    tt: TextTranslator = context.user_data['tt']
    update.message.reply_text(tt.asking_env(MyCommand.CANCEL))
    update.message.reply_text(f'<pre>{env}</pre>', parse_mode=ParseMode.HTML)
    return 1


def overwrite_env_file(update: Update, context: CallbackContext):
    with open(PATH_ROOT / '.env', 'w', encoding='utf-8') as f:
        f.write(update.message.text)
    tt: TextTranslator = context.user_data['tt']
    update.message.reply_text(tt.success_env(AdminCommand.RESTART))
    return -1


def cancel(update: Update, context: CallbackContext):
    tt: TextTranslator = context.user_data['tt']
    update.message.reply_text(tt.notify_cancel)
    return -1


@vip
@admin
def restart(update: Update, context: CallbackContext):
    tt: TextTranslator = context.user_data['tt']
    update.message.reply_text(tt.restart)
    os.execv(sys.executable, [sys.executable] + sys.argv)


env_handler = ConversationHandler(
    entry_points=[CommandHandler(AdminCommand.ENV, send_env_file)],
    states={1: [MessageHandler(Filters.text & (~ Filters.command), overwrite_env_file)]},
    fallbacks=[CommandHandler(MyCommand.CANCEL, cancel)]
)


@vip
def git(update: Update, context: CallbackContext):
    console = run(['git', '-C', str(Path(__file__).parent.parent.parent), 'pull'], capture_output=True)
    update.message.reply_text(console.stdout.decode())


restart_handler = CommandHandler(AdminCommand.RESTART, restart)
git_handler = CommandHandler(AdminCommand.GIT, git)