from datetime import timedelta, datetime

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.inspection import inspect

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



def count(table, *filters) -> int:
    pk = inspect(table).primary_key[0]
    q = session.query(func.count(pk))
    for flt in filters:
        q = q.filter(eval(flt))
    return q.scalar()

def count_signlanguage() -> int:
    return session.query(Language.code).filter(Language.is_sign_language == True).scalar()

def sum_duration() -> str:
    """Duration in 'x days, HH:MM:SS of all File"""    
    return str(timedelta(seconds=round(session.query(func.sum(File.duration)).scalar())))

def sum_duration_sent() -> str:
    """Duration in 'x days, HH:MM:SS of all File2User"""    
    return str(timedelta(seconds=round(
        session.query(func.sum(File.duration)) \
            .select_from(File2User) \
            .join(File, File.id == File2User.file_id) \
            .scalar()
        )))

def sum_size_sent() -> int:
    """Size in MB of all File2User"""  
    return round(
        session.query(func.sum(File.size)) \
            .select_from(File2User) \
            .join(File, File.id == File2User.file_id) \
            .scalar() / 1024 / 1024
            )

def count_active_users() -> int:
    return session.query(func.count(User.id)) \
        .where(User.last_active_datetime > datetime.now() - timedelta(days=30)) \
        .scalar()

def sum_size() -> int:
    """Size in MB of all File"""
    return round(session.query(func.sum(File.size)).scalar() / 1024 / 1024)

def stats_user(user_id: int) -> list[tuple[str, int]]:
    return session.query(Language.code, func.sum(File.count_verses)) \
        .select_from(File) \
        .join(Chapter, Chapter.id == File.chapter_id) \
        .join(Book, Book.id == Chapter.book_id) \
        .join(Edition, Edition.id == Book.edition_id) \
        .join(Language, Language.code == Edition.language_code) \
        .where(File.id.in_(select(File2User.file_id).filter(File2User.user_id == user_id).distinct())) \
        .group_by(Language.code) \
        .all()

def duration_size(user_id: int) -> tuple[int, int]:
    result = session.query(func.sum(File.duration), func.sum(File.size)) \
        .select_from(File2User) \
        .join(File, File2User.file_id == File.id) \
        .where(File2User.user_id == user_id) \
        .one()
    return round(result[0] / 60), round(result[1] / 1024 /1024)

    
if __name__ == '__main__':
    telegram_user_id = 58736295
    # print(duration_size(telegram_user_id))
    data = stats_user(telegram_user_id)
    total = sum(map(lambda x: x[1], data))
    print(total, '\n'.join([f'{code} - {count}' for code, count in data]))

    print(f'{count(Language)=}')
    print(f'{count(Language.code, "Language.is_sign_language == True")=}')
    print('end')
