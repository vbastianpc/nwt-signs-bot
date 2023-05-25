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
    return ''.join([x if (x.isalnum() or x in "._-,() ") else '_' for x in text.replace(':', '.')])


def dt_now(naive: bool = False) -> datetime:
    """Server datetime.now()"""
    tzinfo = pytz.timezone('UTC')
    dt = tzinfo.localize(datetime.now()).astimezone(tz=pytz.timezone('America/Santiago'))
    if naive is False:
        return dt.astimezone(tz=pytz.timezone('America/Santiago')) # server datetime but shown as America/Santiago
    else:
        return dt.replace(tzinfo=None)

def now() -> str:
    return dt_now().isoformat(sep=' ', timespec="seconds")

def how_to_say(this_language_code: str, in_this_language_code: str) -> str:
    try:
        data = browser.open(f'https://www.jw.org/{in_this_language_code}/languages').json()
        return list(filter(lambda x: x['symbol'] == this_language_code, data['languages']))[0]['name']
    except:
        logger.warning(f"Can't get how to say this language {this_language_code!r} "
                       f"in this language {in_this_language_code!r}")
        return get.language(code=this_language_code).name
