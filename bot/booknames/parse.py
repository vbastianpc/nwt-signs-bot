import re
from typing import Any, List, Optional, Tuple
from pathlib import Path
import time
import logging

from ruamel.yaml import YAML
from unidecode import unidecode


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


BIBLE_PATTERN = fr"^/?(.*?) *(\d+) *:? *(\d+(?:(?: *, *| +|-)\d+)*)?$"


class BooknumNotFound(Exception):
    pass

class MultipleBooknumsFound(Exception):
    def __init__(self, maybe_booknums):
        self.booknums = maybe_booknums


def parse_bible_citation(text: str) -> Tuple[int, Optional[int], List[Optional[int]]]:
    citation = unidecode(text).lower()
    match = re.match(BIBLE_PATTERN, citation)
    try:
        bookname = match.group(1)
    except Exception as e:
        print(e)
        raise e # BooknumNotFound
    else:
        booknum = 'find_booknum'
        if not booknum:
            print('raise algo')
    try:
        chapter = int(match.group(2))
    except Exception as e:
        print(e)
        chapter = None
        raise e # BooknumNotFound
    try:
        verses = []
        groups = [i.split() for i in match.group(3).split(',')]
        groups = [i for group in groups for i in group]
        for group in groups:
            if '-' in group:
                # str verse or int verse
                verses += [str(verse) for verse in range(int(group.split('-')[0]), int(group.split('-')[1]) + 1)]
            else:
                verses.append(group)
    except Exception as e:
        print(e)
        raise e
    
    return booknum, chapter, verses

# TODO nuevo comando para mostrar las abreviaciones de los libros de la biblia
