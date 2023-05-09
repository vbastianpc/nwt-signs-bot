from unidecode import unidecode
from typing import List, Callable, Iterator

from telegram import BotCommand

from bot.logs import get_logger
from bot.database import localdatabase as db
from bot.database.schema import Book


logger = get_logger(__name__)



def search_bookname(likely_bookname: str, language_code: int = None) -> Book:
    # search case insensitive
    likely_bookname = likely_bookname.lower().strip()
    def variations(book: Book) -> List[str]:
        return [
            book.name.lower(),
            book.standard_abbreviation.lower(),
            book.official_abbreviation.lower(),
            book.name.lower().replace(' ', ''),
            book.standard_abbreviation.lower().replace(' ', ''),
            book.official_abbreviation.lower().replace(' ', '')
        ]

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

    books = db.get_books(language_code=language_code)
    def find_bookname(*funcs: Callable[[str], bool]) -> Iterator[Book]:
        i = 0
        for func in funcs:
            for book in books:
                i += 1
                if any(map(func, variations(book))):
                    logger.info("%s iterations to found '%s' (%s %s %s %s '%s') by '%s' mode",
                        i, likely_bookname, book.name, book.standard_abbreviation, book.official_abbreviation, book.number, book.bible.language.code, func.__name__)
                    yield book
        logger.info("Total iterations searching '%s' in %s: %s", likely_bookname, (f"'{language_code}' language id" if language_code else 'all languages'), i)
    
    for book in find_bookname(
            strict,
            strict_unidecode,
            startswith,
            startswith_unidecode,
            contains,
            contains_unidecode):
        return book

    if language_code:
        logger.info(f'{likely_bookname} not found in {language_code=}. Trying in all languages')
        return search_bookname(likely_bookname, None)
    else:
        logger.info(f'{likely_bookname!r} not found in any language')
        raise Exception

def get_botcommands(language_code) -> List[BotCommand]:
    books = db.get_books(language_code=language_code)
    return [BotCommand(unidecode(book.standard_abbreviation).lower().replace(' ', ''), book.full_name) for book in books]

def get_commands(language_code) -> List[str]:
    books = db.get_books(language_code=language_code)
    return [unidecode(book.standard_abbreviation).lower().replace(' ', '') for book in books]