from telegram import Update
from telegram import ParseMode
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Document
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import ConversationHandler
from telegram.ext import MessageHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext import Filters

from bot import AdminCommand
from bot import MyCommand
from bot.secret import ADMIN
from bot.utils.decorators import vip, admin
from bot.utils import now
from bot.database import report as rdb
from bot.database.report import count
from bot.database.schema import File, File2User, VideoMarker, Chapter, Book, Edition, Language, User
from bot.database import get
from bot.database import PATH_DB
from bot.strings import TextTranslator
from bot.utils import how_to_say


@vip
def stats(update: Update, context: CallbackContext) -> None:
    user = get.user(update.effective_user.id)
    tt: TextTranslator = context.user_data['tt']
    total_verses = sum(map(lambda x: x.count_verses, user.files))
    sign_language_codes = list(set(map(lambda x: x.language.code, user.files)))
    total_overlay = sum(map(lambda x: x.count_verses,
                            filter(lambda f: f.overlay_language_code is not None, user.files)))
    if len(sign_language_codes) == 1:
        update.message.reply_text(
            text=tt.stat(total_verses, how_to_say(sign_language_codes[0], user.bot_language.code), total_overlay,
                         *rdb.duration_size(user.id)),
            parse_mode=ParseMode.HTML)
    elif len(sign_language_codes) > 1:
        update.message.reply_text(
            text=tt.stats(total_verses, len(sign_language_codes), total_overlay, *rdb.duration_size(user.id)),
            parse_mode=ParseMode.HTML)
    if update.effective_user.id == ADMIN:
        update.message.reply_html(
            '<pre>'
            f'{rdb.sum_duration():>6} Duración videos cortados\n'
            f'{rdb.sum_duration_sent():>6} Duración videos enviados\n'
            f'{count(File):>6,} Videos cortados\n'
            f'{count(File2User):>6,} Videos enviados\n'
            f'{(ss := rdb.sum_size() / 1024) :>6.1f} GB de versículos cortados\n'
            f'{(sss := rdb.sum_size_sent() / 1024) :>6.1f} GB versículos enviados\n'
            f'{(sss - ss) :>6.1f} GB ahorrados\n'
            f'{count(VideoMarker):>6,} Marcadores guardados\n'
            f'{count(Edition):>6,} Ediciones de Biblia\n'
            f'{count(Chapter):>6,} Capítulos guardados\n'
            f'{count(Book):>6,} Libros guardados\n'
            f'{count(Language):>6} Idiomas\n'
            f'{count(Language, "Language.is_sign_language == True"):>6} Lengua de Señas\n'
            f'{rdb.count_active_users():>6} Usuarios activos último mes\n'
            f'{count(User):>6} Usuarios en total\n'
            f'{count(User, "User.status == User.AUTHORIZED"):>6} Usuarios permitidos\n'
            f'{count(User, "User.status == User.WAITING"):>6} Usuarios en lista de espera\n'
            f'{count(User, "User.status == User.DENIED"):>6} Usuarios bloqueados\n'
            '</pre>'
        )


def document(update: Update, context: CallbackContext):
    update.message.reply_text(
        '⚠️ Critical! Do you want to replace the database?',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton('✅ Yes', callback_data='✅'), InlineKeyboardButton('❌ No', callback_data='❌')]
        ]))
    context.user_data['db'] = update.message.document
    return 1


def overwrite_db(update: Update, context: CallbackContext):
    update.effective_message.edit_reply_markup()
    try:
        update.effective_message.reply_document(document=open(PATH_DB, 'rb'), filename= f'{now()} {PATH_DB}')
    except:
        pass
    db_doc: Document = context.user_data['db']
    db_doc.get_file().download(PATH_DB)
    update.effective_message.reply_text('Database has been replaced')
    del context.user_data['db']
    return -1


def cancel(update: Update, context: CallbackContext):
    update.effective_message.edit_reply_markup()
    update.effective_message.reply_text('Canceled')
    return -1


database_status_handler = CommandHandler(AdminCommand.STATS, stats)
replace_db_handler = ConversationHandler(
    entry_points=[MessageHandler(Filters.document.file_extension('db') & Filters.user(ADMIN), document)],
    states={1: [CallbackQueryHandler(overwrite_db, pattern='✅')]},
    fallbacks=[CommandHandler(MyCommand.CANCEL, cancel),
               CallbackQueryHandler(cancel, pattern='❌')]
    )