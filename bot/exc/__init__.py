
from sqlalchemy import select

from bot.database.schema import Bible


def last_chapter(booknum: int) -> int:
    if 0 <= booknum <= 66:
        return select(Bible.chapter) \
            .where(Bible.book == booknum) \
            .order_by(Bible.chapter.desc()) \
            .limit(1).scalar()
    else:
        raise BookNumberNotExists(booknum)

def last_verse(booknum: int, chapter: int) -> int:
    if 0 <= booknum <= 66:
        return select(Bible.verse) \
            .where(Bible.book == booknum,
                Bible.chapter == chapter) \
            .order_by(Bible.verse.desc()) \
            .limit(1).scalar()
    else:
        raise BookNumberNotExists(booknum)


class BaseBibleException(Exception):
    pass


class BibleCitationNotFound(BaseBibleException):
    pass


class VerseNotExists(BaseBibleException):
    def __init__(self, booknum: int, bookname: str, chapternum: int, wrong_verses: str, count_wrong: int):
        self.bookname = bookname
        self.chapternum = chapternum
        self.wrong_verses = wrong_verses
        self.last_versenum = last_verse(booknum, chapternum)
        self.count_wrong = count_wrong


class isApocrypha(BaseBibleException):
    def __init__(self, citation: str):
        self.citation = citation


class ChapterNotExists(BaseBibleException):
    def __init__(self, booknum:int, bookname: str, chapternum: int):
        super().__init__()
        self.bookname = bookname
        self.chapternum = chapternum
        self.last_chapternum = last_chapter(booknum)


class MissingChapterNumber(BaseBibleException):
    def __init__(self, bookname: str):
        super().__init__()
        self.bookname = bookname


class BookNameNotFound(BaseBibleException):
    def __init__(self, book_like):
        super().__init__()
        self.book_like = book_like


class BookNotFound(BaseBibleException):
    pass


class BookNumberNotExists(BaseBibleException):
    def __init__(self, booknum: int):
        super().__init__(self)
        self.booknum = booknum


class LanguageNotFound(BaseBibleException):
    def __init__(self, language_code: str):
        super().__init__()
        self.language_code = language_code


class PubmediaNotExists(BaseBibleException):
    pass

class IncompleteVideoMarkers(BaseBibleException):
    def __init__(self, verses):
        super().__init__()
        self.verses = verses

class NoNeedVideoMarkerFFMPEG(BaseBibleException):
    pass

class EditionNotFound(BaseBibleException):
    def __init__(self, language_code: str):
        super().__init__()
        self.language_code = language_code
