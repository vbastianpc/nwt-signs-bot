from typing import Optional, List, Tuple, Union
from datetime import datetime
import pytz
from sqlalchemy.util.langhelpers import NoneType

from bot import get_logger
from bot.database import SESSION
from bot.database.schemedb import Language
from bot.database.schemedb import BibleBook
from bot.database.schemedb import BibleChapter
from bot.database.schemedb import VideoMarker
from bot.database.schemedb import SentVerse
from bot.database.schemedb import SentVerseUser
from bot.database.schemedb import User
from bot.database.schemedb import BookNamesAbbreviation


logger = get_logger(__name__)


def query_sign_language(lang_code) -> Optional[Language]:
    return (
        SESSION.query(Language)
        .filter(Language.code == lang_code)
        .one_or_none()
    )


def insert_language(lang_code, locale, name, vernacular, rsconf, lib, is_sign_lang) -> Language:
    sign_language = Language(
        code=lang_code,
        locale=locale,
        name=name,
        vernacular=vernacular,
        rsconf=rsconf,
        lib=lib,
        is_sign_lang=is_sign_lang
    )
    SESSION.add(sign_language)
    SESSION.commit()
    return sign_language


def insert_or_update_language(lang_code, locale, name, vernacular, rsconf, lib, is_sign_lang) -> Language:
    sign_language = query_sign_language(lang_code)
    if sign_language:
        return sign_language
    else:
        return insert_language(lang_code, locale, name, vernacular, rsconf, lib, is_sign_lang)

def get_sign_languages() -> List[Language]:
    return SESSION.query(Language).filter(Language.is_sign_lang == True).order_by(Language.code.asc()).all()

def get_languages() -> List[Language]:
    return SESSION.query(Language).order_by(Language.code.asc()).all()

def get_language(lang_code=None, lang_locale=None) -> Optional[Language]:
    if all([lang_locale, lang_code]):
        raise TypeError('lang_code and lang_locale are mutually exclusive arguments')
    q = SESSION.query(Language)
    if lang_code:
        q = q.filter(Language.code == lang_code)
    elif lang_locale:
        q = q.filter(Language.locale == lang_locale)
    else:
        raise TypeError('get_language expected one argument')
    return q.one_or_none()

def get_sign_language_codes() -> List[str]:
    return [
        lang[0] for lang in
        SESSION.query(Language.code)
        .filter(Language.is_sign_lang == True)
        .all()
    ]

def get_user(telegram_user_id) -> Optional[User]:
    return SESSION.query(User).filter(User.telegram_user_id == telegram_user_id).one_or_none()

def get_all_users() -> List[User]:
    return SESSION.query(User).all()

def get_banned_users() -> Optional[List[User]]:
    return SESSION.query(User).filter(User.status == -1).all()

def get_waiting_users() -> Optional[List[User]]:
    return SESSION.query(User).filter(User.status == 0).all()

def get_active_users() -> Optional[List[User]]:
    return SESSION.query(User).filter(User.status == 1).all()

def set_user(
        telegram_user_id,
        lang_code=None,
        full_name=None,
        bot_lang=None,
        waiting=False,
        blocked=False,
        brother=False,
    ) -> User:
    if [waiting, blocked, brother].count(True) > 1:
        raise TypeError('waiting, blocked and brother are mutually exclusive arguments')
    user = get_user(telegram_user_id)
    if not user:
        user = User(telegram_user_id=telegram_user_id)
    if lang_code:
        user.sign_language_id = query_sign_language(lang_code).id
    if full_name:
        user.full_name = full_name
    if bot_lang:
        user.bot_lang = bot_lang
    user.status = -1 if blocked else 0 if waiting else 1 if brother else user.status
    SESSION.add(user)
    SESSION.commit()
    return user

def add_waiting_user(telegram_user_id, full_name, bot_lang) -> None:
    user = get_user(telegram_user_id)
    if not user:
        SESSION.add(User(
            telegram_user_id=telegram_user_id,
            full_name=full_name,
            status=0,
            added_datetime=now(),
            bot_lang=bot_lang,
        ))
        SESSION.commit()


