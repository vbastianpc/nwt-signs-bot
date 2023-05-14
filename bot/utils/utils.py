from typing import Any
from datetime import datetime
import pytz


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

def represent(instance, **kwargs):
    s = ', '.join([f'{kw}={arg!r}' for kw, arg in kwargs.items()])
    return f'{type(instance).__name__}({s})'
    