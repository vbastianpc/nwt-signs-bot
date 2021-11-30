import json
import logging
import traceback
import html

from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.ext import ConversationHandler
from telegram.constants import MAX_MESSAGE_LENGTH
from telegram.parsemode import ParseMode

from bot.database import localdatabase as db
from bot.utils.decorators import admin
from bot import AdminCommand, MyCommand
from bot import ADMIN
from bot.strings import TextGetter


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


@admin
def test_data(update: Update, context: CallbackContext) -> None:
    if not context.args:
        data = sorted(context.user_data.keys())
    else:
        varname = context.args[0].split('.')[0]
        attr_keys = '.'.join(context.args[0].split('.')[1:])
        e = f'context.user_data.get("{varname}")' + (('.' + attr_keys) if attr_keys else '')
        data = eval(e)

    try:
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
    except TypeError:
        json_data = str(data)
    except:
        json_data = json.dumps(data, indent=2, ensure_ascii=False, default=lambda x: x.__dict__)
    update.message.reply_markdown_v2(f'```\n{json_data[:MAX_MESSAGE_LENGTH]}```')


@admin
def notify(update: Update, context: CallbackContext):
    t = TextGetter(db.get_user(update.effective_user.id).bot_lang)
    if not context.args:
        update.message.reply_text(
            text=t.wrong_notify.format(AdminCommand.NOTIFY),
            parse_mode=ParseMode.MARKDOWN
        )
        return -1
    context.user_data['user_ids'] = context.args
    update.message.reply_text(t.notify.format(MyCommand.OK, MyCommand.CANCEL))
    context.user_data['advice_note'] = []
    return 1


def get_notification(update: Update, context: CallbackContext):
    context.user_data['advice_note'].append(update.message)
    return 1


def send_notification(update: Update, context: CallbackContext):
    user_ids = context.user_data['user_ids']
    for msg in context.user_data['advice_note']:
        for user_id in user_ids:
            context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=update.effective_user.id,
                message_id=msg.message_id,
            )
    t = TextGetter(db.get_user(update.effective_user.id).bot_lang)
    update.message.reply_text(t.notify_success)
    del context.user_data['advice_note']
    del context.user_data['user_ids']
    return -1


def cancel(update: Update, context: CallbackContext):
    t = TextGetter(db.get_user(update.effective_user.id).bot_lang)
    update.message.reply_text(t.notify_cancel)
    del context.user_data['advice_note']
    return -1


@admin
def logs(update: Update, context: CallbackContext):
    try:
        with open('./log.log', 'r', encoding='utf-8') as f:
            data = f.read()
    except FileNotFoundError:
        t = TextGetter(db.get_user(update.effective_user.id).bot_lang)
        update.message.reply_text(t.logfile_notfound)
    else:
        update.message.reply_markdown_v2(f'```{data[-MAX_MESSAGE_LENGTH::]}```')
    return


@admin
def logfile(update: Update, context: CallbackContext):
    try:
        context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=open('./log.log', 'rb'),
        )
    except FileNotFoundError:
        t = TextGetter(db.get_user(update.effective_user.id).bot_lang)
        update.message.reply_text(t.logfile_notfound)


def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)
    tb_string = f'<pre>{html.escape(tb_string)}</pre>'

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
    )

    context.bot.send_message(chat_id=ADMIN, text=message, parse_mode=ParseMode.HTML)
    context.bot.send_message(chat_id=ADMIN, text=tb_string, parse_mode=ParseMode.HTML)



test_handler = CommandHandler(AdminCommand.TEST, test_data)

notice_handler = ConversationHandler(
    entry_points=[CommandHandler(AdminCommand.NOTIFY, notify)],
    states={
        1: [CommandHandler(MyCommand.OK, send_notification),
            CommandHandler(MyCommand.CANCEL, cancel),
            MessageHandler(Filters.all, get_notification)],
    },
    fallbacks=[CommandHandler(MyCommand.CANCEL, cancel)],
)

logs_handler = CommandHandler(AdminCommand.LOGS, logs)
logfile_handler = CommandHandler(AdminCommand.LOGFILE, logfile)
