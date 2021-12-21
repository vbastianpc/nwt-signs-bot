from unidecode import unidecode
from typing import Tuple, List, Callable, Iterator

from telegram import BotCommand

from bot import get_logger
from bot.utils.browser import LazyBrowser
from bot.jw.jwlanguage import JWLanguage
from bot.database import localdatabase as db
from bot.database.schemedb import BookNamesAbbreviation, Language


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


def search_bookname(likely_bookname: str, lang_locale: str = None) -> Tuple[int, str]:
    # search case insensitive
    likely_bookname = likely_bookname.lower()
    db_booknames = db.get_booknames(lang_locale)
    def strict(bookname: str):
        return bookname.lower() == likely_bookname
    def startswith(bookname: str):
        return bookname.lower().startswith(likely_bookname)
    def startswith_unidecode(bookname: str):
        return unidecode(bookname).lower().startswith(unidecode(likely_bookname))
    def strict_unidecode(bookname: str):
        return unidecode(bookname).lower() == likely_bookname.lower()
    def contains(bookname: str):
        return likely_bookname in bookname.lower()
    def contains_unidecode(bookname: str):
        return unidecode(likely_bookname) in unidecode(bookname).lower()
    def variations(book: BookNamesAbbreviation) -> List[str]:
        return [
            book.full_name,
            book.long_abbr_name,
            book.abbr_name,
            book.full_name.replace(' ', ''),
            book.long_abbr_name.replace(' ', ''),
            book.abbr_name.replace(' ', '')
        ]
    def find_bookname(*funcs: Callable[[str], bool]) -> Iterator[BookNamesAbbreviation]:
        i = 0
        for func in funcs:
            for book in db_booknames:
                i += 1
                if any(map(func, variations(book))):
                    logger.info("%s iterations to found '%s' (%s %s %s %s '%s') by '%s' mode",
                        i, likely_bookname, book.full_name, book.long_abbr_name, book.abbr_name, book.booknum, book.lang_locale, func.__name__)
                    yield book
        logger.info("Total iterations searching '%s' in %s: %s", likely_bookname, (f"'{lang_locale}' language" if lang_locale else 'all languages'), i)
    
    for book in find_bookname(
            strict,
            strict_unidecode,
            startswith,
            startswith_unidecode,
            contains,
            contains_unidecode):
        return book.booknum, book.lang_locale, book.full_name

    if lang_locale:
        logger.info(f'{likely_bookname} not found in {lang_locale!r}. Trying in all languages')
        return search_bookname(likely_bookname, None)
    else:
        logger.info(f'{likely_bookname!r} not found in any language')
        raise Exception


def get_commands(lang_locale) -> List[BotCommand]:
    db_booknames = db.get_booknames(lang_locale)
    return [BotCommand(unidecode(b.abbr_name).lower(), b.full_name) for b in db_booknames]


def testing_bible_booknames_commands():
    logger.info('Init testing...')
    db_booknames = db.get_booknames()
    def check(book: BookNamesAbbreviation):
        assert search_bookname(book.abbr_name, book.lang_locale)[0] == book.booknum, f"abbr_name doesn't match {book.abbr_name!r} {book.lang_locale!r}"
        assert search_bookname(book.long_abbr_name, book.lang_locale)[0] == book.booknum, f"long_abbr_name doesn't match {book.long_abbr_name!r} {book.lang_locale!r}"
        assert search_bookname(book.full_name, book.lang_locale)[0] == book.booknum, f"full_name doesn't match {book.full_name!r} {book.lang_locale!r}"
    for book in db_booknames:
        check(book)
    logger.info('All booknames checked')