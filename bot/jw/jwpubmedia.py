from pathlib import Path
import re
from typing import List, Dict, Union, Optional
import json
from subprocess import run
import shlex
from urllib.parse import urlparse

from bot import get_logger
from bot.utils.browser import LazyBrowser
from bot.utils.models import LazyProperty
from bot.jw.jwlanguage import JWLanguage
from bot.jw import URL_PUBMEDIA
from bot.jw import URL_WOLBIBLE
from bot.jw import SHARE_URL
from bot.jw import URL_WOL_DISCOVER



logger = get_logger(__name__)

class NWT:
    browser_wol = LazyBrowser()

    def __init__(self,
                 lang: JWLanguage = None, # speak language
                 booknum: int = None,
                 chapter: int = None,
                 verses: Union[List[str], List[int]] = None,
                 ):
        self.booknum = booknum
        self.chapter = chapter
        self.verses = verses
        self.lang = lang
    
    def passages(self):
        global span
        if not all([self.lang, self.booknum, self.chapter, self.verses]):
            raise ValueError('First you must define lang, booknum, chapter and verses')
        self.browser_wol.open(SHARE_URL(self.lang.code, self.booknum, self.chapter))
        article = self.browser_wol.page.find('article', id='article')
        href = SHARE_URL(self.lang.code, self.booknum, self.chapter, sorted(self.verses)[0], sorted(self.verses)[-1])
        header = f'<a href="{href}"><b>{article.get("data-bookname")} {article.get("data-chapter")}</b></a>:'
        passages = [header]
        for i, versenum in enumerate(self.verses):
            verse_href = f'<a href="{SHARE_URL(self.lang.code, self.booknum, self.chapter, versenum)}"><b>{versenum}</b></a>'
            span = self.browser_wol.page.find('span', id=f'v{self.booknum}{self.chapter:0=3}{versenum:0=3}')
            spanverse = ''
            for e in span.find_all('span'):
                c = e.get('class')
                if 'first' in c:
                    spanverse += '    '
                spanverse += '    ' if 'style-z' in c else '\n' if 'style-l' in c else ''
                if e.find('sup', class_='verseNum'):
                    spanverse += '\n    ' if i > 0 and versenum != self.verses[i-1] + 1 else ''
                    spanverse += verse_href
                if any(['style-' in cc for cc in c]):
                    spanverse += ''.join(e.find_all(text=True, recursive=False)).rstrip()
                if 'parabreak' in c or 'newblock' in c:
                    spanverse += '\n'
            spanverse = re.sub(r'(\xa0)+', ' ', spanverse)
            if versenum == 1:
                spanverse = f'{verse_href} {spanverse.lstrip()}'
            if i == 0:
                spanverse = spanverse.lstrip()
            passages.append(spanverse + ' ')
        print(passages)
        text = ''.join(passages)
        text = re.sub(r'( ?\n ?)+', '\n', text)
        return text



def clean(func):
    def function(self):
        s = re.sub('(nbsp;|amp;|&)', ' ', func(self))
        return re.sub(' +', ' ', s)
    return function

