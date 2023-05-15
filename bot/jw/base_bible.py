
import re
from typing import TypeVar, Type, Self

from unidecode import unidecode as ud
from sqlalchemy import select

from bot.database import session
from bot.database import get
from bot.database.schema import Bible
from bot.database.schema import Book
from bot.database.schema import Edition
from bot.database.schema import Chapter
from bot.database.schema import Language
from bot import exc
from bot.logs import get_logger


logger = get_logger(__name__)

BO = TypeVar('BO', bound='BibleObject')


class BibleObject:
    BIBLE_PATTERN = r'([123]? *(?:[^\d]+)) *(?:(\d*)[ :]+)? *([ ,\d-]*)'
    ONE_CHHAPTER_BOOKS = [31, 57, 63, 64, 65] # Abdías, Filemón, 2 Juan, 3 Juan, Judas
    __slots__ = (
        '_language',
        '_edition',
        '_book',
        '_chapter',
        '_chapternumber',
        '_verses',
    )

    def __init__(self, book: Book, chapternumber: int | None = None,
                 verses: int | str | list[int | str] | None = None):
        self._book = book
        self._language = book.edition.language # shortcut
        self._edition = book.edition # shortcut
        self._chapter = get.chapter(chapternumber, book)
        self.chapternumber = chapternumber
        self.verses = verses


    @property
    def language(self) -> Language:
        return self._language

    @property
    def edition(self) -> Edition:
        return self._edition

    @property
    def book(self) -> Book:
        return self._book

    @property
    def chapter(self) -> Chapter:
        return self._chapter

    @property
    def verses(self) -> list[int | None]:
        return self._verses

    @verses.setter
    def verses(self, value: int | str | list[int | str] | None):
        self._verses = self.get_verses(value)

    @property
    def chapternumber(self):
        return self._chapternumber

    @chapternumber.setter
    def chapternumber(self, value: int | str | None) -> int | None:
        if value is not None and not select(Bible.verse).where(
                Bible.book == self.book.number,
                Bible.chapter == int(value)
            ).scalar():
            raise exc.ChapterNotExists(self.book.number, self.book.name, int(value))
        if isinstance(value, (str, int)):
            self._chapternumber = int(value)
            self._chapter = get.chapter(self._chapternumber, self.book)
        elif value is None:
            self._chapternumber = None
            self._chapter = None

    def refresh(self):
        self._book = get.book(self._language.code, self._book.number)
        self._edition = self._book.edition
        self._chapter = get.chapter(self.chapternumber, self._book)
        self._language = get.language(code=self._language.code)

    def set_booknum(self, booknum: int):
        new_book = get.book(self.language.code, booknum)
        if new_book:
            self._edition = new_book.edition
            self._book = new_book
            self._chapter = get.chapter(self.chapternumber, new_book)
        else:
            raise exc.BookNotFound


    def set_language(self, language_code: str) -> Self:
        new_book = get.book(language_code, self.book.number)
        if new_book:
            self._language = new_book.edition.language
            self._edition = new_book.edition
            self._book = new_book
            self._chapter = get.chapter(self.chapternumber, new_book)
            return self
        else:
            if get.language(code=language_code):
                raise exc.BookNotFound
            else:
                raise exc.LanguageNotFound

    @property
    def citation(self) -> str:
        bookname = self.book.name if len(self.verses) > 1 else self.book.standard_singular_bookname
        if self.book.number in [57, 63, 64, 65]:  # Filemón, 2 Juan, 3 Juan, Judas
            return f'{bookname} {self.get_verse_citation(self.verses)}'
        if self.chapternumber and self.verses:
            return f'{bookname} {self.chapternumber}:{self.get_verse_citation(self.verses)}'
        if self.chapternumber:
            return f'{bookname} {self.chapternumber}'
        else:
            return f'{bookname}'


    @classmethod
    def from_human(cls: Type[BO], citation: str, language_code: str) -> BO:
        book_like, chapternumber, verses = cls.parse_citation_regex(citation)
        try:
            book = cls.search_book(book_like, language_code=language_code)
        except exc.BookNameNotFound as e:
            if book_like and chapternumber:
                raise e
            else:
                raise exc.BibleCitationNotFound
        if chapternumber is None and len(verses) == 1 and book.number not in cls.ONE_CHHAPTER_BOOKS:
            # "Mateo 5" chapternumber = None, verses = [5]
            chapternumber, verses = verses[0], []
        elif chapternumber is None and len(verses) > 1 and book.number not in cls.ONE_CHHAPTER_BOOKS:
            # "Mateo 5, 6, 7" chapternumber = None, verses = [5, 6, 7]
            raise exc.MissingChapterNumber(book.name)
        elif chapternumber is None and book.number in cls.ONE_CHHAPTER_BOOKS:
            # "Judas 5, 6" chapternumber = None, verses = [5, 6]
            chapternumber = 1
        cls.exists(book.number, chapternumber, verses, book.name)
        if book.edition.language.code != language_code:
            b = get.book(language_code, book.number)
            if b:
                book = b
            else:
                logger.warning(f'{citation!r} found in another language: {book.edition.language.code!r}. '
                               f'Query language: {language_code!r}. ')
        return cls(book, chapternumber, verses)


    @staticmethod
    def exists(booknum: int, chapternumber: int | str | None, verses: int | str | list[int | str] | None,
               bookname:str = None, raise_error:bool = True) -> bool:
        try:
            s = select(Bible).where(Bible.book == booknum)
            if not session.query(s.exists()).scalar():
                raise exc.BookNumberNotExists(booknum)
            if chapternumber is None:
                return True
            chapternumber = int(chapternumber)
            s = s.where(Bible.chapter == chapternumber)
            if not session.query(s.exists()).scalar():
                raise exc.ChapterNotExists(booknum, bookname, chapternumber)
            if not verses:
                return True
            verses = BibleObject.get_verses(verses)
            in_nwt = session.scalars(
                select(Bible.verse).where(
                    Bible.book == booknum,
                    Bible.chapter == chapternumber,
                    Bible.verse.in_(verses),
                )
            ).all()
            bad = list(set(verses) - set(in_nwt))
            if bad:
                raise exc.VerseNotExists(
                    booknum,
                    bookname,
                    chapternumber,
                    wrong_verses=BibleObject.get_verse_citation(bad),
                    count_wrong=len(bad)
                )
            s = s.where(Bible.verse.in_(verses), Bible.is_apocryphal == True)
            if session.query(s.exists()).scalar():
                apocryphal = session.scalars(
                    select(Bible.verse).where(
                        Bible.book == booknum,
                        Bible.chapter == chapternumber,
                        Bible.verse.in_(verses),
                        Bible.is_apocryphal == True
                    ).order_by(Bible.verse.asc())
                ).all()
                raise exc.isApocrypha(f'{bookname} {chapternumber}:{BibleObject.get_verse_citation(apocryphal)}')
        except exc.BaseBibleException as e:
            if raise_error:
                raise e
            else:
                return False
        else:
            return True


    @staticmethod
    def search_book(book_like: str | None = None,
                    language_code: str | None = None,
                    from_citation: str | None = None) -> Book | None:
        book_like = BibleObject.parse_citation_regex(from_citation)[0] if from_citation else book_like
        book_like = re.sub(' *', '', book_like).lower().replace('.', '')
        books = get.books(language_code=language_code)
        for book in books:
            bn, sa, oa, ssb = map(
                lambda x: re.sub(' *', '', x).lower(),
                [book.name, book.standard_abbreviation, book.official_abbreviation, book.standard_singular_bookname]
            )
            if any(map(lambda x: x.startswith(book_like), (bn, sa, oa, ssb))) or \
                any(map(lambda x: ud(x).lower().startswith(ud(book_like)), (bn, sa, oa, ssb))):
                return book
        else:
            if language_code is None:
                raise exc.BookNameNotFound(book_like)
            else:
                return BibleObject.search_book(book_like, language_code=None)

    @staticmethod
    def parse_citation_regex(citation: str) -> tuple[str, int | None, list[int | None]]:
        m = re.search(BibleObject.BIBLE_PATTERN, citation)
        if m is None:
            raise exc.BibleCitationNotFound
        return (m.group(1),                              # book_like
                int(m.group(2)) if m.group(2) else None, # chapternum
                BibleObject.get_verses(m.group(3)))      # verses

    @staticmethod
    def get_verses(verses_like: int | str | list[int | str] | None = None,
                   from_citation: str | None = None) -> list[int | None]:
        """
        1  ->  [1]
        '1'  ->  [1]
        '1-3, 6, 7'  -> [1, 2, 3, 6, 7]
        """
        if from_citation:
            return BibleObject.get_verses(BibleObject.parse_citation_regex(from_citation)[2])
        if isinstance(verses_like, int):
            return [verses_like]
        elif verses_like is None or verses_like == '':
            return []
        elif isinstance(verses_like, str): # it could be '14' or '14 15 18' or '14-18' or '14, 15, 17-20' etc
            verses = []
            groups = [i for i in re.sub(' *', '', verses_like).split(',')]
            for group in groups:
                if '-' in group:
                    verses += [verse for verse in range(int(group.split('-')[0]), int(group.split('-')[1]) + 1)]
                else:
                    verses.append(int(group))
            return verses
        elif isinstance(verses_like, list):
            return [verse for result in [BibleObject.get_verses(item) for item in verses_like] for verse in result]
        else:
            raise TypeError(f'verses must be a list, a string or an integer, not {type(verses_like).__name__}')

    @staticmethod
    def get_verse_citation(verses: list[int | None]) -> str:
        """Reverse function of 'get_verses'
        [1, 2, 3, 6, 7]  ->  '1-3, 6, 7'
        """
        if not verses:
            return ''
        pv = str(verses[0])
        last = verses[0]
        sep = ', '
        for i in range(1, len(verses) - 1):
            if verses[i] - 1 == verses[i - 1] and verses[i] + 1 == verses[i + 1]:
                temp = ''
                sep = '-'
            elif verses[i] - 1 == verses[i - 1] and not verses[i] + 1 == verses[i + 1]:
                temp = f'{sep}{verses[i]}, {verses[i+1]}'
                last = verses[i + 1]
            else:
                sep = ', '
                if last == verses[i]:
                    temp = ''
                else:
                    temp = f'{sep}{verses[i]}'
            pv += temp
        if last != verses[-1]:
            pv += f'{sep}{verses[-1]}'
        return pv

    @classmethod
    def from_num(cls :Type[BO],
                 language_code: str,
                 booknumber: str | int,
                 chapternumber: str | int | None = None,
                 verses: int | str | list[int | str] | None = None
                 ) -> BO:
        cls.exists(int(booknumber), chapternumber, verses)
        book = get.book(language_code, booknumber)
        if not book:
            if not get.language(code=language_code):
                raise exc.LanguageNotFound(language_code)
            else:
                raise exc.BookNotFound
        return cls(book, chapternumber, verses)


if __name__ == '__main__':
    passage = BibleObject.from_human('Mat', 'es')


    print('end')
