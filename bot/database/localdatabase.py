from typing import Optional, List, Union, Iterable
from datetime import datetime


from sqlalchemy.exc import IntegrityError
from telegram import Video

from bot.logs import get_logger
from bot.utils.browser import LazyBrowser
from bot.utils import dt_now
from bot.database import SESSION
from bot.database.schemedb import Language
from bot.database.schemedb import Bible
from bot.database.schemedb import Book
from bot.database.schemedb import Chapter
from bot.database.schemedb import VideoMarker
from bot.database.schemedb import File
from bot.database.schemedb import File2User
from bot.database.schemedb import User
from bot.jw.pubmedia import SignsBible
from bot.jw.language import JWLanguage


logger = get_logger(__name__)

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


def get_sign_languages() -> List[Language]:
    return SESSION.query(Language).filter(Language.is_sign_language == True).order_by(Language.meps_symbol.asc()).all()

def get_languages() -> List[Language]:
    return SESSION.query(Language).order_by(Language.meps_symbol.asc()).all()

def get_language(
        id: Optional[int] = None,
        meps_symbol: Optional[str] = None,
        code: Optional[str] = None
    ) -> Optional[Language]:
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

def get_sign_languages_meps_symbol() -> List[str]:
    return [
        lang[0] for lang in
        SESSION.query(Language.meps_symbol)
        .filter(Language.is_sign_language == True)
        .all()
    ]

# endregion
# region User

def get_user(telegram_user_id) -> Optional[User]:
    return SESSION.query(User).filter(User.telegram_user_id == telegram_user_id).one_or_none()

def get_users() -> List[User]:
    return SESSION.query(User).all()

def get_banned_users() -> Optional[List[User]]:
    return SESSION.query(User).filter(User.status == -1).all()

def get_waiting_users() -> Optional[List[User]]:
    return SESSION.query(User).filter(User.status == 0).all()

def get_accepted_users() -> Optional[List[User]]:
    return SESSION.query(User).filter(User.status == 1).all()

def set_user(
        telegram_user_id: int,
        sign_language_code: str = None,
        full_name: str = None,
        bot_language: Language = None,
        waiting: bool = False,
        blocked: bool = False,
        brother: bool = False,
        overlay_language: Language = None,
        added_datetime: datetime = None
    ) -> User:
    if [waiting, blocked, brother].count(True) > 1:
        raise TypeError('waiting, blocked and brother are mutually exclusive arguments')
    user = get_user(telegram_user_id)
    if not user:
        user = User(telegram_user_id=telegram_user_id)
    if sign_language_code:
        try:
            user.sign_language_id = get_language(code=sign_language_code).id
        except AttributeError:
            raise TypeError(f'sign language code: {sign_language_code!r} does not exists')
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
    user.status = -1 if blocked else 0 if waiting else 1 if brother else user.status
    SESSION.add(user)
    SESSION.commit()
    return user

# endregion

# region Bible
def fetch_bible_editions():
    browser = LazyBrowser()
    data = browser.open("https://www.jw.org/en/library/bible/json/").json()
    for d in data['langs'].values():
        language_meps_symbol = d['lang']['langcode']
        language = get_language(meps_symbol=language_meps_symbol)
        try:
            assert language is not None
        except AssertionError:
            continue
        for e in d['editions']:
            bible = Bible(
                language_id=language.id,
                name=e['title'],
                symbol=e['symbol'],
                url=e.get('contentAPI')
            )
            SESSION.add(bible)
            try:
                SESSION.commit()
            except IntegrityError:
                SESSION.rollback()

def fetch_bible_books(language_meps_symbol):
    bible = get_bible(language_meps_symbol)
    browser = LazyBrowser()
    data = browser.open(bible.url).json()
    for booknum, bookdata in data['editionData']['books'].items():
        SESSION.add(
            Book(
                bible_id=bible.id,
                number=int(booknum),
                chapter_count=int(bookdata['chapterCount']),
                name=bookdata['standardName'].strip('.'),
                standard_abbreviation=bookdata['standardAbbreviation'].strip('.'),
                official_abbreviation=bookdata['officialAbbreviation'].strip('.'),
                standard_singular_bookname=bookdata['standardSingularBookName'].strip('.'),
                standard_singular_abbreviation=bookdata['standardSingularAbbreviation'].strip('.'),
                official_singular_abbreviation=bookdata['officialSingularAbbreviation'].strip('.'),
                standard_plural_bookname=bookdata['standardPluralBookName'].strip('.'),
                standard_plural_abbreviation=bookdata['standardPluralAbbreviation'].strip('.'),
                official_plural_abbreviation=bookdata['officialPluralAbbreviation'].strip('.'),
                book_display_title=bookdata['bookDisplayTitle'].strip('.'),
                chapter_display_title=bookdata['chapterDisplayTitle'].strip('.')
            )
        )
    try:
        SESSION.commit()
    except IntegrityError as e:
        logger.warning("%s", e)
        SESSION.rollback()
    return

