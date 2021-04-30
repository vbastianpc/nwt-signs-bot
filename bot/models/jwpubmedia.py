from pathlib import Path
import requests
import logging
import re
from typing import List


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


URL_PUBMEDIA = (
    'https://pubmedia.jw-api.org/GETPUBMEDIALINKS?output=json&'
    'alllangs=0&langwritten={lang}&txtCMSLang={lang}&'
    'pub=nwt&booknum={booknum}'
)


class LazyProperty:
    """Para que LazyProperty pueda cachear en memoria el resultado, y no calcularlo cada vez,
    debe ser un descriptor non-data. Implementar solo __get__, no __set__ ni __delete__"""
    def __init__(self, function):
        self.function = function
        self.name = function.__name__

    def __get__(self, obj, type=None) -> object:
        obj.__dict__[self.name] = self.function(obj)
        return obj.__dict__[self.name]


class JWPubMedia:
    def __init__(self,
                 lang: str,
                 booknum: str = None,
                 chapter: str = None,
                 verses: List[str] = [],
                 quality: str = None,
                 ):
        self.lang = lang
        self.booknum = booknum
        self.chapter = chapter
        self.verses = verses
        self.quality = quality
    
    @LazyProperty
    def data(self):
        url = URL_PUBMEDIA.format(lang=self.lang, booknum=self.booknum)
        return requests.get(url).json()
    
    def _match(self):
        "match self.booknum self.chapter self.quality"
        for item in self._items():
            if (item['label'] == self.quality and
                self.chapter_from_url(item['file']['url']) == self.chapter):
                return item
        raise Exception(f'No hay coincidencias')

    @property
    def video_url(self):
        return self._match()['file']['url']

    @property
    def filesize(self):
        return self._match()['filesize']

    def chapter_from_url(self, url):
        " returns '1' if url= '/.../nwt_40_Mt_SCH_01_r240P.mp4'"
        try:
            return str(int(Path(url).name.split('_')[4]))
        except (IndexError, ValueError):
            return None
    
    @property
    def match_markers(self):
        # Los marcadores no están guardados en todas las calidades.
        for item in self._items():
            if (item['markers'] and
                self.chapter_from_url(item['file']['url']) == self.chapter):
                return [
                    marker for verse in self.verses for marker in item['markers']['markers']
                    if int(verse) == marker['verseNumber']
                ] # Se guardan en el mismo orden que self.verses

    def match_marker(self, verseNumber):
        for marker in self.markers():
            if marker['verseNumber'] == int(verseNumber):
                return marker
        raise Exception('Verse label not found')

    def verse_name(self, verseNumber):
        return self.match_marker(verseNumber)['label']

    @property
    def bookname(self):
        return self.data['pubName']
    
    def markers(self, chapter=None):
        chapter = chapter or self.chapter
        for item in self._items():
            if (item['markers'] and
                self.chapter_from_url(item['file']['url']) == chapter):
                return item['markers']['markers']
    
    def not_available_verses(self):
        return [
            verse for verse in self.verses
            if verse not in self.available_verses()
        ]

    def _items(self):
        for files in self.data['files'][self.lang].values():
            for item in files:
                yield item

    def available_chapters(self):
        chapters = set()
        for item in self._items():
            chapters.update([self.chapter_from_url(item['file']['url'])])
        return sorted(filter(None, chapters), key=lambda x: int(x))
    
    def available_verses(self, chapter=None):
        return [str(marker['verseNumber']) for marker in self.markers(chapter)]

    @staticmethod
    def get_signs_languages():
        url = 'https://data.jw-api.org/mediator/v1/languages/S/web'
        data = requests.get(url).json()
        return {lang['code']: remove_html_tags(
            lang['name']) for lang in data['languages'] if lang['isSignLanguage']}

    def get_qualities(self):
        qualities = set()
        for item in self._items():
            qualities.update([item['label']])
        return sorted(qualities)
    
    @property
    def pretty_name(self):
        """low level function for named concatenated verses
        si booknum=55 chapter=3 verses=[1, 2, 3, 4, 5, 9]
        devuelve 2 Timoteo 3:1-5, 9
        raise ValueError si self.verses es vacío
        """
        if not self.verses:
            raise ValueError('Primero define self.verses')
        verses = self.verses
        pv = verses[0]
        last = verses[0]
        sep = ', '
        for i in range(1, len(self.verses) - 1):
            if int(verses[i]) - 1 == int(verses[i - 1]) and int(verses[i]) + 1 == int(verses[i + 1]):
                temp = ''
                sep = '-'
            elif int(verses[i]) - 1 == int(verses[i - 1]) and not int(verses[i]) + 1 == int(verses[i + 1]):
                temp = f'{sep}{int(verses[i])}, {int(verses[i+1])}'
                last = verses[i+1]
            else:
                sep = ', '
                if last == verses[i]:
                    temp = ''
                else:
                    temp = f'{sep}{verses[i]}'
            pv += temp
        if last != verses[-1]:
            pv += f'{sep}{verses[-1]}'
        return f'{self.bookname} {self.chapter}:{pv}'


def remove_html_tags(text): return re.compile(r'<[^>]+>').sub('', text).strip()

if __name__ == '__main__':
    jw = JWPubMedia('SCH', booknum='1')
    print(jw.get_qualities())