class JWBible:
    browser_pubmedia = LazyBrowser()
    browser_wol = LazyBrowser()

    def __init__(self,
                 sign_lang_code: str = None,
                 booknum: Union[str, int] = None,
                 chapter: Union[str, int] = None,
                 verses: Union[int, str, List[str], List[int]] = [],
                 lang_locale_written: str = None,
                 **kwargs,
                 ):
        self.lang = JWLanguage(sign_lang_code)
        self.nwt = NWT()
        self.booknum = booknum
        self.chapter = chapter
        self.verses = verses
        self.lang_locale_written = lang_locale_written
    
    def __str__(self):
        return f'lang.code={self.lang.code}\tbooknum={self.booknum}\tchapter={self.chapter}\tverses={self.verses}'
    
    @property
    def booknum(self) -> Optional[int]:
        return self._booknum
    
    @booknum.setter
    def booknum(self, value):
        if hasattr(self, '_booknum') and self._booknum is not None and int(self._booknum) != int(value): # pylint: disable=access-member-before-definition
            self.__dict__.pop('markers', None)
        try:
            self._booknum = int(value)
            self.nwt.booknum = int(value)
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
            self.nwt.chapter = int(value)
        except TypeError:
            self._chapter = None

    @property
    def verses(self) -> Optional[List[int]]:
        return self._verses
    
    @verses.setter
    def verses(self, value):
        if isinstance(value, list):
            self._verses = [int(verse) for verse in value]
            self.nwt.verses = [int(verse) for verse in value]
        elif isinstance(value, (int, str)):
            self._verses = [int(value)]
            self.nwt.verses = [int(value)]
        elif value is None:
            self._verses = None
        else:
            raise TypeError(f'verses must be a list, a string or an integer, not {type(value).__name__}')
    
    @property
    def lang_locale_written(self) -> str:
        return self._lang_locale_written
    
    @lang_locale_written.setter
    def lang_locale_written(self, value):
        self._lang_locale_written = value
        self.nwt.lang = JWLanguage(locale=value)

    
    @property
    def _rawdata(self) -> Dict:
        assert all([self.lang.code, self.booknum]), f'Debes definir lang.code y booknum ({self.lang.code} {self.booknum})'
        url_without_track = URL_PUBMEDIA.format(lang_code=self.lang.code, booknum=self.booknum, track='')
        if self.chapter and self.browser_pubmedia.url == url_without_track:
            return self.browser_pubmedia.response.json()

        url = URL_PUBMEDIA.format(lang_code=self.lang.code, booknum=self.booknum, track=self.chapter or '')
        r = self.browser_pubmedia.open(url)
        if r.status_code == 200:
            return r.json()

        r = self.browser_pubmedia.open(url_without_track)
        if r.status_code == 200:
            return r.json()
        self.browser_pubmedia.open_fake_page('')
        return {}

    def _items(self) -> Dict:
        for files in self._rawdata['files'][self.lang.code].values():
            for item in files:
                yield item

    def _match(self, quality=None, chapter=None) -> Dict:
        quality = quality or self.get_best_quality()
        chapter = int(chapter) if isinstance(chapter, (int, str)) else self.chapter
        assert isinstance(chapter, (int, str)), f'Debes definir capítulo {self.chapter}'
        for item in self._items():
            if (item['label'] == quality and item['track'] == chapter):
                return item
        else:
            raise Exception(f'No hay coincidencias')
    
    def pubmedia_exists(self) -> bool:
        return bool(self._rawdata)
    
    @property
    @clean
    def bookname(self) -> str:
        return self._rawdata['pubName']
    
    def get_video_url(self, **kwargs) -> str:
        return self._match(**kwargs)['file']['url']

    @property
    @clean
    def title_chapter(self) -> str:
        return self._match()['title']

    def get_checksum(self, chapter=None, quality=None) -> str:
        return self._match(
            quality=quality or self.get_best_quality(),
            chapter=chapter if isinstance(chapter, (int, str)) else self.chapter
        )['file']['checksum']
    
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
        chapters = set((int(item['track'])) for item in self._items() if item['hasTrack'])
        return sorted(chapters)
    
    def match_marker(self, verseNumber) -> Dict:
        for marker in self.markers:
            if int(marker['verseNumber']) == int(verseNumber):
                return marker
        raise Exception('Verse number not found')

    @LazyProperty
    def markers(self) -> List[Dict]:
        return self._api_markers() or self._ffprobe_markers()
    
    def get_markers(self):
        """Wrap function"""
        return self.markers

    def _wol_markers(self) -> List[Dict]:
        logger.info('Scrapping WOL markers!')
        url = URL_WOLBIBLE.format(
            locale=self.lang.locale,
            rsconf=self.lang.rsconf,
            lib=self.lang.lib,
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
        logger.info('Getting JW-API markers')
        for item in self._items():
            if (item['markers'] and
                chapter_from_url(item['file']['url']) == self.chapter):
                # return item['markers']['markers'] # nope
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
        chapter = chapter if isinstance(chapter, (int, str)) else self.chapter
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

    def wol_discover(self, verse=None) -> Optional[str]:
        if self.lang.is_wol_available():
            return URL_WOL_DISCOVER.format(locale=self.lang.locale,
                                        rsconf=self.lang.rsconf,
                                        lib=self.lang.lib,
                                        booknum=self.booknum,
                                        chapter=self.chapter,
                                        first_verse=verse or self.verses[0],
                                        last_verse=verse or self.verses[-1]
                                        )


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