def _query_bible_book(lang_code: str, booknum: Union[int, str]) -> Optional[BibleBook]:
    return (
        SESSION.query(BibleBook)
        .join(Language)
        .filter(
            BibleBook.booknum == int(booknum),
            Language.code == lang_code,
        ).one_or_none()
    )

def _create_bible_book(lang_code: str, booknum: Union[int, str], bookname: str) -> BibleBook:
    sign_language = query_sign_language(lang_code)
    bible_book = BibleBook(
        sign_language_id=sign_language.id,
        booknum=int(booknum),
        bookname=bookname
    )
    SESSION.add(bible_book)
    SESSION.commit()
    return bible_book


def query_or_create_bible_book(**kwargs) -> BibleBook:
    return _query_bible_book(
        kwargs['language'],
        kwargs['booknum'],
    ) or _create_bible_book(
        kwargs['language'],
        kwargs['booknum'],
        kwargs['bookname']
    )


def _get_bible_chapter(
        lang_code: str,
        booknum: Union[int, str],
        chapter: Union[int, str],
    ) -> Optional[BibleChapter]:
    return (
        SESSION.query(BibleChapter)
        .join(Language, Language.id == BibleBook.sign_language_id)
        .join(BibleBook, BibleBook.id == BibleChapter.bible_book_id)
        .filter(
            Language.code == lang_code,
            BibleBook.booknum == int(booknum),
            BibleChapter.chapter == int(chapter),
        )
        .one_or_none()
    )

def get_bible_chapter(**kwargs) -> Optional[BibleChapter]:
    return _get_bible_chapter(
        kwargs['language'],
        kwargs['booknum'],
        kwargs['chapter']
    )

def _add_bible_chapter(
        lang_code: str,
        booknum: Union[int, str],
        chapter: Union[int, str],
        checksum: str
    ) -> BibleChapter:
    bible_book = _query_bible_book(lang_code, booknum)
    bible_chapter = BibleChapter(
        bible_book_id=bible_book.id,
        chapter=int(chapter), 
        checksum=checksum,
    )
    SESSION.add(bible_chapter)
    SESSION.commit()
    return bible_chapter


def touch_checksum(
        lang_code: str,
        booknum: Union[int, str],
        chapter: Union[int, str]
    ) -> Optional[Tuple[BibleChapter, List[SentVerse], str]]:
    bible_chapter = _get_bible_chapter(lang_code, booknum, chapter)
    if bible_chapter is None:
        return
    fake_checksum = f'FAKE CHECKSUM: {now()}'
    checksum = bible_chapter.checksum
    sent_verses = query_sent_verses(lang_code, booknum, chapter, checksum=bible_chapter.checksum)
    for sent_verse in sent_verses:
        sent_verse.checksum = fake_checksum
    SESSION.add_all(sent_verses)
    bible_chapter.checksum = fake_checksum
    SESSION.add(bible_chapter)
    SESSION.commit()
    return (bible_chapter, sent_verses, checksum)


def _query_video_marker(
        lang_code: str,
        booknum: Union[int, str],
        chapter: Union[int, str],
        checksum: str,
        ):
    return (
        SESSION.query(VideoMarker)
        .join(Language, Language.id == BibleBook.sign_language_id)
        .join(BibleBook, BibleBook.id == BibleChapter.bible_book_id)
        .join(BibleChapter, BibleChapter.id == VideoMarker.bible_chapter_id)
        .filter(
            Language.code == lang_code,
            BibleBook.booknum == int(booknum),
            BibleChapter.chapter == int(chapter),
            BibleChapter.checksum == checksum,
        )
    )


def get_videomarker(**kwargs) -> VideoMarker:
    return _query_video_marker(
        kwargs['language'],
        kwargs['booknum'],
        kwargs['chapter'],
        kwargs['checksum'],
    ).filter(VideoMarker.versenum == int(kwargs['versenum'])).one_or_none()


