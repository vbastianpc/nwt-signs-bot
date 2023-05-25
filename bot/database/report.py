from sqlalchemy import func
from sqlalchemy import select

from bot.logs import get_logger
from bot.database import session
from bot.database.schema import Language
from bot.database.schema import Bible
from bot.database.schema import Book
from bot.database.schema import Edition
from bot.database.schema import Chapter
from bot.database.schema import VideoMarker
from bot.database.schema import File
from bot.database.schema import File2User
from bot.database.schema import User


logger = get_logger(__name__)



def _count(primary_key) -> int:
    return session.query(func.count(primary_key))

def count_sentverse() -> int:
    return _count(File.id).scalar()

def count_videomarker() -> int:
    return _count(VideoMarker.id).scalar()

def count_biblechapter() -> int:
    return _count(Chapter.id).scalar()

def count_biblebook() -> int:
    return _count(Book.id).scalar()

def count_bible_editions() -> int:
    return _count(Bible.id).scalar()

def count_signlanguage() -> int:
    return _count(Language.id).filter(Language.is_sign_language == True).scalar()

def count_languages() -> int:
    return _count(Language.id).scalar()

def count_sentverseuser() -> int:
    return _count(File2User.id).scalar()

def count_user() -> int:
    return _count(User.id).scalar()

def count_user_blocked() -> int:
    return _count(User.id).filter(User.status == -1).scalar()

def count_user_brother() -> int:
    return _count(User.id).filter(User.status == 1).scalar()

def count_user_waiting() -> int:
    return _count(User.id).filter(User.status == 0).scalar()

def stats_user(telegram_user_id: int) -> list[tuple[str, int]]:
    result = session.query(Language.code, func.sum(File.count_verses)) \
        .select_from(File2User) \
        .join(User, User.id == File2User.user_id) \
        .join(Chapter, Chapter.id == File.chapter_id) \
        .join(Book, Book.id == Chapter.book_id) \
        .join(Edition, Edition.id == Book.edition_id) \
        .join(Language, Language.id == Edition.language_id) \
        .join(File, File2User.file_id == File.id) \
        .where(User.telegram_user_id == telegram_user_id) \
        .group_by(Language.code) \
        .all()
    return result

    
if __name__ == '__main__':
    telegram_user_id = 58736295
    print(stats_user(telegram_user_id))
    print('end')