from datetime import datetime
from time import sleep
import pytz
from collections.abc import Iterator
import random

from telegram import Bot
from telegram.error import BadRequest
from sqlalchemy import select

from bot.migration.old_schema import old_session
from bot.migration.old_schema import Language as oLanguage
from bot.migration.old_schema import BibleBook as oBibleBook
from bot.migration.old_schema import BibleChapter as oBibleChapter
from bot.migration.old_schema import VideoMarker as oVideoMarker
from bot.migration.old_schema import SentVerse as oSentVerse
from bot.migration.old_schema import User as oUser
from bot.migration.old_schema import SentVerseUser as oSentVerseUser
from bot.migration.old_schema import BookNamesAbbreviation as oBookNamesAbbreviation

from bot.jw import BiblePassage
from bot.database import session
from bot.database.schema import Bible
from bot.database.schema import Language
from bot.database.schema import Edition
from bot.database.schema import Book
from bot.database.schema import Chapter
from bot.database.schema import VideoMarker
from bot.database.schema import File
from bot.database.schema import User
from bot.database.schema import File2User
from bot.database import get
from bot.database import fetch
from bot.utils.browser import browser
from bot.utils import how_to_say, dt_now, safechars
from bot.logs import get_logger
from bot.secret import TOKEN
from bot.utils.video import parse_time

logger = get_logger(__name__)

bot = Bot(TOKEN)


def migrate_users():
    ousers: list[oUser] = old_session.query(oUser).all()
    users = []
    for ouser in ousers:
        bot_language = get.language(code=ouser.bot_lang)
        if ouser.sign_language_id is not None:
            sl_code = old_session.query(oLanguage).where(oLanguage.id == ouser.sign_language_id).one().locale
        else:
            sl_code = None
        try:
            member = bot.get_chat_member(chat_id=ouser.telegram_user_id, user_id=ouser.telegram_user_id)
        except BadRequest:
            member = None
        users.append(User(
            id=ouser.id,
            telegram_user_id=ouser.telegram_user_id,
            first_name=member.user.first_name if member else ouser.full_name,
            last_name=member.user.last_name if member else None,
            user_name=member.user.username if member else None,
            is_premium=member.user.is_premium if member else False,
            sign_language_code=sl_code.replace('_', '-'),
            bot_language_code=bot_language.code,
            overlay_language_code=None,
            sign_language_name=how_to_say(sl_code, bot_language.code) if sl_code else bot_language.vernacular,
            status=ouser.status,
            added_datetime=datetime.fromisoformat(ouser.added_datetime) if ouser.added_datetime else dt_now(),
            last_active_datetime=None
        ))
    session.add_all(users)
    session.commit()


def migrate_books():
    language_codes: list[str] = old_session.scalars(
        select(oLanguage.locale).select_from(oBibleBook)
        .join(oLanguage, oLanguage.id == oBibleBook.sign_language_id).distinct()
        ).all()
    language_codes += old_session.scalars(
        select(oLanguage.locale).select_from(oUser)
        .join(oLanguage, oLanguage.locale == oUser.bot_lang).distinct()
    ).all()
    for language_code in language_codes:
        language_code = language_code.replace('_', '-')
        if not get.books(language_code):
            fetch.books(language_code)
            sleep(random.randint(2, 7))


def migrate_chapters_and_videomarkers():
    pubmedias: set[str, int] = set(map(lambda x: (x.parent.parent.locale, x.parent.booknum),
                        old_session.query(oSentVerse)))
    for i, pubmedia in enumerate(sorted(pubmedias), 1):
        if fetch.need_chapter_and_videomarks((book := get.book(pubmedia[0].replace('_', '-'), pubmedia[1]))):
            fetch.chapters_and_videomarkers(book)
            s = random.randint(1, 2)
            logger.info(f'{i}/{len(pubmedias)} - Sleeping for {s} seconds')
            sleep(s)



def migrate_files():
    def map_file(language_code: str, booknum: int, sent_verses: Iterator[oSentVerse]):
        p = BiblePassage.from_num(language_code, booknum)
        for sent_verse in sent_verses:
            p.chapternumber = sent_verse.chapter
            p.verses = sent_verse.raw_verses.split()
            yield dict(
                id=sent_verse.id,
                chapter_id=p.chapter.id,
                telegram_file_id=sent_verse.telegram_file_id,
                telegram_file_unique_id=None,
                path=None,
                size=None if sent_verse.id <= 1184 else sent_verse.size,
                duration=round(sum(parse_time(vm.duration) for vm in vms)) \
                    if all(vms := [p.chapter.get_videomarker(v) for v in p.verses]) \
                    else 0,
                citation=p.citation,
                raw_verses=p.raw_verses,
                count_verses=len(p.verses),
                added_datetime=datetime.fromisoformat(sent_verse.added_datetime).astimezone(pytz.UTC).replace(tzinfo=None),
                overlay_language_code=None,
                is_deprecated=0 if sent_verse.checksum == p.chapter.checksum else 1,
            )

    pubmedias: set[str, int] = set(map(lambda x: (x.parent.parent.locale, x.parent.booknum),
                        old_session.query(oSentVerse).order_by(oSentVerse.id.desc())
                        ))
    for i, pubmedia in enumerate(pubmedias, 1):
        logger.info(f'{i} - {pubmedia}')
        sent_verses: Iterator[oSentVerse] = old_session.query(oSentVerse) \
            .join(oBibleBook, oBibleBook.id == oSentVerse.bible_book_id) \
            .join(oLanguage, oLanguage.id == oBibleBook.sign_language_id) \
            .where(oLanguage.locale == pubmedia[0],
                   oBibleBook.booknum == pubmedia[1]) \
            .order_by(oSentVerse.id.asc())

        session.bulk_insert_mappings(File, map_file(pubmedia[0].replace('_', '-'), pubmedia[1], sent_verses))
        session.commit()

def fix_duration_files():
    files: Iterator[File] = session.query(File).filter(File.duration == 0)
    for file in files:
        o = old_session.query(oBibleChapter).filter(oBibleChapter.checksum == file.chapter.checksum).one_or_none()
        if not o:
            logger.warning(f'{file.citation} not found in old session')
            continue
        session.bulk_insert_mappings(VideoMarker, (dict(
            chapter_id=file.chapter_id,
            verse_id=select(Bible.id).where(Bible.book==file.book.number,
                                            Bible.chapter==file.chapter.number,
                                            Bible.verse==ovm.versenum).scalar(),
            versenum=ovm.versenum,
            label=ovm.label,
            duration=ovm.duration,
            start_time=ovm.start_time,
            end_transition_duration=ovm.end_transition_duration,
        ) for ovm in o.video_markers))
        session.commit()

    files: Iterator[File] = session.query(File).filter(File.duration == 0)
    for file in files:
        file.duration = round(sum(parse_time(vm.duration) for vm in vms)) \
                    if all(vms := [file.chapter.get_videomarker(int(v)) for v in file.raw_verses.split()]) \
                    else 0
        session.commit()


def migrate_files2users():
    session.bulk_insert_mappings(File2User, (dict(
        id=o.id,
        file_id=o.sent_verse_id,
        user_id=o.user_id,
        datetime=datetime.fromisoformat(o.datetime).astimezone(pytz.UTC).replace(tzinfo=None),
    ) for o in old_session.query(oSentVerseUser))
    )
    session.commit()




if __name__ == '__main__':
    # fetch.languages()
    # fetch.editions()
    # migrate_users()
    # migrate_books()
    # migrate_chapters_and_videomarkers()
    # migrate_files()
    # migrate_files2users()
    # fix_duration_files()
    pass
