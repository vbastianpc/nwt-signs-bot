from typing import Optional, List, Union
import logging
from datetime import datetime
import pytz

from bot.database import SESSION
from bot.database.schemedb import SignLanguage
from bot.database.schemedb import BibleBook
from bot.database.schemedb import BibleChapter
from bot.database.schemedb import VideoMarker
from bot.database.schemedb import SentVerse
from bot.database.schemedb import SentVerseUser
from bot.database.schemedb import User


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def query_sign_language(lang_code) -> Optional[SignLanguage]:
    return (
        SESSION.query(SignLanguage)
        .filter(SignLanguage.lang_code == lang_code)
        .one_or_none()
    )

def insert_or_update_sign_language(lang_code, locale, name, vernacular, rsconf, lib) -> SignLanguage:
    sign_language = query_sign_language(lang_code)
    if not sign_language:
        sign_language = SignLanguage(lang_code=lang_code)
    sign_language.locale = locale
    sign_language.name = name
    sign_language.vernacular = vernacular
    sign_language.rsconf = rsconf
    sign_language.lib = lib
    SESSION.add(sign_language)
    SESSION.commit()
    return sign_language


def get_user(telegram_user_id) -> Optional[User]:
    return SESSION.query(User).filter(User.telegram_user_id == telegram_user_id).one_or_none()


def get_all_users() -> List[User]:
    return SESSION.query(User).filter(User.status == 1).all()

def set_user(
        user_id,
        lang_code=None,
        full_name=None,
        waiting=False,
        blocked=False,
        brother=False,
    ) -> User:
    assert [waiting, blocked, brother].count(True) <= 1, 'waiting, blocked and brother are mutually exclusive arguments' 
    user = get_user(user_id)
    user.sign_language_id = query_sign_language(lang_code).id if lang_code else user.sign_language_id
    user.full_name = full_name or user.full_name
    user.status = -1 if waiting else 0 if blocked else 1 if brother else user.status
    SESSION.add(user)
    SESSION.commit()
    return user

def add_waiting_user(telegram_user_id, full_name) -> None:
    user = get_user(telegram_user_id)
    if not user:
        SESSION.add(User(
            telegram_user_id=telegram_user_id,
            full_name=full_name,
            status=-1,
            added_datetime=now(),
        ))
        SESSION.commit()


