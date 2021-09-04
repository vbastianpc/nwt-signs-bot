from pathlib import Path
import sys
import logging
import re
from typing import List, Dict, Union, Optional
import json
from subprocess import run
import shlex

import mechanicalsoup


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# URL Principal. bookname, chapters, qualities, url videos, markers
URL_PUBMEDIA = 'https://pubmedia.jw-api.org/GETPUBMEDIALINKS?output=json&alllangs=0&langwritten={code_lang}&txtCMSLang={code_lang}&pub=nwt&booknum={booknum}&track={chapter}'

# TODOS los lenguajes de señas (jw y wol), vernacular, name, code_lang
URL_LANGUAGES = 'https://data.jw-api.org/mediator/v1/languages/S/all'

# solo wol: rsconf, locale, lib, iswolavailable, (vernacular, name, code_lang)
URL_LIBRARIES = 'https://wol.jw.org/es/wol/li/r4/lp-s'

# para obtener marcadores
URL_WOLBIBLE = 'https://wol.jw.org/{locale}/wol/b/{rsconf}/{lib}/nwt/{booknum}/{chapter}'


# citas de biblia, solo si hay wol. No se ocupa
URL_CITATION = 'https://wol.jw.org/wol/api/v1/citation/{rsconf}/{lib}/bible/{startBook}/{startChapter}/{startVerse}/{endBook}/{endChapter}/{endVerse}?pub=nwtst'


# https://wol.jw.org/wol/vidlink/r377/lp-sch?pub=nwt&langwritten=SCH&booknum=4&track=30&txtCMSLang=SCH&fileformat=mp4%2Cm4v&output=json
# https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS?track=30&output=json&alllangs=0&langwritten=SCH&pub=nwt&booknum=4

class LazyProperty:
    """Para que LazyProperty pueda cachear en memoria el resultado, y no calcularlo cada vez,
    debe ser un descriptor non-data. Implementar solo __get__, no __set__ ni __delete__
    See https://realpython.com/python-descriptors/#lazy-properties"""
    def __init__(self, function):
        self.function = function
        self.name = function.__name__

    def __get__(self, obj, type=None) -> object:
        if isinstance(obj.__dict__.get('_lazies'), list):
            obj.__dict__['_lazies'].append(self.name)
        else:
            obj.__dict__['_lazies'] = [self.name]
        obj.__dict__[self.name] = self.function(obj)
        return obj.__dict__[self.name]


class SpecialProperty:
    def __set_name__(self, owner, name):
        self.name = name

    def __set__(self, obj, value) -> None:
        logger.info('Seteando %s', self.name)
        if self.name in obj.__dict__ and obj.__dict__[self.name] != value:
            logger.info('Existe el valor y es diferente al ya configurado')
            if '_lazies' in obj.__dict__:
                for lazy in obj.__dict__.get('_lazies') or []:
                    del obj.__dict__[lazy]
                del obj.__dict__['_lazies']
                logger.info('Cache lazies borrada')
        obj.__dict__[self.name] = value


class LazyBrowser(mechanicalsoup.StatefulBrowser):
    def __init__(self):
        agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
        self.last_url = None
        self.response = None
        super().__init__(user_agent=agent)
        
    def open(self, url):
        if self.last_url == url or self.url == url:
            return self.response
        else:
            logger.info(f'Not Lazy :( {self.last_url} {url}')
            self.last_url = url
            self.response = super().open(url)
            return self.response


class classinstancemethod:
    """https://stackoverflow.com/questions/48808788/make-a-method-that-is-both-a-class-method-and-an-instance-method"""
    def __init__(self, method, instance=None, owner=None):
        self.method = method
        self.instance = instance
        self.owner = owner

    def __get__(self, instance, owner=None):
        return type(self)(self.method, instance, owner)

    def __call__(self, *args, **kwargs):
        instance = self.instance
        if instance is None and args:
            instance, args = args[0], args[1:]
        cls = self.owner
        return self.method(cls, instance, *args, **kwargs)


