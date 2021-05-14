import re
from typing import Any, List

from unidecode import unidecode


class BooknumNotFound(Exception):
    pass

class MultipleBooknumsFound(Exception):
    def __init__(self, maybe_booknums):
        self.booknums = maybe_booknums


BIBLE_BOOKALIAS_NUM = {
    'gen': 1,
    'ex': 2,
    'lev': 3,
    'num': 4,
    'deut': 5,
    'jos': 6,
    'juec': 7,
    'rut': 8,
    '1sam': 9,
    '2sam': 10,
    '1rey': 11,
    '2rey': 12,
    '1cron': 13,
    '2cron': 14,
    'esd': 15,
    'neh': 16,
    'est': 17,
    'job': 18,
    'sal': 19,
    'prov': 20,
    'ecl': 21,
    'cant': 22,
    'is': 23,
    'jer': 24,
    'lam': 25,
    'ezeq': 26,
    'dan': 27,
    'os': 28,
    'joel': 29,
    'amos': 30,
    'abd': 31,
    'jon': 32,
    'miq': 33,
    'nah': 34,
    'hab': 35,
    'sof': 36,
    'ageo': 37,
    'zac': 38,
    'mal': 39,
    'mat': 40,
    'mar': 41,
    'luc': 42,
    'juan': 43,
    'hech': 44,
    'rom': 45,
    '1cor': 46,
    '2cor': 47,
    'gal': 48,
    'efes': 49,
    'filip': 50,
    'col': 51,
    '1tes': 52,
    '2tes': 53,
    '1tim': 54,
    '2tim': 55,
    'tito': 56,
    'filem': 57,
    'heb': 58,
    'sant': 59,
    '1ped': 60,
    '2ped': 61,
    '1juan': 62,
    '2juan': 63,
    '3juan': 64,
    'jud': 65,
    'apoc': 66,
}
BIBLE_NUM_BOOKALIAS = {v: k for k, v in BIBLE_BOOKALIAS_NUM.items()}


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


BIBLE_BOOKNAMES = (
    'Génesis',
    'Éxodo',
    'Levítico',
    'Números',
    'Deuteronomio',
    'Josué',
    'Jueces',
    'Rut',
    '1 Samuel',
    '2 Samuel',
    '1 Reyes',
    '2 Reyes',
    '1 Crónicas',
    '2 Crónicas',
    'Esdras',
    'Nehemías',
    'Ester',
    'Job',
    'Salmos',
    'Proverbios',
    'Eclesiastés',
    'El Cantar de los Cantares',
    'Isaías',
    'Jeremías',
    'Lamentaciones',
    'Ezequiel',
    'Daniel',
    'Oseas',
    'Joel',
    'Amós',
    'Abdías',
    'Jonás',
    'Miqueas',
    'Nahúm',
    'Habacuc',
    'Sofonías',
    'Ageo',
    'Zacarías',
    'Malaquías',
    'Mateo',
    'Marcos',
    'Lucas',
    'Juan',
    'Hechos',
    'Romanos',
    '1 Corintios',
    '2 Corintios',
    'Gálatas',
    'Efesios',
    'Filipenses',
    'Colosenses',
    '1 Tesalonicenses',
    '2 Tesalonicenses',
    '1 Timoteo',
    '2 Timoteo',
    'Tito',
    'Filemón',
    'Hebreos',
    'Santiago',
    '1 Pedro',
    '2 Pedro',
    '1 Juan',
    '2 Juan',
    '3 Juan',
    'Judas',
    'Apocalipsis',
)
dict_booknames = {
    **BIBLE_BOOKALIAS_NUM,
    **{bookname.lower(): booknum for booknum, bookname in enumerate(BIBLE_BOOKNAMES, 1)},
    **{unidecode(bookname.lower()): booknum for booknum, bookname in enumerate(BIBLE_BOOKNAMES, 1)
        if bookname != unidecode(bookname)},
}
def safechars(text):
    return ''.join([x if (x.isalnum() or x in "._-﹕,() ") else '_' for x in text.replace(':', '﹕')])

#BIBLE_PATTERN = fr"^({'|'.join(BIBLE_BOOKALIAS_NUM.keys())}) *(\d+)? *:? *(\d+(?:(?: *, *| +|-)\d+)*)? *$"
#BIBLE_PATTERN = fr"^/?({'|'.join(dict_booknames)}) *(\d+)? *:? *(\d+(?:(?: *, *| +|-)\d+)*)? *$"
#BIBLE_PATTERN = fr"^/?(.*?) *(\d+)? *:? *(\d+(?:(?: *, *| +|-)\d+)*)?$"
BIBLE_PATTERN = fr"^/?(.*?) *(\d+) *:? *(\d+(?:(?: *, *| +|-)\d+)*)?$"


def parse_bible_pattern(text):
    return parse_bookname(text), parse_chapter(text), parse_verses(text)


def parse_bookname(text) -> str:
    if isinstance(text, str):
        text = text.lower()
        match = re.match(BIBLE_PATTERN, text)
    elif isinstance(text, re.Match):
        match = text
    elif text is None:
        raise BooknumNotFound('No hay')

    maybe_bookname = match.group(1) if match else text
    if not maybe_bookname:
        raise BooknumNotFound
    booknum = dict_booknames.get(maybe_bookname)
    if booknum:
        return str(booknum)
    else:
        maybe_booknum = (
            {booknum for bookname, booknum in dict_booknames.items() if bookname.startswith(maybe_bookname)}
            or {booknum for bookname, booknum in dict_booknames.items() if maybe_bookname in bookname}
        )
        if len(maybe_booknum) == 1:
            return str(list(maybe_booknum)[0])
        elif len(maybe_booknum) > 1:
            raise MultipleBooknumsFound([str(bkn) for bkn in sorted(maybe_booknum)])
        else:
            raise BooknumNotFound('No hay')


def parse_chapter(text) -> str:
    if isinstance(text, str):
        match = re.match(BIBLE_PATTERN, text.lower())
    elif isinstance(text, re.Match):
        match = text
    elif text is None:
        return ''
    if match:
        return str(int(match.group(2))) if match.group(2) else ''
    else:
        return ''


def parse_verses(text) -> List[str]:
    if isinstance(text, str):
        match = re.match(BIBLE_PATTERN, text.lower())
    elif isinstance(text, re.Match):
        match = text
    elif text is None:
        return []
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


def seems_bible(text):
    match = re.match(BIBLE_PATTERN, text.lower())
    try:
        booknum = parse_bookname(match)
    except (MultipleBooknumsFound, BooknumNotFound):
        booknum = None
    finally:
        chapter = parse_chapter(match)
        verses = parse_verses(match)
    return any([booknum, chapter, verses])