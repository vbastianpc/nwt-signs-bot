from bot.jw.language import JWLanguage


class BaseBible:
    def __init__(
            self,
            language_meps_symbol: str = None,
            booknum: int | None = None,
            chapternum: int | None = None,
            verses: int | str | list[str] | list[int] = [],
    ):
        self.language_meps_symbol = language_meps_symbol
        self.language = language_meps_symbol
        self.booknum = booknum
        self.chapternum = chapternum
        self.verses = verses

    @property
    def booknum(self) -> int | None:
        return self._booknum

    @booknum.setter
    def booknum(self, value):
        if value is None:
            self._booknum = None
        elif int(value) >= 1 and int(value) <= 66:
            self._booknum = int(value)
        else:
            raise ValueError('booknum must be between 1 and 66')

    @property
    def chapternum(self) -> int | None:
        return self._chapter

    @chapternum.setter
    def chapternum(self, value):
        if isinstance(value, (str, int)):
            self._chapter = int(value)
        else:
            self._chapter = None

    @property
    def verses(self) -> list[int | None]:
        return self._verses

    @verses.setter
    def verses(self, value):
        if isinstance(value, list):
            self._verses = [int(verse) for verse in value]
        elif isinstance(value, int):
            self._verses = [value]
        elif isinstance(value, str):  # it could be '14' or '14 15 18' etc
            self._verses = [int(i) for i in value.split()]
        elif value is None:
            self._verses = []
        else:
            raise TypeError(f'verses must be a list, a string or an integer, not {type(value).__name__}')

    @property
    def raw_verses(self):
        return ' '.join(map(str, self.verses))

    @property
    def language(self) -> JWLanguage:
        return self._language

    @language.setter
    def language(self, language_meps_symbol) -> None:
        self._language = JWLanguage(language_meps_symbol)

    def citation(self, bookname=None, chapternum=None, verses=None) -> str:
        """low level function for citation verses
        chapternum=3 verses=[1, 2, 3, 5, 6]
        3:1-3, 5, 6
        """
        chapternum = chapternum if isinstance(chapternum, (int, str)) else self.chapternum
        verses = (self.__class__(verses=verses).verses or self.verses)
        assert all([chapternum, verses]), f'Debes definir chapternum, verses  -->  ({self})'
        pv = str(verses[0])
        last = verses[0]
        sep = ', '
        for i in range(1, len(verses) - 1):
            if verses[i] - 1 == verses[i - 1] and verses[i] + 1 == verses[i + 1]:
                temp = ''
                sep = '-'
            elif verses[i] - 1 == verses[i - 1] and not verses[i] + 1 == verses[i + 1]:
                temp = f'{sep}{verses[i]}, {verses[i+1]}'
                last = verses[i + 1]
            else:
                sep = ', '
                if last == verses[i]:
                    temp = ''
                else:
                    temp = f'{sep}{verses[i]}'
            pv += temp
        if last != verses[-1]:
            pv += f'{sep}{verses[-1]}'
        return f'{bookname} {chapternum}:{pv}' if bookname else f'{chapternum}:{pv}'

    def share_url(self, verse=None, is_sign_language=True, language_meps_symbol=None):
        assert not None in [self.language_meps_symbol, self.booknum, self.chapternum]
        return (
            language_meps_symbol or self.language_meps_symbol,
            self.booknum,
            self.chapternum,
            verse if verse else self.verses[0] if self.verses else 0,
            0 if verse else self.verses[-1] if self.verses else 0,
            is_sign_language
        )

    def __repr__(self):
        return f'{self.__class__.__name__}(language_meps_symbol={self.language_meps_symbol}, booknum={self.booknum}, ' \
            f'chapternum={self.chapternum}, verses={self.verses})'
