from collections.abc import Iterable
from datetime import datetime

from telegram import Video

from bot.logs import get_logger
from bot.utils.browser import LazyBrowser
from bot.utils import dt_now
from bot.database import SESSION
from bot.database.schema import Language
from bot.database.schema import Bible
from bot.database.schema import Book
from bot.database.schema import Chapter
from bot.database.schema import VideoMarker
from bot.database.schema import File
from bot.database.schema import File2User
from bot.database.schema import User
from bot.jw.pubmedia import SignsBible
from bot.jw.language import JWLanguage


logger = get_logger(__name__)
browser = LazyBrowser()

# region Language

def fetch_languages():
    jw = JWLanguage()
    languages = []
    for lang in JWLanguage().all_langs:
        if not get_language(meps_symbol=lang['code']):
            jw.meps_symbol = lang['code']
            languages.append(
                Language(
                    meps_symbol=jw.meps_symbol,
                    code=jw.code,
                    name=jw.name,
                    vernacular=jw.vernacular,
                    rsconf=jw.rsconf,
                    lib=jw.lib,
                    is_sign_language=jw.is_sign_language,
                    script=jw.script,
                    is_rtl=jw.is_rtl,
                )
            )
    SESSION.add_all(languages)
    SESSION.commit()

def get_sign_languages() -> list[Language]:
    return SESSION.query(Language).filter(Language.is_sign_language == True).order_by(Language.meps_symbol.asc()).all()

def get_languages() -> list[Language]:
    return SESSION.query(Language).order_by(Language.meps_symbol.asc()).all()

def get_language(
        id: int | None = None, # pylint: disable=redefined-builtin
        meps_symbol: str | None = None,
        code: str | None = None
    ) -> Language | None:
    q = SESSION.query(Language)
    if id is not None:
        q = q.filter(Language.id == id)
    elif meps_symbol is not None:
        q = q.filter(Language.meps_symbol == meps_symbol)
    elif code is not None:
        q = q.filter(Language.code == code)
    else:
        raise TypeError('get_language expected one argument')
    return q.one_or_none()

def get_sign_languages_meps_symbol() -> list[str]:
    return [
        lang[0] for lang in
        SESSION.query(Language.meps_symbol)
        .filter(Language.is_sign_language == True)
        .all()
    ]

# endregion
# region User

def get_user(telegram_user_id) -> User | None:
    return SESSION.query(User).filter(User.telegram_user_id == telegram_user_id).one_or_none()

def get_users() -> list[User | None]:
    return SESSION.query(User).all()

def get_banned_users() -> list[User | None]:
    return SESSION.query(User).filter(User.status == -1).all()

def get_waiting_users() -> list[User | None]:
    return SESSION.query(User).filter(User.status == 0).all()

def get_accepted_users() -> list[User | None]:
    return SESSION.query(User).filter(User.status == 1).all()

def set_user(
        telegram_user_id: int,
        sign_language_code: str | None = None,
        full_name: str | None = None,
        bot_language: Language | None = None,
        status: int | None = None,
        overlay_language: Language | None = None,
        added_datetime: datetime | None = None,
        last_active_datetime: datetime | None = None
    ) -> User:
    user = get_user(telegram_user_id)
    if not user:
        user = User(telegram_user_id=telegram_user_id)
    if sign_language_code:
        try:
            user.sign_language_id = get_language(code=sign_language_code).id
        except AttributeError as exc:
            raise TypeError(f'sign language code: {sign_language_code!r} does not exists') from exc
    if full_name:
        user.full_name = full_name
    if added_datetime:
        user.added_datetime = added_datetime
    if bot_language:
        user.bot_language_id = bot_language.id
    if overlay_language:
        user.overlay_language_id = user.bot_language.id
    elif overlay_language is False:
        user.overlay_language_id = None
    if last_active_datetime:
        user.last_active_datetime = last_active_datetime
    user.status = status if status is not None else user.status
    SESSION.add(user)
    SESSION.commit()
    return user

# endregion

# region Bible
def fetch_bible_editions():
    data = browser.open("https://www.jw.org/en/library/bible/json/").json()
    editions = []
    for d in data['langs'].values():
        language_meps_symbol = d['lang']['langcode']
        language = get_language(meps_symbol=language_meps_symbol)
        try:
            assert language is not None
        except AssertionError:
            continue
        for e in d['editions']:
            if not get_bible(language_code=language.code):
                editions.append(Bible(
                    language_id=language.id,
                    name=e['title'],
                    symbol=e['symbol'],
                    url=e.get('contentAPI')
                ))
    SESSION.add_all(editions)
    SESSION.commit()



