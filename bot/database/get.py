from datetime import datetime

from sqlalchemy import select, func

from bot.logs import get_logger
from bot.database import session
from bot.database.schema import Language
from bot.database.schema import Edition
from bot.database.schema import Book
from bot.database.schema import Chapter
from bot.database.schema import VideoMarker
from bot.database.schema import File
from bot.database.schema import User
from bot.database.schema import Bible
from bot import exc


logger = get_logger(__name__)

def sign_languages() -> list[Language]:
    return session.query(Language).filter(Language.is_sign_language == True).order_by(Language.meps_symbol.asc()).all()

def languages() -> list[Language]:
    return session.query(Language).order_by(Language.meps_symbol.asc()).all()

def language(code: str | None = None, meps_symbol: str | None = None) -> Language | None:
    q = session.query(Language)
    if code is not None:
        q = q.filter(Language.code == code)
    elif meps_symbol is not None:
        q = q.filter(Language.meps_symbol == meps_symbol)
    else:
        raise TypeError('get_language expected one argument')
    return q.one_or_none()


def parse_language(code_or_meps: str) -> Language | None:
    return language(code=code_or_meps.lower()) or language(meps_symbol=code_or_meps.upper())


def sign_languages_meps_symbol() -> list[str]:
    return session.scalars(select(Language.meps_symbol).filter(Language.is_sign_language == True)).all()

def user(telegram_user_id) -> User | None:
    return session.query(User).filter(User.telegram_user_id == telegram_user_id).one_or_none()

def users() -> list[User | None]:
    return session.query(User).all()

def banned_users() -> list[User | None]:
    return session.query(User).filter(User.status == -1).all()

def waiting_users() -> list[User | None]:
    return session.query(User).filter(User.status == 0).all()

def accepted_users() -> list[User | None]:
    return session.query(User).filter(User.status == 1).all()

def edition(language_code: str) -> Edition | None:
    return (session
            .query(Edition)
            .join(Language)
            .filter(Language.code == language_code)
            .order_by(Edition.id.asc())
            .limit(1)
            .one_or_none()
    )


def books(language_code: str = None, booknum: int = None) -> list[Book]:
    q = session.query(Book)
    if isinstance(language_code, str):
        q = (q
             .join(Edition, Edition.id == Book.edition_id)
             .join(Language, Language.code == Edition.language_code)
             .filter(Language.code == language_code)
        )
    if isinstance(booknum, int):
        q = q.filter(Book.number == booknum)
    return q.order_by(Book.number.asc()).all()


def book(language_code: str, booknum: int | str, edition_id: int | None = None) -> Book | None:
    q = (
        session.query(Book)
        .join(Edition, Edition.id == Book.edition_id)
        .join(Language, Language.code == Edition.language_code)
        .filter(
            Book.number == int(booknum),
            Language.code == language_code,
        )
    )
    if isinstance(edition_id, int):
        q = q.filter(Edition.id == edition_id)
    return q.one_or_none()

def chapter(chapternum: int, book: Book, checksum: str | None = None) -> Chapter | None:
    q = (session.query(Chapter)
         .join(Book, Book.id == Chapter.book_id)
         .join(Edition, Edition.id == Book.edition_id)
         .join(Language, Language.code == Edition.language_code)
         .filter(Language.code == book.edition.language.code,
                 Book.number == book.number,
                 Chapter.number == chapternum
        ).order_by(Chapter.id.desc()).limit(1)
    )
    if checksum:
        q.filter(Chapter.checksum == checksum)
    return q.one_or_none()


def chapters(book: Book) -> list[Chapter | None]:
    return (session.query(Chapter)
         .join(Book, Book.id == Chapter.book_id)
         .join(Edition, Edition.id == Book.edition_id)
         .join(Language, Language.code == Edition.language_code)
         .filter(Language.code == book.edition.language.code,
                 Book.number == book.number,
        ).order_by(Chapter.id.asc())
    ).all()


def videomarkers(chapter: Chapter, verses: list[int] | None = None) -> list[VideoMarker]:
    q = session.query(VideoMarker).filter(VideoMarker.chapter_id == chapter.id)
    if verses is None:
        return q.all()
    else:
        vms = q.filter(VideoMarker.versenum.in_(verses)).all()
        available_versenums = [vm.versenum for vm in vms]
        if set(verses) == set(available_versenums):
            return vms
        else:
            raise exc.IncompleteVideoMarkers(set(verses) == set(available_versenums))


def unavailable_verses(chapter: Chapter, verses: list[int]) -> list[int]:
    available = session.scalars(select(VideoMarker.versenum).filter(VideoMarker.chapter_id == chapter.id)).all()
    return list(set(verses) - set(available))


def file(chapter: Chapter,
         verses: list[int],
         overlay_language_code: str,
         checksum: str | None = None,
         ) -> File | None:
    q = session.query(File) \
        .join(Chapter, Chapter.id == File.chapter_id) \
        .join(Book, Book.id == Chapter.book_id) \
        .join(Edition, Edition.id == Book.edition_id) \
        .join(Language, Language.code == Edition.language_code) \
        .filter(Language.code == chapter.book.edition.language.code,
                Chapter.number == chapter.number,
                File.raw_verses == ' '.join(map(str, verses)),
                File.overlay_language.code == overlay_language_code)
    if checksum:
        q = q.filter(Chapter.checksum == checksum)
    return q.all()

def files(
        sign_language_code: str = None,
        booknum: int = None,
        chapternum: int = None,
        raw_verses: str = None,
        checksum: str = None,
        overlay_language_code: str | None = False,
        is_deprecated: bool = None,
        limit: int = 200,
        since: datetime = None
    ) -> list[File | None]:
    q = (
        session.query(File)
        .join(Chapter, Chapter.id == File.chapter_id)
        .join(Book, Book.id == Chapter.book_id)
        .join(Edition, Edition.id == Book.edition_id)
        .join(Language, Language.code == Edition.language_code)
    )
    if sign_language_code is not None:
        q = q.filter(Language.code == sign_language_code)
    if booknum is not None:
        q = q.filter(Book.number == booknum)
    if chapternum is not None:
        q = q.filter(Chapter.number == chapternum)
    if raw_verses:
        q = q.filter(File.raw_verses == raw_verses)
    if checksum is not None:
        q = q.filter(Chapter.checksum == checksum)
    if overlay_language_code is not False:
        q = q.filter(File.overlay_language_code == overlay_language_code)
    if is_deprecated is not None:
        q = q.filter(File.is_deprecated == is_deprecated)
    if since:
        q = q.filter(since < File.added_datetime)
    q = q.order_by(Book.number.asc(), Chapter.number.asc(), File.raw_verses.asc())
    if limit > 0:
        q = q.limit(limit)
    return q.all()


def last_chapternum(booknumber: int) -> int:
    return select(func.max(Bible.chapter)).where(Bible.book == booknumber).scalar()

def last_versenum(booknumber: int, chapternumber: int) -> int:
    return select(func.max(Bible.verse)).where(Bible.book == booknumber,
                                               Bible.chapter == chapternumber,
                                               Bible.is_omitted == False).scalar()

if __name__ == '__main__':
    my_markers = session.query(VideoMarker).filter(
        VideoMarker.chapter_id == 2,
        VideoMarker.versenum.in_([3, 4, 5])
    ).all()
    bk = book('csg', 40)
    chp = chapter(28, bk)

    print()
