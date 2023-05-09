import re
from typing import List, Optional, Tuple

from bot.logs import get_logger
from bot.booknames.booknames import search_bookname
from bot.database.schema import Book


logger = get_logger(__name__)


BIBLE_PATTERN = fr"^(.*?) *(\d+)? *:? *(\d+(?:[ \-,\d]+)*)?$"
# BIBLE_PATTERN= r"([\w ]*?) *(?:(\d+) *:)? *(\d+(?:[ \-,\d]+)*)"
BIBLE_PATTERN = r'([123]?)((?: ?[^\d\W]+ ?)+) ?(?:(\d+) *:)?([ ,\d-]+)*'


class BooknumNotFound(Exception):
    pass


class BibleCitationNotFound(Exception):
    pass


def parse_bible_citation(text: str, prefer_language_code=None) -> Tuple[Book, Optional[int], List[Optional[int]]]:
    match = re.match(BIBLE_PATTERN, text)
    try:
        likely_bookname = match.group(1) + match.group(2)
        likely_chapter = match.group(3)
        likely_verses = match.group(4)
    except AttributeError:
        raise BibleCitationNotFound

    try:
        book = search_bookname(likely_bookname, prefer_language_code)
    except:
        if not likely_chapter:
            raise BibleCitationNotFound
        raise BooknumNotFound

    chapter = int(likely_chapter) if likely_chapter else None

    verses = []
    groups = [i.replace(' ', '').split() for i in likely_verses.split(',')] if likely_verses else []
    groups = [i for group in groups for i in group]
    for group in groups:
        if '-' in group:
            verses += [verse for verse in range(int(group.split('-')[0]), int(group.split('-')[1]) + 1)]
        else:
            verses.append(int(group))

    if book.number in [57, 63, 64, 65] and verses and not chapter:
        chapter = 1
    elif book.number not in [57, 63, 64, 65] and len(verses) == 1 and not chapter:
        chapter = verses[0]
        verses = []
    return book, chapter, verses
