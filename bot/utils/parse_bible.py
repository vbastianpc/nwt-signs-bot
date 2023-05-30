# import re

# from sqlalchemy import select
# from unidecode import unidecode as ud

# from bot.database import get
# from bot.database.schema import Bible
# from bot.database.schema import Book
# from bot import exc
# from bot.logs import get_logger


# logger = get_logger(__name__)


# BIBLE_PATTERN = r'([123]? *(?:[^\d]+)) *(?:(\d*)[ :]+)? *([ ,\d-]*)'
# ONE_CHHAPTER_BOOKS = [31, 57, 63, 64, 65] # Abdías, Filemón, 2 Juan, 3 Juan, Judas

# def human_citation(citation: str, language_code: str) -> tuple[Book, int | None, list[int | None]]:
#     m = re.search(BIBLE_PATTERN, citation)
#     if m is None:
#         raise exc.BibleCitationNotFound
#     book_like = m.group(1)
#     book = search_book(book_like, language_code=language_code)
#     if not book:
#         raise exc.BookNameNotFound(book_like)
#     chapternumber = int(m.group(2)) if m.group(2) else None
#     verses = get_verses(m.group(3))
#     if chapternumber is None and len(verses) == 1 and book.number not in ONE_CHHAPTER_BOOKS:
#         # "Mateo 5" chapternumber = None, verses = [5]
#         chapternumber, verses = verses[0], []
#     elif chapternumber is None and len(verses) > 1 and book.number not in ONE_CHHAPTER_BOOKS:
#         # "Mateo 5, 6, 7" chapternumber = None, verses = [5, 6, 7]
#         raise exc.MissingChapterNumber
#     elif chapternumber is None and book.number in ONE_CHHAPTER_BOOKS:
#         # "Judas 5, 6" chapternumber = None, verses = [5, 6]
#         chapternumber = 1

#     s = select(Bible).where(Bible.book == book.number, Bible.chapter == chapternumber)
#     if not s.exists():
#         raise exc.ChapterNotExists(book.name, chapternumber)
#     elif not s.where(Bible.verse.in_(verses)).exists():
#         raise exc.VerseNotExists(book, chapternumber, verses)

#     if book.edition.language.code != language_code:
#         b = get.book(language_code, book.number)
#         if b:
#             book = b
#         else:
#             logger.warning(f'{book_like!r} found in {book.edition.language.code!r} language, '
#                         f'but it does not match language {language_code!r} requested')
#     return book, chapternumber, verses


# def search_book(book_like: str, language_code: str) -> Book | None:
#     book_like = re.sub(' *', '', book_like).lower()
#     books = get.books(language_code=language_code)
#     for book in books:
#         bn, sa, oa, ssb = map(
#             lambda x: re.sub(' *', '', x).lower(),
#             [book.name, book.standard_abbreviation, book.official_abbreviation, book.standard_singular_bookname]
#         )
#         if any(map(lambda x: x.startswith(book_like), (bn, sa, oa, ssb))) or \
#             any(map(lambda x: ud(x).lower().startswith(ud(book_like)), (bn, sa, oa, ssb))):
#             return book
#     else:
#         if language_code is None:
#             return None
#         else:
#             return search_book(book_like, language_code=None)


# def get_verses(verses_like: int | str | list[int | str] | None) -> list[int | None]:
#     if isinstance(verses_like, int):
#         return [verses_like]
#     elif isinstance(verses_like, str): # it could be '14' or '14 15 18' or '14-18' or '14, 15, 17-20' etc
#         verses = []
#         groups = [i for i in re.sub(' *', '', verses_like).split(',')]
#         for group in groups:
#             if '-' in group:
#                 verses += [verse for verse in range(int(group.split('-')[0]), int(group.split('-')[1]) + 1)]
#             else:
#                 verses.append(int(group))
#         return verses
#     elif isinstance(verses_like, list):
#         return [verse for result in [get_verses(item) for item in verses_like] for verse in result]
#     elif verses_like is None:
#         return []
#     else:
#         raise TypeError(f'verses must be a list, a string or an integer, not {type(verses_like).__name__}')


# def get_verse_citation(verses: list[int | None]) -> str:
#     """Reverse function of 'get_verses'"""
#     if not verses:
#         return ''
#     pv = str(verses[0])
#     last = verses[0]
#     sep = ', '
#     for i in range(1, len(verses) - 1):
#         if verses[i] - 1 == verses[i - 1] and verses[i] + 1 == verses[i + 1]:
#             temp = ''
#             sep = '-'
#         elif verses[i] - 1 == verses[i - 1] and not verses[i] + 1 == verses[i + 1]:
#             temp = f'{sep}{verses[i]}, {verses[i+1]}'
#             last = verses[i + 1]
#         else:
#             sep = ', '
#             if last == verses[i]:
#                 temp = ''
#             else:
#                 temp = f'{sep}{verses[i]}'
#         pv += temp
#     if last != verses[-1]:
#         pv += f'{sep}{verses[-1]}'
#     return pv

# if __name__ == '__main__':
#     # book, chapternum, verses = human_citation('isai 15:4', 'es')
#     # book, chapternum, verses = human_citation('Ê-sai 15:4', 'vi')

#     print('end')