class JWInfo:
    browser = LazyBrowser()

    def __init__(self, code_lang):
        self.code_lang = code_lang

    @classmethod
    def get_signs_languages(cls) -> List[Dict]:
        data = cls.browser.open(URL_LANGUAGES).json()
        langs = []
        sign_languages = (item for item in data['languages'] if item['isSignLanguage'])
        for item in sign_languages:
            langs.append({
                'code': item['code'],               # ASL
                'locale': item['locale'],           # ase
                'vernacular': item['vernacular'],   # American Sign Language
                'name': item['name'],               # lenguaje de señas americano
            })
        return langs

    def is_wol_available(self) -> bool:
        self.browser.open(URL_LIBRARIES)
        if self.browser.page.find('a', {'data-meps-symbol': self.code_lang}):
            return True
        else:
            return False

    def _get_tag_attribute(self, code_lang, attribute_name) -> Optional[str]:
        self.browser.open(URL_LIBRARIES)
        try:
            value = self.browser.page.find('a', {'data-meps-symbol': code_lang}).get(attribute_name)
        except:
            return None
        else:
            return value

    def rsconf(self, code_lang=None) -> Optional[str]:
        return self._get_tag_attribute(code_lang or self.code_lang, 'data-rsconf')
    
    def lib(self, code_lang=None) -> Optional[str]:
        return self._get_tag_attribute(code_lang or self.code_lang, 'data-lib')

    def locale(self, code_lang=None) -> Optional[str]:
        return self._get_tag_attribute(code_lang or self.code_lang, 'data-locale')


