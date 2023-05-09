from datetime import datetime
import json

import pytest
from telegram import Bot

from bot.secret import ADMIN
from bot.secret import TOKEN
from bot.utils import video, dt_now
from bot.database import SESSION
from bot.database.schemedb import Language
from bot.database.schemedb import Bible
from bot.database.schemedb import Book
from bot.database.schemedb import Chapter
from bot.database.schemedb import VideoMarker
from bot.database.schemedb import File
from bot.database.schemedb import File2User
from bot.database.schemedb import User
from bot.database import localdatabase as db
from bot.jw.bible import BaseBible
from bot.jw.language import JWLanguage
from bot.jw.pubmedia import SignsBible


@pytest.fixture
def español() -> Language:
    return db.get_language(code='S')

@pytest.fixture
def señas_chilena() -> Language:
    return db.get_language(code='SCH')

@pytest.fixture
def ingles() -> Language:
    return db.get_language(code='E')

@pytest.fixture
def señas_americanas() -> Language:
    return db.get_language(code='ASL')


@pytest.fixture
def jw_bible(señas_chilena) -> SignsBible:
    return SignsBible(señas_chilena.code, booknum=19, chapternum=1, verses=[2])


@pytest.fixture
def book(español, jw_bible) -> Book:
    return db.get_book(español, jw_bible.booknum)

@pytest.fixture
def db_user() -> User:
    return db.get_user(ADMIN)


def test_languages():
    if not db.get_language(code='S'):
        print('No languages in db. Adding all languages')
        db.fetch_languages()
    assert db.get_language(code='S').code == 'es'

def test_books(español):
    assert db.get_book(español, 1).name == 'Génesis'
    assert len(db.get_books(español.id)) == 66

def test_jw(jw_bible):
    jw = jw_bible
    db.manage_video_markers(jw)
    assert db.get_chapter(jw)

def test_user(español, señas_chilena):
    user = db.get_user(ADMIN) or db.set_user(ADMIN, sign_language_code=señas_chilena.code, full_name='Bastian Palavecino', bot_language=español, status=User.AUTHORIZED, added_datetime=dt_now())
    assert user.telegram_user_id == ADMIN
