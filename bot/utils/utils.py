from typing import Any
from datetime import datetime

import pytz

from bot.database import get
from bot.utils.browser import browser
from bot.logs import get_logger


logger = get_logger(__name__)


def list_of_lists(items: list[Any], columns: int) -> list[list[Any]]:
    start = 0
    end = columns if columns < len(items) else len(items)
    new = []
    while True:
        new.append(items[start:end])
        start += columns
        end += columns
        if start >= len(items):
            break
        if end >= len(items):
            new.append(items[start:])
            break
    return new


def safechars(text):
    return ''.join([x if (x.isalnum() or x in "._-+,() ") else '_' for x in text.replace(':', '.')])


def strike(text: str | int) -> str:
    result = ''
    for c in str(text):
        result += c + '\u0336'
    return result


def dt_now(naive: bool = False, timezone: pytz.tzinfo.BaseTzInfo | str = 'America/Santiago') -> datetime:
    """Real datetime.now(), location independent"""
    now = datetime.now()
    if isinstance(timezone, pytz.tzinfo.BaseTzInfo):
        now = now.astimezone(tz=timezone)
    elif isinstance(timezone, str):
        now = now.astimezone(tz=pytz.timezone(timezone))

    if naive is True:
        now = now.replace(tzinfo=None)
    elif naive is False and not timezone:
        now = now.astimezone()
    return now


def how_to_say(this_language_code: str, in_this_language_code: str) -> str:
    try:
        data = browser.open(f'https://www.jw.org/{in_this_language_code}/languages').json()
        return list(filter(lambda x: x['symbol'] == this_language_code, data['languages']))[0]['name']
    except:
        logger.warning(f"Can't get how to say this language {this_language_code!r} "
                       f"in this language {in_this_language_code!r}")
        return get.language(code=this_language_code).name
