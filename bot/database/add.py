from datetime import datetime

from bot.database import session
from bot.database.schema import Language
from bot.database.schema import User
from bot.database.schema import File
from bot.database.schema import File2User
from bot.database import get
from bot.utils import dt_now
from bot.logs import get_logger


logger = get_logger(__name__)


def or_update_user(
        telegram_user_id: int,
        sign_language_code: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        user_name: str | None = None,
        is_premium: bool | None = None,
        bot_language_code: str | None = None,
        sign_language_name: str = None,
        status: int | None = None,
        with_overlay: bool | None = None,
        added_datetime: datetime | None = None,
        last_active_datetime: datetime | None = None
    ) -> User:
    user = session.query(User).filter(User.telegram_user_id == telegram_user_id).one_or_none()
    if not user:
        logger.info(f'No existe usuario')
        user = User(telegram_user_id=telegram_user_id)
        session.add(user)

    if sign_language_code:
        user.sign_language_id = get.language(code=sign_language_code).id
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    if user_name:
        user.user_name = user_name
    if is_premium is not None:
        user.is_premium = is_premium
    if added_datetime:
        user.added_datetime = added_datetime
    if bot_language_code:
        user.bot_language_id = get.language(code=bot_language_code).id
    if with_overlay is False:
        user.overlay_language_id = None
    elif with_overlay is True:
        user.overlay_language_id = user.bot_language.id
    if sign_language_name:
        user.sign_language_name = sign_language_name
    if last_active_datetime:
        user.last_active_datetime = last_active_datetime
    if status is not None:
        user.status = status
    if (sign_language_code or bot_language_code) and not sign_language_name:
        logger.warning('You must set sign_language_name according to new sign_language_code or new bot_language')
    session.commit()
    return user

def file(
        chapter_id: int,
        verses: list[int],
        telegram_file_id: str,
        telegram_file_unique_id: str,
        duration: int,
        file_name: str,
        file_size: int,
        overlay_language_id: int | None,
    ) -> File:
    f = File(
        chapter_id=chapter_id,
        raw_verses=' '.join(map(str, verses)),
        telegram_file_id=telegram_file_id,
        telegram_file_unique_id=telegram_file_unique_id,
        duration=duration,
        name=file_name,
        size=file_size,
        added_datetime=dt_now(),
        overlay_language_id=overlay_language_id,
        is_single_verse=True if len(verses) == 1 else False
    )
    session.add(f)
    session.commit()
    return f


def file2user(file_id: int, user_id: int) -> None:
    session.add(File2User(file_id=file_id, user_id=user_id, datetime=dt_now()))
    session.commit()