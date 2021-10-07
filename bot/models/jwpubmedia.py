from pathlib import Path
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
URL_PUBMEDIA = 'https://pubmedia.jw-api.org/GETPUBMEDIALINKS?output=json&alllangs=0&langwritten={lang_code}&txtCMSLang={lang_code}&pub=nwt&booknum={booknum}&track={track}'

# TODOS los lenguajes de señas (jw y wol), vernacular, name, lang_code
URL_LANGUAGES = 'https://data.jw-api.org/mediator/v1/languages/S/all'

# solo wol: rsconf, locale, lib, iswolavailable, (vernacular, name, lang_code)
URL_LIBRARIES = 'https://wol.jw.org/es/wol/li/r4/lp-s'

# para obtener marcadores
URL_WOLBIBLE = 'https://wol.jw.org/{locale}/wol/b/{rsconf}/{lib}/nwt/{booknum}/{chapter}'


# citas de biblia, solo si hay wol. No se ocupa
URL_CITATION = 'https://wol.jw.org/wol/api/v1/citation/{rsconf}/{lib}/bible/{startBook}/{startChapter}/{startVerse}/{endBook}/{endChapter}/{endVerse}?pub=nwtst'


# https://wol.jw.org/wol/vidlink/r377/lp-sch?pub=nwt&langwritten=SCH&booknum=4&track=30&txtCMSLang=SCH&fileformat=mp4%2Cm4v&output=json
# https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS?track=30&output=json&alllangs=0&langwritten=SCH&pub=nwt&booknum=4

class BiblePassage:
    def __init__(self,
                 booknum: int = None,
                 chapter: int = None,
                 verses: Union[int, str, List[str], List[int]] = [],
                 ):
        self.booknum = booknum
        self.chapter = chapter
        self.verses = verses

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
        if self.name in obj.__dict__ and obj.__dict__[self.name] != value:
            if '_lazies' in obj.__dict__:
                for lazy in obj.__dict__.get('_lazies') or []:
                    del obj.__dict__[lazy]
                del obj.__dict__['_lazies']
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

    def __init__(self, lang_code=None):
        self.lang_code = lang_code

    @LazyProperty
    def signs_languages(self) -> List[Dict]:
        data = self.browser.open(URL_LANGUAGES).json()
        raw_sign_languages = [item for item in data['languages'] if item['isSignLanguage']]
        languages = []
        for item in raw_sign_languages:
            languages.append({
                'code': item['code'],               # ASL
                'locale': item['locale'],           # ase
                'vernacular': item['vernacular'],   # American Sign Language
                'name': item['name'],               # lenguaje de señas americano
            })
        return languages
    
    def _get_lang_data(self, lang_code, data_name):
        return next((lang[data_name] for lang in self.signs_languages if lang['code'] == lang_code), '')
    
    def name(self, lang_code=None):
        return self._get_lang_data(lang_code or self.lang_code, 'name')

    def vernacular(self, lang_code=None):
        return self._get_lang_data(lang_code or self.lang_code, 'vernacular')

    def locale(self, lang_code=None) -> Optional[str]:
        return self._get_lang_data(lang_code or self.lang_code, 'locale')

    def is_wol_available(self, lang_code=None) -> bool:
        self.browser.open(URL_LIBRARIES)
        if self.browser.page.find('a', {'data-meps-symbol': lang_code or self.lang_code}):
            return True
        else:
            return False

    def _get_tag_attribute(self, lang_code, attribute_name) -> Optional[str]:
        self.browser.open(URL_LIBRARIES)
        try:
            value = self.browser.page.find('a', {'data-meps-symbol': lang_code}).get(attribute_name)
        except:
            return None
        else:
            return value

    def rsconf(self, lang_code=None) -> Optional[str]:
        return self._get_tag_attribute(lang_code or self.lang_code, 'data-rsconf')
    
    def lib(self, lang_code=None) -> Optional[str]:
        return self._get_tag_attribute(lang_code or self.lang_code, 'data-lib')



