from pathlib import Path
import requests
import logging
import re
from typing import List, Dict
import json

import mechanicalsoup


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
# https://wol.jw.org/wol/vidlink/r377/lp-sch?pub=nwt&langwritten=SCH&booknum=4&track=30&txtCMSLang=SCH&fileformat=mp4%2Cm4v&output=json
# https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS?track=30&output=json&alllangs=0&langwritten=SCH&pub=nwt&booknum=4

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
    
    @property
    def title_chapter(self):
        return self._match()['title']

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
        raise Exception('Verse number not found')

    def verse_name(self, verseNumber):
        return self.match_marker(verseNumber)['label']

    @property
    def bookname(self):
        return self.data['pubName']
    
    def markers(self) -> List[Dict]:
        mks = []
        for item in self._items():
            if (item['markers'] and
                self.chapter_from_url(item['file']['url']) == self.chapter):
                mks = item['markers']['markers']
                break
        verses = [m['verseNumber'] for m in mks]
        missings_markers = [marker for marker in self.alternate_markers if marker['verseNumber'] not in verses]
        return sorted(mks + missings_markers, key=lambda x: x['verseNumber'])

    @LazyProperty
    def alternate_markers(self) -> List[Dict]:
        return scrap_wol_markers(self.lang, self.booknum, self.chapter, self.bookname)

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
        return [str(marker['verseNumber']) for marker in self.markers()]

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

    def check_quality(self):
        return self.quality in self.get_qualities()
    
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


def scrap_wol_markers(lang, booknum, chapter, bookname):
    url = f'https://wol.jw.org/wol/finder?wtlocale={lang}'
    agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
    browser = mechanicalsoup.StatefulBrowser(user_agent=agent)
    browser.open(url)
    locale, _, _, rsconf, lib = browser.get_url().split('/')[-5:]
    browser.open(f'https://wol.jw.org/{locale}/wol/b/{rsconf}/{lib}/nwt/{booknum}/{chapter}')
    bare_markers = json.loads(browser.page.find("input", id='videoMarkers').get('data-json-markers'))
    return [{
        'duration': marker['duration'],
        "verseNumber": int(verse),
        "startTime": marker['startTime'],
        "label": f"{bookname} {chapter}:{verse}",
        "endTransitionDuration": 0,
        }
        for verse, marker in sorted(bare_markers.items(), key=lambda x: int(x[0]))
    ]


def remove_html_tags(text): return re.compile(r'<[^>]+>').sub('', text).strip()

if __name__ == '__main__':
    jw = JWPubMedia('SCH', booknum='1')
    print(jw.get_qualities())