def get_videomarkers(**kwargs) -> List[Optional[VideoMarker]]:
    return _query_video_marker(
        kwargs['language'],
        kwargs['booknum'],
        kwargs['chapter'],
        kwargs['checksum'],
    ).order_by(VideoMarker.versenum.asc()).all()


def _get_all_versenumbers(
        lang_code: str,
        booknum: Union[int, str],
        chapter: Union[int, str],
        checksum: str,
    ) -> List[Optional[int]]:
    return [versenum for versenum, in (
        SESSION.query(VideoMarker.versenum)
        .join(Language, Language.id == BibleBook.sign_language_id)
        .join(BibleBook, BibleBook.id == BibleChapter.bible_book_id)
        .join(BibleChapter, BibleChapter.id == VideoMarker.bible_chapter_id)
        .filter(
            Language.code == lang_code,
            BibleBook.booknum == int(booknum),
            BibleChapter.chapter == int(chapter),
            BibleChapter.checksum == checksum,
        )
        .all()
    )]


def get_all_versenumbers(**kwargs) -> List[Optional[int]]:
    return _get_all_versenumbers(
        kwargs['language'],
        kwargs['booknum'],
        kwargs['chapter'],
        kwargs['checksum'],
    )


def _manage_video_markers(
        function_get_markers,
        # method1 get markers
        # method2 get markers
        lang_code: str,
        booknum: Union[int, str],
        chapter: Union[int, str],
        checksum: str,
    ) -> None:
    bible_chapter = _get_bible_chapter(lang_code, booknum, chapter)
    if bible_chapter:
        logger.info('Tengo %s marcadores', len(bible_chapter.video_markers))
        if bible_chapter.checksum == checksum: # TODO and db.count_markers == len(method1_get_markers) evitar consultar ffmpeg
            logger.info(f'Coinciden checksum {checksum!r}')
        else:
            logger.info(f'No coinciden checksum o hay nuevos marcadores. Intentaré borrar capítulo y sus respectivos marcadores. old {bible_chapter.checksum} != {checksum} new')
            SESSION.delete(bible_chapter)
            SESSION.commit()
            bible_chapter = _add_bible_chapter(lang_code, booknum, chapter, checksum)
    else:
        logger.info('No se ha registrado capitulo. Ahora lo registro')
        bible_chapter = _add_bible_chapter(lang_code, booknum, chapter, checksum)

    if not bible_chapter.video_markers:
        logger.info('No existían marcadores para %s booknum=%s chapter=%s %s', lang_code, booknum, chapter, checksum)
        for marker in function_get_markers():
            bible_chapter.video_markers.append(
                VideoMarker(
                    versenum=int(marker['verseNumber']),
                    start_time=marker['startTime'],
                    duration=marker['duration'],
                    end_transition_duration=marker['endTransitionDuration'],
                    label=marker['label']
                )
            )
        SESSION.add(bible_chapter)
        SESSION.commit()
        logger.info('Marcadores guardados en db')
    else:
        logger.info('Ya existían marcadores en db para %s booknum=%s chapter=%s %s', lang_code, booknum, chapter, checksum)


def manage_video_markers(function_get_markers, **kwargs) -> None:
    _manage_video_markers(
        function_get_markers,
        kwargs['language'],
        kwargs['booknum'],
        kwargs['chapter'],
        kwargs['checksum']
    )


def _query_sent_verse(
        lang_code: str,
        booknum: Union[int, str],
        chapter: Union[int, str],
        checksum: str,
        quality: str,
        raw_verses: Optional[str] = None
    ) -> Optional[SentVerse]:
    q = (
        SESSION.query(SentVerse)
        .join(Language, Language.id == BibleBook.sign_language_id)
        .join(BibleBook, BibleBook.id == SentVerse.bible_book_id)
        .filter(
            Language.code == lang_code,
            BibleBook.booknum == int(booknum),
            SentVerse.chapter == int(chapter),
            SentVerse.checksum == checksum,
            SentVerse.quality == quality,
            SentVerse.raw_verses == raw_verses
        )
    )
    # print(q.statement.compile(compile_kwargs={"literal_binds": True}))
    return q.one_or_none()


