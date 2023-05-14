from telegram import Video

from sqlalchemy import select

from bot.logs import get_logger
from bot.database import session
from bot.database.schema import Language
from bot.database.schema import Edition
from bot.database.schema import Book
from bot.database.schema import Chapter
from bot.database.schema import VideoMarker
from bot.database.schema import File
from bot.database.schema import User
from bot import exc


logger = get_logger(__name__)

def sign_languages() -> list[Language]:
    return session.query(Language).filter(Language.is_sign_language == True).order_by(Language.meps_symbol.asc()).all()

def languages() -> list[Language]:
    return session.query(Language).order_by(Language.meps_symbol.asc()).all()

def language(
        id: int | None = None, # pylint: disable=redefined-builtin
        meps_symbol: str | None = None,
        code: str | None = None
    ) -> Language | None:
    q = session.query(Language)
    if id is not None:
        q = q.filter(Language.id == id)
    elif meps_symbol is not None:
        q = q.filter(Language.meps_symbol == meps_symbol)
    elif code is not None:
        q = q.filter(Language.code == code)
    else:
        raise TypeError('get_language expected one argument')
    return q.one_or_none()

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


def books(
        language_code: str = None,
        booknum: int = None,
    ) -> list[Book]:
    q = session.query(Book)
    if isinstance(language_code, str):
        q = (q
             .join(Edition, Edition.id == Book.edition_id)
             .join(Language, Language.id == Edition.language_id)
             .filter(Language.code == language_code)
        )
    if isinstance(booknum, int):
        q = q.filter(Book.number == booknum)
    return q.order_by(Book.number.asc()).all()


def book(language_code: str,
             booknum: int | str,
             edition_id: int | None = None
             ) -> Book | None:
    q = (
        session.query(Book)
        .join(Edition, Edition.id == Book.edition_id)
        .join(Language, Language.id == Edition.language_id)
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
         .join(Language, Language.id == Edition.language_id)
         .filter(Language.id == book.edition.language.id,
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
         .join(Language, Language.id == Edition.language_id)
         .filter(Language.id == book.edition.language.id,
                 Book.number == book.number,
        ).order_by(Chapter.id.asc())
    ).all()

def videomarkers(chapter: Chapter, verses: list[int]) -> list[VideoMarker]:
    return session.query(VideoMarker).filter(
        VideoMarker.chapter_id == chapter.id,
        VideoMarker.versenum.in_(verses)
    ).all()


def file(chapter: Chapter,
         verses: list[int],
         overlay_language_code: str,
         checksum: str | None = None,
         ) -> File | None:
    q = session.query(File) \
        .join(Chapter, Chapter.id == File.chapter_id) \
        .join(Book, Book.id == Chapter.book_id) \
        .join(Edition, Edition.id == Book.edition_id) \
        .join(Language, Language.id == Edition.language_id) \
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
        overlay_language_code: int = None,
    ) -> list[File | None]:
    q = (
        session.query(File)
        .join(Chapter, Chapter.id == File.chapter_id)
        .join(Book, Book.id == Chapter.book_id)
        .join(Edition, Edition.id == Book.edition_id)
        .join(Language, Language.id == Edition.language_id)
    )
    if sign_language_code is not None:
        q = q.filter(Language.code == sign_language_code)
    if booknum is not None:
        q = q.filter(Book.number == booknum)
    if chapternum is not None:
        q = q.filter(File.chapter == chapternum)
    if raw_verses is not None:
        q = q.filter(File.raw_verses == raw_verses)
    if checksum is not None:
        q = q.filter(File.checksum == checksum)
    if overlay_language_code is not None:
        q = (q
             .filter(
            File.overlay_language_id == language(code=overlay_language_code).id if overlay_language_code else None
            )
        )
    return q.all()


# def get_chapter(jw: SignsBible) -> Chapter | None:
#     q = (
#         session.query(Chapter)
#         .join(Book, Book.id == Chapter.book_id)
#         .join(Edition, Edition.id == Book.edition_id)
#         .join(Language, Language.id == Edition.language_id)
#         .filter(
#             Language.meps_symbol == jw.language_meps_symbol,
#             Book.number == jw.booknum,
#             Chapter.number == jw.chapternum,
#             Chapter.checksum == jw.get_checksum()
#         )
#     )
#     return q.one_or_none()


# def get_videomarker(jw: SignsBible) -> VideoMarker | None:
#     assert len(jw.verses) == 1
#     q = (
#         session.query(VideoMarker)
#         .join(Language, Language.id == Edition.language_id)
#         .join(Edition, Edition.id == Book.edition_id)
#         .join(Book, Book.id == Chapter.book_id)
#         .join(Chapter, Chapter.id == VideoMarker.chapter_id)
#         .filter(
#             Language.meps_symbol == jw.language_meps_symbol,
#             Book.number == jw.booknum,
#             Chapter.number == jw.chapternum,
#             Chapter.checksum == jw.get_checksum(),
#             VideoMarker.versenum == jw.verses[0],
#         )
#     )
#     return q.one_or_none()



# def get_videomarkers(jw: SignsBible) -> list[VideoMarker | None]:
#     q = (
#         session.query(VideoMarker)
#         .join(Language, Language.id == Edition.language_id)
#         .join(Edition, Edition.id == Book.edition_id)
#         .join(Book, Book.id == Chapter.book_id)
#         .join(Chapter, Chapter.id == VideoMarker.chapter_id)
#         .filter(
#             Language.meps_symbol == jw.language_meps_symbol,
#             Book.number == jw.booknum,
#             Chapter.number == jw.chapternum,
#             Chapter.checksum == jw.get_checksum(),
#         )
#         .order_by(VideoMarker.versenum.asc())
#     )
#     # print(q.statement.compile(compile_kwargs={"literal_binds": True}))
#     return q.all()


# def get_all_versenumbers(jw: SignsBible | None = None) -> list[int | None]:
#     return [row[0] for row in (
#         session.query(VideoMarker.versenum)
#         .join(Chapter, Chapter.id == VideoMarker.chapter_id)
#         .join(Book, Book.id == Chapter.book_id)
#         .join(Edition, Edition.id == Book.edition_id)
#         .join(Language, Language.id == Edition.language_id)
#         .filter(
#             Language.meps_symbol == jw.language_meps_symbol,
#             Book.number == jw.booknum,
#             Chapter.number == jw.chapternum,
#             Chapter.checksum == jw.get_checksum(),
#         )
#         .all()
#     )]


# def get_file(
#         jw: SignsBible,
#         overlay_language_code: int = 0,
#     ) -> File | None:
#     q = (
#         session.query(File)
#         .join(Chapter, Chapter.id == File.chapter_id)
#         .join(Book, Book.id == Chapter.book_id)
#         .join(Edition, Edition.id == Book.edition_id)
#         .join(Language, Language.id == Edition.language_id)
#         .filter(
#             Language.meps_symbol == jw.language_meps_symbol,
#             Book.number == jw.booknum,
#             Chapter.number == jw.chapternum,
#             Chapter.checksum == jw.get_checksum(),
#             File.raw_verses == jw.raw_verses,
#             File.overlay_language_id == get_language(code=overlay_language_code).id if overlay_language_code else None
#         )
#     )
#     # print(q.statement.compile(compile_kwargs={"literal_binds": True}))
#     return q.one_or_none()


if __name__ == '__main__':
    my_markers = session.query(VideoMarker).filter(
        VideoMarker.chapter_id == 2,
        VideoMarker.versenum.in_([3, 4, 5])
    ).all()
    bk = book('csg', 40)
    chp = chapter(28, bk)
    

    print()