class JWBible(JWInfo):
    browser_pubmedia = LazyBrowser()
    browser_wol = LazyBrowser()

    def __init__(self,
                 code_lang: str = None,
                 quality: str = None,
                 booknum: Union[str, int] = None,
                 chapter: Union[str, int] = None,
                 verses: Union[int, str, List[str], List[int]] = [],
                 videopath: Union[Path, str, None] = None,
                 ):
        self.code_lang = code_lang
        self.booknum = booknum
        self.chapter = chapter
        self.verses = verses
        self.quality = quality
        self.videopath = videopath
    
    def __str__(self):
        return f'code_lang={self.code_lang}\tbooknum={self.booknum}\tchapter={self.chapter}\tverses={self.verses}\tquality={self.quality}'
    
    @property
    def booknum(self) -> Optional[int]:
        return self._booknum
    
    @booknum.setter
    def booknum(self, value):
        if hasattr(self, '_booknum') and self._booknum is not None and int(self._booknum) != int(value): # pylint: disable=access-member-before-definition
            self.__dict__.pop('_rawdata', None)
            self.__dict__.pop('_markers', None)
        try:
            self._booknum = int(value)
        except TypeError:
            self._booknum = None

    @property
    def chapter(self) -> Optional[int]:
        return self._chapter
    
    @chapter.setter
    def chapter(self, value):
        if hasattr(self, '_chapter') and self._chapter is not None and int(self._chapter) != int(value): # pylint: disable=access-member-before-definition
            self.__dict__.pop('_markers', None)
        try:
            self._chapter = int(value)
        except TypeError:
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
            self._verses = None
        else:
            raise TypeError(f'verses must be a list, a string or an integer, not {type(value).__name__}')
    
    @property
    def _rawdata(self) -> Dict:
        assert all([self.code_lang, self.booknum]), f'Debes definir code_lang y booknum ({self.code_lang} {self.booknum})'
        url = URL_PUBMEDIA.format(code_lang=self.code_lang, booknum=self.booknum, chapter='')
        r = self.browser_pubmedia.open(url)
        if r.status_code == 200:
            return r.json()
        else:
            return {}

    def _items(self) -> Dict:
        for files in self._rawdata['files'][self.code_lang].values():
            for item in files:
                yield item

    def _match(self) -> Dict:
        assert all([self.quality, self.chapter]), f'Debes definir calidad y capítulo ({self.quality}, {self.chapter})'
        for item in self._items():
            if (item['label'] == self.quality and
                self.chapter_from_url(item['file']['url']) == self.chapter):
                return item
        else:
            raise Exception(f'No hay coincidencias')
    
    def pubmedia_exists(self) -> bool:
        return bool(self._rawdata)
    
    @property
    def bookname(self) -> str:
        return self._rawdata['pubName']
    
    @property
    def video_url(self) -> str:
        return self._match()['file']['url']
    @property
    def title_chapter(self) -> str:
        return self._match()['title']

    @property
    def filesize(self) -> int:
        assert self._match().get('filesize')
        return self._match().get('filesize')
    
    @property
    def checksum(self) -> str:
        assert self._match()['file']['checksum']
        return self._match()['file']['checksum']
    
    @property
    def modifiedDatetime(self) -> str:
        assert self._match()['file']['modifiedDatetime']
        return self._match()['file']['modifiedDatetime']

    @property
    def available_qualities(self) -> List[str]:
        qualities = set()
        for item in self._items():
            qualities.update([item['label']])
        return sorted(qualities)

    def chapter_from_url(self, url) -> Optional[int]:
        " returns '1' if url= '/.../nwt_40_Mt_SCH_01_r240P.mp4'"
        try:
            return int(Path(url).name.split('_')[4])
        except (IndexError, ValueError):
            return None

    @property
    def available_chapters(self) -> List[int]:
        chapters = set()
        for item in self._items():
            chapters.update([self.chapter_from_url(item['file']['url'])])
        return sorted(filter(None, chapters), key=lambda x: int(x))
    
    def match_marker(self, verseNumber) -> Dict:
        for marker in self.markers:
            if marker['verseNumber'] == int(verseNumber):
                return marker
        raise Exception('Verse number not found')

    @LazyProperty
    def markers(self) -> List[Dict]:
        mks = self._wol_markers() or self._ffprobe_markers()
        logger.info('Getting endTransitionDuration from JW-API markers!')
        for marker in mks:
            marker['endTransitionDuration'] = next(
                (jam['endTransitionDuration'] for jam in self._api_markers() if jam['verseNumber'] == marker['verseNumber']),
                marker['endTransitionDuration'],
            )
        return mks

    def _wol_markers(self) -> List[Dict]:
        logger.info('Scrapping WOL markers!')
        url = URL_WOLBIBLE.format(
            locale=self.locale(),
            rsconf=self.rsconf(),
            lib=self.lib(),
            booknum=self.booknum,
            chapter=self.chapter
        )
        self.browser_wol.open(url)
        try:
            bare_markers = json.loads(self.browser_wol.page.find("input", id='videoMarkers').get('data-json-markers'))
        except AttributeError:
            logger.info('WOL markers not found :(')
            return []
        if isinstance(bare_markers, dict):
            # some languages is type list (asl), others type dict (sch)
            bare_markers = [marker for _, marker in sorted(bare_markers.items(), key=lambda x: int(x[0]))]
        return [{
            'duration': marker['duration'],
            "verseNumber": int(marker['verse']),
            "startTime": marker['startTime'],
            "label": f"{self.bookname} {self.chapter}:{marker['verse']}",
            "endTransitionDuration": 0,
            }
            for marker in bare_markers
        ]
    
    def _ffprobe_markers(self) -> List[Dict]:
        return ffprobe_markers(self.videopath)

    def _api_markers(self) -> List[Dict]:
        for item in self._items():
            if (item['markers'] and
                self.chapter_from_url(item['file']['url']) == self.chapter):
                return item['markers']['markers']
        logger.info('JW-API markers not found :(')
        return []

    @property
    def not_available_verses(self) -> List[int]:
        return [
            verse for verse in self.verses
            if verse not in self.available_verses
        ]

    @property
    def available_verses(self) -> List[int]:
        return [marker['verseNumber'] for marker in self.markers]
    
    def citation(self, bookname=None, chapter=None, verses=None) -> str:
        """low level function for citation verses
        si bookname='2 Timoteo' chapter=3 verses=[1, 2, 3, 5, 6]
        devuelve 2 Timoteo 3:1-3, 5, 6
        """
        bookname = bookname or self.bookname
        chapter = chapter or self.chapter
        verses = (self.__class__(verses=verses).verses or self.verses)
        assert all([bookname, chapter, verses]), f'Debes definir bookname, chapter, verses  -->  ({self})'
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
        return f'{bookname} {chapter}:{pv}'




def ffprobe_markers(videopath):
    logger.info('Getting ffprobe markers!')
    logger.info(videopath)
    assert videopath
    console = run(
        shlex.split(f'ffprobe -v quiet -show_chapters -print_format json "{videopath}"'),
        capture_output=True,
    )
    raw_chapters = json.loads(console.stdout.decode())['chapters']
    markers = [{
        'duration': float(rc['end_time']) - float(rc['start_time']),
        'verseNumber': int(re.findall(r'\d+', rc['tags']['title'])[-1]),
        'startTime': rc['start_time'],
        'label': rc['tags']['title'].strip(),
        'endTransitionDuration': 0,

    } for rc in raw_chapters]
    return markers


def remove_html_tags(text): return re.compile(r'<[^>]+>').sub('', text).strip()

if __name__ == '__main__':
    jw = JWBible('SCH', '', 40, 24, 14)
    print(f'{jw.booknum} {jw.bookname}')
    jw.booknum = 40
    print(f'{jw.booknum} {jw.bookname}')
    jw.booknum = 10
    print(f'{jw.booknum} {jw.bookname}')
