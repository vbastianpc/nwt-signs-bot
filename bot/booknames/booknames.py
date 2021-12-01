from unidecode import unidecode
from typing import Tuple, List

from telegram import BotCommand

from bot import get_logger
from bot.utils.browser import LazyBrowser
from bot.jw.jwlanguage import JWLanguage
from bot.database import localdatabase as db
from bot.database.schemedb import Language


logger = get_logger(__name__)


browser = LazyBrowser()
lang = JWLanguage()

def add_booknames(lang_locale) -> Language:
    db_language = db.get_language(lang_locale=lang_locale)
    if not db_language:
        raise ValueError(f"Language {lang_locale!r} doesn't exist")
    lang.locale = lang_locale
    url = f'https://wol.jw.org/wol/finder?pub=nwt&wtlocale={lang.code}'
    browser.open(url)

    booklinks = browser.page.find_all('a', class_='bookLink')
    for booklink in booklinks:
        db.add_bookname_abbr(
            lang_locale,
            int(booklink.get('data-bookid')),
            booklink.find('span', class_='title ellipsized name').text.strip('.'),
            booklink.find('span', class_='title ellipsized abbreviation').text.strip('.'),
            booklink.find('span', class_='title ellipsized official').text.strip('.'),
        )
    return db_language


def find_bookname(likely_bookname: str, lang_locale: str) -> Tuple[int, str]:
    def compare_plain(real_bookname):
        return unidecode(real_bookname).lower().startswith(unidecode(likely_bookname).lower())
    def rw(text: str):
        return text.replace(' ', '')
    db_booknames = db.get_booknames(lang_locale)
    for book in db_booknames:
        if any(map(compare_plain,
                   [book.full_name, book.long_abbr_name, book.abbr_name,
                   rw(book.full_name), rw(book.long_abbr_name), rw(book.abbr_name)]
                   )):
            logger.info('Encontrado en %s', book.lang_locale) # delete
            return book.booknum, book.lang_locale, book.full_name
    else:
        if lang_locale:
            logger.info(f'No encontrado en idioma {lang_locale!r}. Intentando en todos los idiomas')
            return find_bookname(likely_bookname, None)
        else:
            logger.info(f'Recorrí todos los idiomas en db BookNames y no encontré {likely_bookname!r}')
            raise Exception


def get_commands(lang_locale) -> List[BotCommand]:
    db_booknames = db.get_booknames(lang_locale)
    return [BotCommand(unidecode(b.abbr_name).lower(), b.full_name) for b in db_booknames]