def fetch_bible_books(language_code):
    bible = get_bible(language_code)
    data = browser.open(bible.url).json()
    books = []
    for booknum, bookdata in data['editionData']['books'].items():
        book = get_book(language_code=bible.language.code, booknum=booknum, bible_id=bible.id)
        if not book:
            book.append(
                Book(
                    bible_id=bible.id,
                    number=int(booknum),
                    chapter_count=int(bookdata['chapterCount']),
                    name=bookdata.get('standardName'),
                    standard_abbreviation=bookdata.get('standardAbbreviation'),
                    official_abbreviation=bookdata.get('officialAbbreviation'),
                    standard_singular_bookname=bookdata.get('standardSingularBookName'),
                    standard_singular_abbreviation=bookdata.get('standardSingularAbbreviation'),
                    official_singular_abbreviation=bookdata.get('officialSingularAbbreviation'),
                    standard_plural_bookname=bookdata.get('standardPluralBookName'),
                    standard_plural_abbreviation=bookdata.get('standardPluralAbbreviation'),
                    official_plural_abbreviation=bookdata.get('officialPluralAbbreviation'),
                    book_display_title=bookdata.get('bookDisplayTitle'),
                    chapter_display_title=bookdata.get('chapterDisplayTitle')
                )
            )
    SESSION.add_all(books)
    SESSION.commit()


def get_bible(language_code: str) -> Bible | None:
    return (SESSION
            .query(Bible)
            .join(Language)
            .filter(Language.code == language_code)
            .order_by(Bible.id.desc())
            .limit(1)
            .one_or_none()
    )

# endregion
# region Book

def get_books(
        language_code: str = None,
        booknum: int = None,
    ) -> list[Book]:
    q = SESSION.query(Book)
    if isinstance(language_code, str):
        q = (q
             .join(Bible, Bible.id == Book.bible_id)
             .join(Language, Language.id == Bible.language_id)
             .filter(Language.code == language_code)
        )
    if isinstance(booknum, int):
        q = q.filter(Book.number == booknum)
    return q.order_by(Book.number.asc()).all()


def get_book(language_code: str,
             booknum: int | str,
             bible_id: int | None = None
             ) -> Book | None:
    q = (
        SESSION.query(Book)
        .join(Bible, Bible.id == Book.bible_id)
        .join(Language, Language.id == Bible.language_id)
        .filter(
            Book.number == int(booknum),
            Language.code == language_code,
        )
    )
    if isinstance(bible_id, int):
        q = q.filter(Bible.id == bible_id)
    return q.one_or_none()

# endregion

# region Chapter
def get_chapter(jw: SignsBible) -> Chapter | None:
    q = (
        SESSION.query(Chapter)
        .join(Book, Book.id == Chapter.book_id)
        .join(Bible, Bible.id == Book.bible_id)
        .join(Language, Language.id == Bible.language_id)
        .filter(
            Language.meps_symbol == jw.language_meps_symbol,
            Book.number == jw.booknum,
            Chapter.number == jw.chapternum,
            Chapter.checksum == jw.get_checksum()
        )
    )
    return q.one_or_none()


def _add_chapter(
        language: Language,
        booknum: int | str,
        chapternum: int | str,
        checksum: str,
        modified_datetime: datetime,
        url: str,
        title: str,
    ) -> Chapter:
    book = get_book(language.code, booknum)
    chapter = Chapter(
        book_id=book.id,
        number=int(chapternum),
        checksum=checksum,
        modified_datetime=modified_datetime,
        url=url,
        title=title,
    )
    SESSION.add(chapter)
    SESSION.commit()
    return chapter

# endregion

# def touch_checksum(
#         sign_language_meps_symbol: str,
#         booknum: Union[int, str],
#         chapternum: Union[int, str],
#         **kwargs
#     ) -> Tuple[Chapter, list[File], str]]:
#     bible_chapter = get_chapter(sign_language_meps_symbol, booknum, chapternum)
#     if bible_chapter is None:
#         return
#     fake_checksum = f'FAKE CHECKSUM: {dt_now()}'
#     checksum = bible_chapter.checksum
#     files = get_files(sign_language_meps_symbol, booknum, chapternum, checksum=bible_chapter.checksum)
#     for file in files:
#         file.checksum = fake_checksum
#     SESSION.add_all(files)
#     bible_chapter.checksum = fake_checksum
#     SESSION.add(bible_chapter)
#     SESSION.commit()
#     return (bible_chapter, files, checksum)

# region VideoMarker

def get_videomarker(jw: SignsBible) -> VideoMarker | None:
    assert len(jw.verses) == 1
    q = (
        SESSION.query(VideoMarker)
        .join(Language, Language.id == Bible.language_id)
        .join(Bible, Bible.id == Book.bible_id)
        .join(Book, Book.id == Chapter.book_id)
        .join(Chapter, Chapter.id == VideoMarker.chapter_id)
        .filter(
            Language.meps_symbol == jw.language_meps_symbol,
            Book.number == jw.booknum,
            Chapter.number == jw.chapternum,
            Chapter.checksum == jw.get_checksum(),
            VideoMarker.versenum == jw.verses[0],
        )
    )
    return q.one_or_none()



