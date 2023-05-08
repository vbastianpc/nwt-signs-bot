import re
from typing import Any, List, Optional
from datetime import datetime
import pytz

from unidecode import unidecode


class BooknumNotFound(Exception):
    pass

class MultipleBooknumsFound(Exception):
    def __init__(self, maybe_booknums):
        self.booknums = maybe_booknums


def list_of_lists(items: List[Any], columns: int) -> List[List[Any]]:
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

#BIBLE_PATTERN = fr"^({'|'.join(BIBLE_BOOKALIAS_NUM.keys())}) *(\d+)? *:? *(\d+(?:(?: *, *| +|-)\d+)*)? *$"
#BIBLE_PATTERN = fr"^/?({'|'.join(dict_booknames)}) *(\d+)? *:? *(\d+(?:(?: *, *| +|-)\d+)*)? *$"
#BIBLE_PATTERN = fr"^/?(.*?) *(\d+)? *:? *(\d+(?:(?: *, *| +|-)\d+)*)?$"
BIBLE_PATTERN = fr"^/?(.*?) *(\d+) *:? *(\d+(?:(?: *, *| +|-)\d+)*)?$"



def parse_chapter(text) -> Optional[int]:
    if isinstance(text, str):
        match = re.match(BIBLE_PATTERN, text.lower())
    elif isinstance(text, re.Match):
        match = text
    elif text is None:
        return None
    if match:
        return int(match.group(2)) if match.group(2) else None
    else:
        return None


def parse_verses(text) -> Optional[List[str]]:
    if isinstance(text, str):
        match = re.match(BIBLE_PATTERN, text.lower())
    elif isinstance(text, re.Match):
        match = text
    elif text is None:
        return None
    verses = []
    if match:
        groups = [i.split() for i in match.group(3).split(',')] if match.group(3) else []
        groups = [i for group in groups for i in group]
        for group in groups:
            if '-' in group:
                verses += [str(verse) for verse in range(int(group.split('-')[0]), int(group.split('-')[1]) + 1)]
            else:
                verses.append(group)
    return verses



def dt_now() -> str:
    tzinfo = pytz.timezone('UTC')
    tzinfo.localize(datetime.now())
    return tzinfo.localize(datetime.now()).astimezone(tz=pytz.timezone('America/Santiago'))

def now() -> str:
    return dt_now().isoformat(sep=' ', timespec="seconds")

def represent(instance, **kwargs):
    s = ', '.join([f'{kw}={arg!r}' for kw, arg in kwargs.items()])
    return f'{type(instance).__name__}({s})'
    