class JWBible(JWInfo):
    browser_pubmedia = LazyBrowser()
    browser_wol = LazyBrowser()

    def __init__(self,
                 lang_code: str = None,
                 booknum: Union[str, int] = None,
                 chapter: Union[str, int] = None,
                 verses: Union[int, str, List[str], List[int]] = [],
                 **kwargs,
                 ):
        self.lang_code = lang_code
        self.booknum = booknum
        self.chapter = chapter
        self.verses = verses
    
    def __str__(self):
        return f'lang_code={self.lang_code}\tbooknum={self.booknum}\tchapter={self.chapter}\tverses={self.verses}'
    
    @property
    def booknum(self) -> Optional[int]:
        return self._booknum
    
    @booknum.setter
    def booknum(self, value):
        if hasattr(self, '_booknum') and self._booknum is not None and int(self._booknum) != int(value): # pylint: disable=access-member-before-definition
            self.__dict__.pop('markers', None)
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
            self.__dict__.pop('markers', None)
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
        assert all([self.lang_code, self.booknum]), f'Debes definir lang_code y booknum ({self.lang_code} {self.booknum})'
        url_without_track = URL_PUBMEDIA.format(lang_code=self.lang_code, booknum=self.booknum, track='')
        if self.chapter and self.browser_pubmedia.url == url_without_track:
            return self.browser_pubmedia.response.json()

        url = URL_PUBMEDIA.format(lang_code=self.lang_code, booknum=self.booknum, track=self.chapter or '')
        r = self.browser_pubmedia.open(url)
        if r.status_code == 200:
            return r.json()

        r = self.browser_pubmedia.open(url_without_track)
        if r.status_code == 200:
            return r.json()
        self.browser_pubmedia.open_fake_page('')
        return {}

    def _items(self) -> Dict:
        for files in self._rawdata['files'][self.lang_code].values():
            for item in files:
                yield item

    def _match(self, quality=None, chapter=None) -> Dict:
        quality = quality or self.get_best_quality()
        chapter = chapter or self.chapter
        assert all([quality, chapter]), f'Debes definir capítulo {self.chapter}'
        for item in self._items():
            if (item['label'] == quality and
                chapter_from_url(item['file']['url']) == chapter):
                return item
        else:
            raise Exception(f'No hay coincidencias')
    
    def pubmedia_exists(self) -> bool:
        return bool(self._rawdata)
    
    @property
    def bookname(self) -> str:
        return self._rawdata['pubName']
    
    def get_video_url(self, **kwargs) -> str:
        return self._match(**kwargs)['file']['url']

    @property
    def title_chapter(self) -> str:
        return self._match()['title']

    def get_checksum(self, **kwargs) -> str:
        return self._match(**kwargs)['file']['checksum']
    
    def get_filesize(self, **kwargs):
        return self._match(**kwargs)['filesize']

    def get_available_qualities(self) -> List[str]:
        qualities = set()
        for item in self._items():
            qualities.update([item['label']])
        return sorted(qualities)
    
    def get_best_quality(self):
        return self.get_available_qualities()[-1]

    def get_modified_datetime(self, **kwargs) -> str:
        return self._match(**kwargs)['file']['modifiedDatetime']
    
    def get_representative_datetime(self, chapter=None) -> str:
        return self.get_modified_datetime(chapter=chapter, quality=self.get_best_quality())

    def check_chapternumber(self) -> bool:
        try:
            return self.chapter in (int(item['track']) for item in self._items())
        except KeyError:
            return False
    
    def get_all_chapternumber(self) -> List[int]:
        chapters = set((int(item['track'])) for item in self._items())
        return sorted(chapters)
    
    def match_marker(self, verseNumber) -> Dict:
        for marker in self.markers:
            if int(marker['verseNumber']) == int(verseNumber):
                return marker
        raise Exception('Verse number not found')

    @LazyProperty
    def markers(self) -> List[Dict]:
        mks = self._wol_markers() or self._ffprobe_markers()
        logger.info('Getting endTransitionDuration from JW-API markers!')
        for marker in mks:
            marker['endTransitionDuration'] = next(
                (str(jam['endTransitionDuration']) for jam in self._api_markers() if jam['verseNumber'] == marker['verseNumber']),
                marker['endTransitionDuration'],
            )
        return mks
    
    def get_markers(self):
        """Wrap function"""
        return self.markers

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
            'duration': str(marker['duration']),
            "verseNumber": int(marker['verse']),
            "startTime": str(marker['startTime']),
            "label": f"{self.bookname} {self.chapter}:{marker['verse']}",
            "endTransitionDuration": '0',
            }
            for marker in bare_markers
        ]
    
    def _ffprobe_markers(self) -> List[Dict]:
        return ffprobe_markers(self.get_video_url())

    def _api_markers(self) -> List[Dict]:
        for item in self._items():
            if (item['markers'] and
                chapter_from_url(item['file']['url']) == self.chapter):
                # return item['markers']['markers']
                # PEP 20 Explicit is better than implicit.
                markers = item['markers']['markers']
                return [dict(
                    verseNumber=int(marker['verseNumber']),
                    duration=str(marker['duration']),
                    startTime=str(marker['startTime']),
                    endTransitionDuration=str(marker['endTransitionDuration']),
                    label=str(marker['label'])
                ) for marker in markers]
        logger.info('JW-API markers not found :(')
        return []

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


def chapter_from_url(url) -> Optional[int]:
    " returns '1' if url= '/.../nwt_40_Mt_SCH_01_r240P.mp4'"
    try:
        return int(Path(url).name.split('_')[4])
    except (IndexError, ValueError):
        return None


def ffprobe_markers(videopath):
    logger.info('Getting ffprobe markers! %s', videopath)
    console = run(
        shlex.split(f'ffprobe -v quiet -show_chapters -print_format json "{videopath}"'),
        capture_output=True,
    )
    raw_chapters = json.loads(console.stdout.decode())['chapters']
    markers = [{
        'duration': str(float(rc['end_time']) - float(rc['start_time'])),
        'verseNumber': int(re.findall(r'\d+', rc['tags']['title'])[-1]),
        'startTime': str(rc['start_time']),
        'label': rc['tags']['title'].strip(),
        'endTransitionDuration': '0',

    } for rc in raw_chapters]
    return markers


def remove_html_tags(text): return re.compile(r'<[^>]+>').sub('', text).strip()

if __name__ == '__main__':
    jw = JWBible('SCH', 40, 24, 14)
    print(f'{jw.booknum} {jw.bookname}')
    jw.booknum = 40
    print(f'{jw.booknum} {jw.bookname}')
    jw.booknum = 10
    print(f'{jw.booknum} {jw.bookname}')
