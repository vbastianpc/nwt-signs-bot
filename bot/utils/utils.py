import requests.exceptions
from typing import Any
from datetime import datetime
import pytz
from bot.database import get

from bot.utils.browser import LazyBrowser


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


def dt_now() -> datetime:
    tzinfo = pytz.timezone('UTC')
    return tzinfo.localize(datetime.now()).astimezone(tz=pytz.timezone('America/Santiago'))

def now() -> str:
    return dt_now().isoformat(sep=' ', timespec="seconds")

def how_to_say(this_language_code: str, in_this_language_code: str) -> str:
    try:
        data = LazyBrowser().open(f'https://www.jw.org/{in_this_language_code}/languages/').json()
        return list(map(lambda x: x['name'], filter(lambda x: x['symbol'] == this_language_code, data['languages'])))[0]
    except requests.exceptions.JSONDecodeError:
        return get.language(code=this_language_code).name