def get_videomarkers(jw: SignsBible) -> list[VideoMarker | None]:
    q = (
        SESSION.query(VideoMarker)
        .join(Language, Language.id == Bible.language_id)
        .join(Bible, Bible.id == Book.bible_id)
        .join(Book, Book.id == Chapter.book_id)
        .join(Chapter, Chapter.id == VideoMarker.chapter_id)
        .filter(
            Language.meps_symbol == jw.language_meps_symbol,
            Book.number == jw.booknum,
            Chapter.number == jw.chapternum,
            Chapter.checksum == jw.get_checksum(),
        )
        .order_by(VideoMarker.versenum.asc())
    )
    # print(q.statement.compile(compile_kwargs={"literal_binds": True}))
    return q.all()


def get_all_versenumbers(jw: SignsBible | None = None) -> list[int | None]:
    return [row[0] for row in (
        SESSION.query(VideoMarker.versenum)
        .join(Chapter, Chapter.id == VideoMarker.chapter_id)
        .join(Book, Book.id == Chapter.book_id)
        .join(Bible, Bible.id == Book.bible_id)
        .join(Language, Language.id == Bible.language_id)
        .filter(
            Language.meps_symbol == jw.language_meps_symbol,
            Book.number == jw.booknum,
            Chapter.number == jw.chapternum,
            Chapter.checksum == jw.get_checksum(),
        )
        .all()
    )]

def manage_video_markers(jw: SignsBible) -> None:
    chapter = get_chapter(jw)
    language = get_language(meps_symbol=jw.language_meps_symbol)
    video_markers = get_videomarkers(jw)
    data = (
        language,
        jw.booknum,
        jw.chapternum,
        jw.get_checksum(),
        jw.get_modified_datetime(),
        jw.get_video_url(),
        jw.get_title(),
    )
    if video_markers:
        return
    elif chapter and chapter.checksum == jw.get_checksum():
        _add_video_markers(chapter, jw.get_markers())
    elif chapter and chapter.checksum != jw.get_checksum():
        logger.info('Hay versión actualizada.')
        SESSION.query(VideoMarker).filter(VideoMarker.chapter_id == chapter.id).delete()
        SESSION.commit()
        chapter = _add_chapter(*data)
        _add_video_markers(chapter, jw.get_markers())
    elif not chapter:
        if not get_bible(language_code=language.code):
            fetch_bible_editions()
        if not get_books(language_code=language.code):
            fetch_bible_books(language_code=language.code)
        chapter = _add_chapter(*data)
        _add_video_markers(chapter, jw.get_markers())


def _add_video_markers(chapter: Chapter, markers: Iterable):
    for marker in markers:
        chapter.video_markers.append(
            VideoMarker(
                versenum=int(marker['verseNumber']),
                label=marker['label'],
                duration=marker['duration'],
                start_time=marker['startTime'],
                end_transition_duration=marker['endTransitionDuration'],
            )
        )
    SESSION.add(chapter)
    SESSION.commit()



# endregion
#region File

def get_file(
        jw: SignsBible,
        overlay_language_code: int = 0,
    ) -> File | None:
    q = (
        SESSION.query(File)
        .join(Chapter, Chapter.id == File.chapter_id)
        .join(Book, Book.id == Chapter.book_id)
        .join(Bible, Bible.id == Book.bible_id)
        .join(Language, Language.id == Bible.language_id)
        .filter(
            Language.meps_symbol == jw.language_meps_symbol,
            Book.number == jw.booknum,
            Chapter.number == jw.chapternum,
            Chapter.checksum == jw.get_checksum(),
            File.raw_verses == jw.raw_verses,
            File.overlay_language_id == get_language(code=overlay_language_code).id if overlay_language_code else None
        )
    )
    # print(q.statement.compile(compile_kwargs={"literal_binds": True}))
    return q.one_or_none()


def get_files(
        sign_language_code: str = None,
        booknum: int = None,
        chapternum: int = None,
        raw_verses: str = None,
        checksum: str = None,
        overlay_language_code: int = None,
    ) -> list[File | None]:
    q = (
        SESSION.query(File)
        .join(Chapter, Chapter.id == File.chapter_id)
        .join(Book, Book.id == Chapter.book_id)
        .join(Bible, Bible.id == Book.bible_id)
        .join(Language, Language.id == Bible.language_id)
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
            File.overlay_language_id == get_language(code=overlay_language_code).id if overlay_language_code else None
            )
        )
    return q.all()

def add_file(
        tg_video: Video,
        jw: SignsBible,
        overlay_language_id: int | None,
    ) -> File:
    chapter = get_chapter(jw)
    file = File(
        telegram_file_id=tg_video.file_id,
        telegram_file_unique_id=tg_video.file_unique_id,
        duration=tg_video.duration,
        name=tg_video.file_name,
        size=tg_video.file_size,
        added_datetime=dt_now(),
        raw_verses=jw.raw_verses,
        overlay_language_id=overlay_language_id,
        is_single_verse=True if len(jw.verses) == 1 else False
    )
    chapter.files.append(file)
    SESSION.add(chapter)
    SESSION.commit()
    return file



def add_file2user(file: File, telegram_user_id: int) -> None:
    user = get_user(telegram_user_id)
    SESSION.add(File2User(file_id=file.id, user_id=user.id, datetime=dt_now()))
    SESSION.commit()

# endregion
