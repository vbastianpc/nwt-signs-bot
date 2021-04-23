import re
from typing import Any, List


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
    '1 Timioteo',
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

BIBLE_PATTERN = fr"^({'|'.join(BIBLE_BOOKALIAS_NUM.keys())}) *(\d+)? *:? *(\d+(?:(?: *, *| +|-)\d+)*)? *$"

def parse_bible_pattern(text):
    match = re.match(BIBLE_PATTERN, text.lower())
    if not match:
        return None, None, None, None
    book_alias = match.group(1)
    booknum = str(BIBLE_BOOKALIAS_NUM[book_alias])
    chapter = str(int(match.group(2))) if match.group(2) else None
    verses = []
    groups = [i.split() for i in match.group(3).split(',')] if match.group(3) else []
    groups = [i for group in groups for i in group]
    for group in groups:
        if '-' in group:
            verses += [str(verse) for verse in range(int(group.split('-')[0]), int(group.split('-')[1]) + 1)]
        else:
            verses.append(group)
    return book_alias, booknum, chapter, verses

