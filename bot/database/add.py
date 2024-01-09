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
        sign_language_code2: str | None = None,
        sign_language_code3: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        user_name: str | None = None,
        is_premium: bool | None = None,
        bot_language_code: str | None = None,
        status: int | None = None,
        with_overlay: bool | None = None,
        last_active_datetime: datetime | None = None,
        delogo: bool | None = None
    ) -> User:
    user = session.query(User).filter(User.telegram_user_id == telegram_user_id).one_or_none()
    if not user:
        logger.info(f'No existe usuario')
        user = User(telegram_user_id=telegram_user_id, added_datetime=dt_now())
        session.add(user)

    if sign_language_code:
        user.sign_language_code = sign_language_code
    if sign_language_code2:
        user.sign_language_code2 = sign_language_code2
    if sign_language_code3:
        user.sign_language_code3 = sign_language_code3
    if first_name:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if user_name:
        user.user_name = user_name
    if is_premium is not None:
        user.is_premium = is_premium
    if bot_language_code:
        user.bot_language_code = bot_language_code
    if with_overlay is False:
        user.overlay_language_code = None
    elif with_overlay is True:
        user.overlay_language_code = user.bot_language.code
    if last_active_datetime:
        user.last_active_datetime = last_active_datetime
    if status is not None:
        user.status = status
    if delogo is not None:
        user.delogo = delogo

    if user.overlay_language_code == user.bot_language_code:
        user.overlay_language_code = None
    session.commit()
    return user

def file(
        chapter_id: int,
        verses: list[int],
        telegram_file_id: str,
        telegram_file_unique_id: str,
        duration: int,
        citation: str,
        file_size: int,
        overlay_language_code: str | None,
        delogo: bool,
    ) -> File:
    f = File(
        chapter_id=chapter_id,
        telegram_file_id=telegram_file_id,
        telegram_file_unique_id=telegram_file_unique_id,
        size=file_size,
        duration=duration,
        citation=citation,
        raw_verses=' '.join(map(str, verses)),
        count_verses=len(verses),
        added_datetime=dt_now(),
        overlay_language_code=overlay_language_code,
        delogo=delogo,
    )
    session.add(f)
    session.commit()
    return f


def file2user(file_id: int, user_id: int) -> None:
    session.add(File2User(file_id=file_id, user_id=user_id, datetime=dt_now()))
    session.commit()