def query_sent_verse(**kwargs) -> Optional[SentVerse]:
    return _query_sent_verse(
        kwargs['language'],
        kwargs['booknum'],
        kwargs['chapter'],
        kwargs['checksum'],
        kwargs['quality'],
        kwargs['raw_verses']
    )

def query_sent_verses(
        lang_code: str = None,
        booknum: int = None,
        chapter: int = None,
        raw_verses: str = None,
        checksum: str = None,
    ) -> List[Optional[SentVerse]]:
    q = (
        SESSION.query(SentVerse)
        .join(Language, Language.id == BibleBook.sign_language_id)
        .join(BibleBook, BibleBook.id == SentVerse.bible_book_id)
    )
    if lang_code is not None:
        q = q.filter(Language.code == lang_code)
    if booknum is not None:
        q = q.filter(BibleBook.booknum == int(booknum))
    if chapter is not None:
        q = q.filter(SentVerse.chapter == int(chapter))
    if raw_verses is not None:
        q = q.filter(SentVerse.raw_verses == raw_verses)
    if checksum is not None:
        q = q.filter(SentVerse.checksum == checksum)
    return q.all()

def _add_sent_verse(
        lang_code: str,
        booknum: Union[int, str],
        chapter: Union[int, str],
        checksum: str,
        raw_verses: str,
        citation: str,
        quality: str,
        telegram_file_id: str,
        size: int
    ) -> SentVerse:
    bible_book = _query_bible_book(lang_code, booknum)
    sent_verse = SentVerse(
        checksum=checksum,
        chapter=int(chapter),
        raw_verses=raw_verses,
        citation=citation,
        quality=quality,
        telegram_file_id=telegram_file_id,
        size=size,
        added_datetime=now(),
    )
    bible_book.sent_verses.append(sent_verse)
    SESSION.add(bible_book)
    SESSION.commit()
    return sent_verse


def add_sent_verse(**kwargs) -> SentVerse:
    return _add_sent_verse(
        kwargs['language'],
        kwargs['booknum'],
        kwargs['chapter'],
        kwargs['checksum'],
        kwargs['raw_verses'],
        kwargs['citation'],
        kwargs['quality'],
        kwargs['telegram_file_id'],
        kwargs['size'],
    )


def add_sent_verse_user(sent_verse: SentVerse, telegram_user_id: int) -> None:
    user = get_user(telegram_user_id)
    SESSION.add(SentVerseUser(sent_verse_id=sent_verse.id, user_id=user.id, datetime=now()))
    SESSION.commit()


def add_bookname_abbr(lang_locale: str, booknum: int, fullname: str, long_abbr_name: str, abbr_name: str):
    SESSION.add(
        BookNamesAbbreviation(
            lang_locale=lang_locale,
            booknum=booknum,
            full_name=fullname,
            long_abbr_name=long_abbr_name,
            abbr_name=abbr_name,
        )
    )
    try:
        SESSION.flush()
    except:
        SESSION.rollback()
    SESSION.commit()


def get_booknames(lang_locale=None) -> List[BookNamesAbbreviation]:
    q = SESSION.query(BookNamesAbbreviation)
    if lang_locale:
        q = q.filter(BookNamesAbbreviation.lang_locale == lang_locale)
    return q.order_by(BookNamesAbbreviation.booknum.asc()).all()

def get_bookname(lang_locale, booknum) -> BookNamesAbbreviation:
    q = (
        SESSION.query(BookNamesAbbreviation)
        .filter(
            BookNamesAbbreviation.lang_locale == lang_locale,
            BookNamesAbbreviation.booknum == int(booknum)
        )
    )
    return q.one()


def now() -> str:
    # TODO CONFIG server timezone, local timezone. database name. 
    tzinfo = pytz.timezone('UTC')
    tzinfo.localize(datetime.now())
    return tzinfo.localize(datetime.now()).astimezone(tz=pytz.timezone('America/Santiago')).isoformat(sep=' ', timespec="seconds")