def get_bible(language_meps_symbol: str) -> Optional[Bible]:
    return SESSION.query(Bible).join(Language).filter(Language.meps_symbol == language_meps_symbol).order_by(Bible.id.asc()).limit(1).one_or_none()

# endregion
# region Book

def get_books(
        language_id: int = None,
        booknum: int = None,
    ) -> List[Book]:
    q = SESSION.query(Book)
    if language_id:
        q = q.join(Bible, Bible.id == Book.bible_id).join(Language, Language.id == Bible.language_id)
    if language_id:
        q = q.filter(Language.id == language_id)
    if booknum is not None:
        q = q.filter(Book.number == booknum)
    return q.order_by(Book.number.asc()).all()


def get_book(language: Language,
             booknum: Union[int, str]) -> Optional[Book]:
    return (
        SESSION.query(Book)
        .join(Bible, Bible.id == Book.bible_id)
        .join(Language, Language.id == Bible.language_id)
        .filter(
            Book.number == int(booknum),
            Language.id == language.id,
        ).one_or_none()
    )

# endregion

# region Chapter
def get_chapter(jw: Optional[SignsBible] = None) -> Optional[Chapter]:
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
        booknum: Union[int, str],
        chapternum: Union[int, str],
        checksum: str,
        modified_datetime: Union[datetime, str],
        url: str,
        title: str,
    ) -> Chapter:
    book = get_book(language, booknum)
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
#     ) -> Optional[Tuple[Chapter, List[File], str]]:
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

def get_videomarker(jw: SignsBible):
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



def get_videomarkers(jw: SignsBible):
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


def get_all_versenumbers(jw: SignsBible = None) -> List[Optional[int]]:
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
    print(f'{data=}')
    if video_markers:
        return
    elif chapter and chapter.checksum == jw.get_checksum():
        _add_video_markers(chapter, jw.get_markers())
    elif chapter and chapter.checksum != jw.get_checksum():
        logger.info(f'Hay versión actualizada.')
        SESSION.query(VideoMarker).filter(VideoMarker.chapter_id == chapter.id).delete()
        SESSION.commit()
        chapter = _add_chapter(*data)
        _add_video_markers(chapter, jw.get_markers())
    elif not chapter:
        if not get_bible(jw.language_meps_symbol):
            fetch_bible_editions()
        fetch_bible_books(jw.language_meps_symbol)
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
        jw: SignsBible = None,
        overlay_language_id: Optional[int] = None,
    ) -> Optional[File]:
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
            File.overlay_language_id == overlay_language_id
        )
    )
    # print(q.statement.compile(compile_kwargs={"literal_binds": True}))
    return q.one_or_none()


def get_files(
        sign_language_meps_symbol: str = None,
        booknum: int = None,
        chapternum: int = None,
        raw_verses: str = None,
        checksum: str = None,
        overlay_language_id: int = None,
    ) -> List[Optional[File]]:
    q = (
        SESSION.query(File)
        .join(Chapter, Chapter.id == File.chapter_id)
        .join(Book, Book.id == Chapter.book_id)
        .join(Bible, Bible.id == Book.bible_id)
        .join(Language, Language.id == Bible.language_id)
    )
    if sign_language_meps_symbol is not None:
        q = q.filter(Language.meps_symbol == sign_language_meps_symbol)
    if booknum is not None:
        q = q.filter(Book.number == booknum)
    if chapternum is not None:
        q = q.filter(File.chapter == chapternum)
    if raw_verses is not None:
        q = q.filter(File.raw_verses == raw_verses)
    if checksum is not None:
        q = q.filter(File.checksum == checksum)
    if overlay_language_id is not None:
        q = q.filter(File.overlay_language_id == overlay_language_id)
    return q.all()

def add_file(
        tg_video: Video,
        jw: SignsBible,
        overlay_language_id: Optional[int],
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
