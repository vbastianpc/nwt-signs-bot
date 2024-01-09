from html import escape

from telegram import Update, ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext import Filters
import telegram.error
from telegram.utils.helpers import mention_html

from bot import MyCommand
from bot.secret import ADMIN
from bot.secret import LOG_GROUP_ID
from bot.secret import TOPIC_WAITING
from bot.logs import get_logger
from bot.utils.decorators import forw, vip
from bot.utils import how_to_say
from bot.database import get
from bot.database import add
from bot.database import fetch
from bot.strings import TextTranslator
from bot.database.schema import User


logger = get_logger(__name__)

TAG_START = '#start'


@vip
def start(update: Update, context: CallbackContext) -> int:
    tuser = update.effective_user
    if tuser.id == ADMIN and context.args:
        try:
            int(context.args[0])
        except ValueError:
            pass
        else:
            add_user(update, context)
        return
    user = get.user(tuser.id)
    tt = TextTranslator(user.bot_language_code)
    update.message.reply_text(tt.hi(update.effective_user.first_name) + ' ' + tt.start(MyCommand.HELP))


def add_user(update: Update, context: CallbackContext):
    new_telegram_id = int(context.args[0])
    user_admin = get.user(ADMIN)
    tt = TextTranslator(user_admin.bot_language.code)
    if not (new_user := get.user(new_telegram_id)):
        update.message.reply_text(tt.warn_user)
        return
    if new_user.is_authorized():
        update.message.reply_text(tt.user_already)
        return
    new_user = add.or_update_user(new_telegram_id, status=User.AUTHORIZED)
    try:
        context.bot.send_message(chat_id=new_telegram_id, text='🔐')
    except telegram.error.Unauthorized:
        update.message.reply_text(tt.user_stopped_bot)
        return
    update.message.reply_html(f'{mention_html(new_telegram_id, new_user.full_name)} {tt.user_added}')
    if not get.edition(new_user.bot_language.code):
        fetch.editions()
    if not get.books(new_user.bot_language.code):
        fetch.books(new_user.bot_language.code)
    tt2 = TextTranslator(new_user.bot_language_code)
    context.bot.send_message(chat_id=new_telegram_id,
                             text=tt.hi(update.effective_user.first_name) + ' ' + tt.start(MyCommand.HELP))
    if not new_user.sign_language:
        context.bot.send_message(chat_id=new_telegram_id,
                                 text=tt2.select_sl(MyCommand.SIGNLANGUAGE), parse_mode=ParseMode.HTML)


def whois(update: Update, context: CallbackContext):
    tuser = update.effective_user
    user = get.user(tuser.id)
    t = TextTranslator(user.bot_language_code)
    update.message.reply_text(t.wait)
    context.bot.send_message(
        chat_id=LOG_GROUP_ID,
        message_thread_id=TOPIC_WAITING,
        text=f'{TAG_START}'
             f'<pre><code class="language-python">'
             f'full_name: {tuser.full_name}\nlanguage_code: {tuser.language_code}username: {tuser.username}'
             f'</code></pre>\n\n{t.introduced_himself}',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f'Add {tuser.full_name}', url=f'{context.bot.link}?start={tuser.id}')],
            [InlineKeyboardButton(f'View {tuser.full_name}', url=f'tg://user?id={tuser.id}')],
        ]),
        parse_mode=ParseMode.HTML
    )
    context.bot.forward_message(chat_id=LOG_GROUP_ID,
                                message_thread_id=TOPIC_WAITING,
                                from_chat_id=tuser.id,
                                message_id=update.effective_message.message_id)
    return 2




def forward(update: Update, context: CallbackContext) -> int:
    context.bot.forward_message(chat_id=LOG_GROUP_ID,
                                message_thread_id=TOPIC_WAITING,
                                from_chat_id=update.message.chat_id,
                                message_id=update.message.message_id)

@forw
def all_fallback(u: Update, c: CallbackContext) -> None:
    return


start_handler = CommandHandler(MyCommand.START, start)
all_fallback_handler = MessageHandler(Filters.all, all_fallback)
