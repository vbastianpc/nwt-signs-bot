from typing import Optional, Union, List

from bot.jw.language import JWLanguage
from bot.jw import SHARE_URL


class BaseBible:
    def __init__(
            self,
            language: Optional[Union[JWLanguage, str]] = None,
            booknum: Optional[int] = None,
            chapter: Optional[int] = None,
            verses: Union[int, str, List[str], List[int]] = [],
            **kwargs):
        self.booknum = booknum
        self.chapter = chapter
        self.verses = verses
        self.lang = language
        
    @property
    def booknum(self) -> Optional[int]:
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
    def chapter(self) -> Optional[int]:
        return self._chapter
    
    @chapter.setter
    def chapter(self, value):
        if isinstance(value, (str, int)):
            self._chapter = int(value)
        else:
            self._chapter = None

    @property
    def verses(self) -> Optional[List[int]]:
        return self._verses
    
    @verses.setter
    def verses(self, value):
        if isinstance(value, list):
            self._verses = [int(verse) for verse in value]
        elif isinstance(value, (int, str)):
            self._verses = [int(value)]
        elif value is None:
            self._verses = []
        else:
            raise TypeError(f'verses must be a list, a string or an integer, not {type(value).__name__}')
    
    @property
    def lang(self) -> Optional[JWLanguage]:
        return self._lang
    
    @lang.setter
    def lang(self, value) -> None:
        if isinstance(value, str):
            self._lang = JWLanguage(value)
        elif isinstance(value, JWLanguage):
            self._lang = value
        elif value is None:
            self._lang = None
        else:
            raise ValueError(f'language value {value!r} is not valid arg')


    def citation(self, bookname=None, chapter=None, verses=None) -> str:
        """low level function for citation verses
        chapter=3 verses=[1, 2, 3, 5, 6]
        3:1-3, 5, 6
        """
        chapter = chapter if isinstance(chapter, (int, str)) else self.chapter
        verses = (self.__class__(verses=verses).verses or self.verses)
        assert all([chapter, verses]), f'Debes definir chapter, verses  -->  ({self})'
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
        return f'{bookname} {chapter}:{pv}' if bookname else f'{chapter}:{pv}'
    
    def share_url(self, verse=None, is_sign_language=True):
        assert not None in [self.lang, self.booknum, self.chapter]
        return SHARE_URL(
            self.lang.code,
            self.booknum,
            self.chapter,
            verse if verse else self.verses[0] if self.verses else 0,
            0 if verse else self.verses[-1] if self.verses else 0,
            is_sign_language
        )

    
    def __repr__(self):
        return f'{self.__class__.__name__}(language={self.lang}, booknum={self.booknum}, ' \
            f'chapter={self.chapter}, verses={self.verses})'