def _query_bible_book(lang_code: str, booknum: Union[int, str]) -> Optional[BibleBook]:
    return (
        SESSION.query(BibleBook)
        .join(SignLanguage)
        .filter(
            BibleBook.booknum == int(booknum),
            SignLanguage.lang_code == lang_code,
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
        kwargs['lang_code'],
        kwargs['booknum'],
    ) or _create_bible_book(
        kwargs['lang_code'],
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
        .join(SignLanguage, SignLanguage.id == BibleBook.sign_language_id)
        .join(BibleBook, BibleBook.id == BibleChapter.bible_book_id)
        .filter(
            SignLanguage.lang_code == lang_code,
            BibleBook.booknum == int(booknum),
            BibleChapter.chapter == int(chapter),
        )
        .one_or_none()
    )

def get_bible_chapter(**kwargs) -> Optional[BibleChapter]:
    return _get_bible_chapter(
        kwargs['lang_code'],
        kwargs['booknum'],
        kwargs['chapter']
    )

def _add_bible_chapter(
        lang_code: str,
        booknum: Union[int, str],
        chapter: Union[int, str],
        representative_datetime: str,
    ) -> BibleChapter:
    bible_book = _query_bible_book(lang_code, booknum)
    bible_chapter = BibleChapter(
        bible_book_id=bible_book.id,
        chapter=int(chapter), 
        representative_datetime=representative_datetime,
    )
    SESSION.add(bible_chapter)
    SESSION.commit()
    return bible_chapter


def _query_video_marker(
        lang_code: str,
        booknum: Union[int, str],
        chapter: Union[int, str],
        representative_datetime: str,
        ):
    return (
        SESSION.query(VideoMarker)
        .join(SignLanguage, SignLanguage.id == BibleBook.sign_language_id)
        .join(BibleBook, BibleBook.id == BibleChapter.bible_book_id)
        .join(BibleChapter, BibleChapter.id == VideoMarker.bible_chapter_id)
        .filter(
            SignLanguage.lang_code == lang_code,
            BibleBook.booknum == int(booknum),
            BibleChapter.chapter == int(chapter),
            BibleChapter.representative_datetime == representative_datetime,
        )
    )


def get_videomarker(**kwargs) -> VideoMarker:
    return _query_video_marker(
        kwargs['lang_code'],
        kwargs['booknum'],
        kwargs['chapter'],
        kwargs['representative_datetime'],
    ).filter(VideoMarker.versenum == int(kwargs['versenum'])).one_or_none()


def get_videomarkers(**kwargs) -> List[Optional[VideoMarker]]:
    return _query_video_marker(
        kwargs['lang_code'],
        kwargs['booknum'],
        kwargs['chapter'],
        kwargs['representative_datetime'],
    ).order_by(VideoMarker.versenum.asc()).all()


def _get_all_versenumbers(
        lang_code: str,
        booknum: Union[int, str],
        chapter: Union[int, str],
        representative_datetime: str,
    ) -> List[Optional[int]]:
    return [versenum for versenum, in (
        SESSION.query(VideoMarker.versenum)
        .join(SignLanguage, SignLanguage.id == BibleBook.sign_language_id)
        .join(BibleBook, BibleBook.id == BibleChapter.bible_book_id)
        .join(BibleChapter, BibleChapter.id == VideoMarker.bible_chapter_id)
        .filter(
            SignLanguage.lang_code == lang_code,
            BibleBook.booknum == int(booknum),
            BibleChapter.chapter == int(chapter),
            BibleChapter.representative_datetime == representative_datetime,
        )
        .all()
    )]


def get_all_versenumbers(**kwargs) -> List[Optional[int]]:
    return _get_all_versenumbers(
        kwargs['lang_code'],
        kwargs['booknum'],
        kwargs['chapter'],
        kwargs['representative_datetime'],
    )


def _manage_video_markers(
        function_get_markers,
        lang_code: str,
        booknum: Union[int, str],
        chapter: Union[int, str],
        representative_datetime: str,
    ) -> None:
    bible_chapter = _get_bible_chapter(lang_code, booknum, chapter)
    if bible_chapter:
        logger.info('Tengo %s marcadores', len(bible_chapter.video_markers))
        if bible_chapter.representative_datetime != representative_datetime:
            logger.info('No coinciden datetime. Intentaré borrar capítulo y sus respectivos marcadores')
            SESSION.delete(bible_chapter)
            SESSION.commit()
            bible_chapter = _add_bible_chapter(lang_code, booknum, chapter, representative_datetime)
        else:
            logger.info('Coinciden datetime')
    else:
        logger.info('No se ha registrado capitulo. Ahora lo registro')
        bible_chapter = _add_bible_chapter(lang_code, booknum, chapter, representative_datetime)

    if not bible_chapter.video_markers:
        logger.info('No existían marcadores para %s booknum=%s chapter=%s %s', lang_code, booknum, chapter, representative_datetime)
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
        logger.info('Ya existían marcadores en db para %s booknum=%s chapter=%s %s', lang_code, booknum, chapter, representative_datetime)


def manage_video_markers(function_get_markers, **kwargs) -> None:
    _manage_video_markers(
        function_get_markers,
        kwargs['lang_code'],
        kwargs['booknum'],
        kwargs['chapter'],
        kwargs['representative_datetime'],
    )


def _query_sent_verse(
        lang_code: str,
        booknum: Union[int, str],
        chapter: Union[int, str],
        representative_datetime: str,
        quality: str,
        raw_verses: Optional[str] = None
    ) -> Optional[SentVerse]:
    q = (
        SESSION.query(SentVerse)
        .join(SignLanguage, SignLanguage.id == BibleBook.sign_language_id)
        .join(BibleBook, BibleBook.id == SentVerse.bible_book_id)
        .filter(
            SignLanguage.lang_code == lang_code,
            BibleBook.booknum == int(booknum),
            SentVerse.chapter == int(chapter),
            SentVerse.representative_datetime == representative_datetime,
            SentVerse.quality == quality,
            SentVerse.raw_verses == raw_verses
        )
    )
    # print(q.statement.compile(compile_kwargs={"literal_binds": True}))
    return q.one_or_none()


def query_sent_verse(**kwargs) -> Optional[SentVerse]:
    return _query_sent_verse(
        kwargs['lang_code'],
        kwargs['booknum'],
        kwargs['chapter'],
        kwargs['representative_datetime'],
        kwargs['quality'],
        kwargs['raw_verses']
    )


def _add_sent_verse(
        lang_code: str,
        booknum: Union[int, str],
        chapter: Union[int, str],
        representative_datetime: str,
        raw_verses: str,
        citation: str,
        quality: str,
        telegram_file_id: str,
        size: int
    ) -> SentVerse:
    bible_book = _query_bible_book(lang_code, booknum)
    sent_verse = SentVerse(
        representative_datetime=representative_datetime,
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
        kwargs['lang_code'],
        kwargs['booknum'],
        kwargs['chapter'],
        kwargs['representative_datetime'],
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


def now():
    # TODO CONFIG server timezone
    return datetime.now().astimezone(tz=pytz.timezone('America/Santiago')).isoformat(sep=' ', timespec="seconds")

