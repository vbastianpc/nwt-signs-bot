import re
from typing import List, Optional, Tuple

from bot import get_logger
from bot.booknames.booknames import search_bookname
from bot.database.schemedb import BookNamesAbbreviation


logger = get_logger(__name__)


BIBLE_PATTERN = fr"^(.*?) *(\d+)? *:? *(\d+(?:[ \-,\d]+)*)?$"


class BooknumNotFound(Exception):
    pass


class BibleCitationNotFound(Exception):
    pass


def parse_bible_citation(text: str, preference_lang_locale=None) -> Tuple[BookNamesAbbreviation, Optional[int], List[Optional[int]]]:
    match = re.match(BIBLE_PATTERN, text)
    likely_bookname = match.group(1)
    likely_chapter = match.group(2)
    likely_verses = match.group(3)
    try:
        book = search_bookname(likely_bookname, preference_lang_locale)
    except:
        if not likely_chapter:
            raise BibleCitationNotFound
        else:
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

    return book, chapter, verses

