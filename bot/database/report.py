from sqlalchemy import func

from bot import get_logger
from bot.database import SESSION
from bot.database.schemedb import Language
from bot.database.schemedb import BibleBook
from bot.database.schemedb import BibleChapter
from bot.database.schemedb import VideoMarker
from bot.database.schemedb import SentVerse
from bot.database.schemedb import SentVerseUser
from bot.database.schemedb import User


logger = get_logger(__name__)



def _count(primary_key) -> int:
    return SESSION.query(func.count(primary_key))

def count_sentverse() -> int:
    return _count(SentVerse.id).scalar()

def count_videomarker() -> int:
    return _count(VideoMarker.id).scalar()

def count_biblechapter() -> int:
    return _count(BibleChapter.id).scalar()

def count_biblebook() -> int:
    return _count(BibleBook.id).scalar()

def count_signlanguage() -> int:
    return _count(Language.id).filter(Language.is_sign_lang == True).scalar()

def count_languages() -> int:
    return _count(Language.id).scalar()

def count_sentverseuser() -> int:
    return _count(SentVerseUser.id).scalar()

def count_user() -> int:
    return _count(User.id).scalar()

def count_user_blocked() -> int:
    return _count(User.id).filter(User.status == -1).scalar()

def count_user_brother() -> int:
    return _count(User.id).filter(User.status == 1).scalar()

def count_user_waiting() -> int:
    return _count(User.id).filter(User.status == 0).scalar()

