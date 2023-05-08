from pathlib import Path
import re
from typing import List, Dict, Optional, Union
import json
from subprocess import run
import shlex
from datetime import datetime

from bot.logs import get_logger
from bot.utils.browser import LazyBrowser
from bot.jw.language import JWLanguage
from bot.jw.bible import BaseBible
from bot.jw import URL_PUBMEDIA
from bot.jw import URL_WOL_DISCOVER


logger = get_logger(__name__)


def clean(func):
    def function(self):
        s = re.sub('(nbsp;|amp;|&)', ' ', func(self))
        return re.sub(' +', ' ', s)
    return function


class SignsBible(BaseBible):
    browser_pubmedia = LazyBrowser()

    def __init__(
            self,
            sign_language_meps_symbol: str = None,
            booknum: Optional[int] = None,
            chapternum: Optional[int] = None,
            verses: Union[int, str, List[str], List[int]] = [],
            **kwargs):
        super().__init__(sign_language_meps_symbol, booknum, chapternum, verses)
    
    @property
    def api_url(self):
        return URL_PUBMEDIA.format(language_meps_symbol=self.language_meps_symbol, booknum=self.booknum, track=self.chapternum or '')

    @property
    def _rawdata(self) -> Dict:
        assert all([self.language_meps_symbol, self.booknum]), f'Debes definir language_code y booknum ({self.language_meps_symbol} {self.booknum})'
        url_1 = self.api_url
        url_2 = URL_PUBMEDIA.format(language_meps_symbol=self.language_meps_symbol, booknum=self.booknum, track='')

        if self.browser_pubmedia.url in [url_1, url_2]:
            # print('cached track or without track')
            return self.browser_pubmedia.response.json()

        r = self.browser_pubmedia.open(url_1)
        if r.status_code == 200:
            # print(f'exists rawdata with track {self.chapternum}')
            return r.json()
    
        # print(f'doesnt exists rawdata with track {self.chapternum}. Trying without track')
        r = self.browser_pubmedia.open(url_2)
        if r.status_code == 200:
            # print('exists rawdata without track')
            return r.json()
        else:
            # print('this book doesnt exists in that language')
            self.browser_pubmedia.open_fake_page('')
            return {}

    def files(self) -> Dict:
        for files in self._rawdata['files'][self.language_meps_symbol].values():
            for file in files:
                yield file

    def _match(self, chapternum=None, quality=None) -> Dict:
        chapternum = int(chapternum) if chapternum is not None else self.chapternum
        quality = quality or self.get_best_quality()
        assert isinstance(chapternum, (int, str)), f'Debes definir capítulo {self.chapternum}'
        for file in self.files():
            if (file['label'] == quality and file['track'] == chapternum):
                return file
        else:
            raise Exception(f'No hay coincidencias')
    
    def pubmedia_exists(self) -> bool:
        return bool(self._rawdata)
    
    @property
    @clean
    def bookname(self) -> str:
        return self._rawdata['pubName']
    
    def get_video_url(self, chapternum=None, quality=None) -> str:
        return self._match(chapternum, quality)['file']['url']

    def get_checksum(self, chapternum=None, quality=None) -> str:
        return self._match(chapternum, quality)['file']['checksum']

    def get_modified_datetime(self, chapternum=None, quality=None) -> datetime:
        return datetime.fromisoformat(self._match(chapternum, quality)['file']['modifiedDatetime'])
    
    def get_title(self):
        return next(self.files())['title']

    def get_available_qualities(self) -> List[str]:
        qualities = set()
        for item in self.files():
            qualities.update([item['label']])
        return sorted(qualities)
    
    def get_best_quality(self):
        return self.get_available_qualities()[-1]

    def check_chapternumber(self) -> bool:
        try:
            return self.chapternum in (int(file['track']) for file in self.files()) or self.chapternum in (int(file['track']) for file in self.__class__(self.language_meps_symbol, self.booknum).files())
        except KeyError:
            return False
    
    def get_all_chapternumber(self) -> List[int]:
        chapters = set((int(item['track'])) for item in self.__class__(self.language_meps_symbol, self.booknum).files() if item['hasTrack'])
        return sorted(chapters)
    

    def get_markers(self) -> List[Dict]:
        return self._api_markers() or self._ffprobe_markers()

    
    def _ffprobe_markers(self) -> List[Dict]:
        url = self.get_video_url(quality=self.get_available_qualities()[0])
        return ffprobe_markers(url)

    def _api_markers(self) -> List[Dict]:
        logger.info('Getting JW-API markers')
        for item in self.files():
            if (item['markers'] and
                chapter_from_url(item['file']['url']) == self.chapternum):
                markers = item['markers']['markers']
                break
        else:
            logger.info('JW-API markers not found :(')
            return []
        # PEP 20 Explicit is better than implicit.
        return [dict(
            verseNumber=int(marker['verseNumber']),
            duration=str(marker['duration']),
            startTime=str(marker['startTime']),
            endTransitionDuration=str(marker['endTransitionDuration']),
            label=str(marker['label'])
        ) for marker in markers]

    def wol_discover(self, verse=None) -> Optional[str]:
        if self.language.is_wol_available():
            return URL_WOL_DISCOVER.format(language_code=self.language.code,
                                        rsconf=self.language.rsconf,
                                        lib=self.language.lib,
                                        booknum=self.booknum,
                                        chapter=self.chapternum,
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

if __name__ == '__main__':
    jw = SignsBible(JWLanguage('SCH'), 40, 24, [14, 15, 16])
    print(jw.markers)
