import json
import traceback
import html
import sys
import io
from pathlib import Path
import os

from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
from telegram.ext import ConversationHandler
from telegram.constants import MAX_MESSAGE_LENGTH
from telegram.parsemode import ParseMode
import telegram.error

from bot.database import get
from bot.utils.decorators import vip, admin
from bot import AdminCommand, MyCommand, PATH_ROOT
from bot.secret import LOG_GROUP_ID
from bot.secret import TOPIC_ERROR
from bot.secret import TOKEN
from bot.logs import get_logger, PATH_LOG
from bot.strings import TextTranslator


logger = get_logger(__name__)

@vip
@admin
def test_data(update: Update, context: CallbackContext) -> None:
    update.message.reply_html(
        f'<pre>{sys.executable=}\n\n{sys.argv=}\n\n{os.getcwd()=}\n\n{PATH_ROOT=}\n\n{TOKEN=}\n\n'
        f'{context.bot.name=}</pre>'
    )
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


@vip
@admin
def notify(update: Update, context: CallbackContext):
    tt: TextTranslator = context.user_data['tt']
    if not context.args:
        update.message.reply_text(
            text=tt.wrong_notify(AdminCommand.NOTIFY),
            parse_mode=ParseMode.HTML
        )
        return -1
    context.user_data['user_ids'] = context.args
    update.message.reply_text(tt.notify(MyCommand.OK, MyCommand.CANCEL))
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
    tt: TextTranslator = context.user_data['tt']
    update.message.reply_text(tt.notify_success)
    del context.user_data['advice_note']
    del context.user_data['user_ids']
    return -1


def cancel(update: Update, context: CallbackContext):
    tt: TextTranslator = context.user_data['tt']
    update.message.reply_text(tt.notify_cancel)
    del context.user_data['advice_note']
    return -1


@admin
def flushlogs(update: Update, context: CallbackContext):
    try:
        update.message.reply_document(PATH_LOG.open('rb'))
    except (FileNotFoundError, telegram.error.BadRequest):
        tt: TextTranslator = context.user_data['tt']
        update.message.reply_text(tt.logfile_notfound)
    else:
        with open(PATH_LOG, 'w', encoding='utf-8') as f:
            pass


def error_handler(update: Update, context: CallbackContext) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    text = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>\n\n" +
        f"<pre>context.bot_data = {html.escape(str(context.bot_data))}</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n" +
        f"<pre>{html.escape(tb_string)}</pre>"
    )
    context.bot.send_document(chat_id=LOG_GROUP_ID, message_thread_id=TOPIC_ERROR, document=io.StringIO(text),
                                    filename=f'{tb_list[-1].split(":")[0]}.html')


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

flushlogs_handler = CommandHandler(AdminCommand.FLUSHLOGS, flushlogs)
