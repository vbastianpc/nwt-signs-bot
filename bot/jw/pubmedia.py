from pathlib import Path
import re
from typing import List, Dict, Optional
import json
from subprocess import run
import shlex

from bot import get_logger
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def _rawdata(self) -> Dict:
        assert all([self.lang.code, self.booknum]), f'Debes definir lang.code y booknum ({self.lang.code} {self.booknum})'
        url_1 = URL_PUBMEDIA.format(lang_code=self.lang.code, booknum=self.booknum, track=self.chapter or '')
        url_2 = URL_PUBMEDIA.format(lang_code=self.lang.code, booknum=self.booknum, track='')

        if self.browser_pubmedia.url in [url_1, url_2]:
            # print('cached track or without track')
            return self.browser_pubmedia.response.json()

        r = self.browser_pubmedia.open(url_1)
        if r.status_code == 200:
            # print(f'exists rawdata with track {self.chapter}')
            return r.json()
    
        # print(f'doesnt exists rawdata with track {self.chapter}. Trying without track')
        r = self.browser_pubmedia.open(url_2)
        if r.status_code == 200:
            # print('exists rawdata without track')
            return r.json()
        else:
            # print('this book doesnt exists in that language')
            self.browser_pubmedia.open_fake_page('')
            return {}

    def files(self) -> Dict:
        for files in self._rawdata['files'][self.lang.code].values():
            for file in files:
                yield file

    def _match(self, chapter=None, quality=None) -> Dict:
        chapter = int(chapter) if isinstance(chapter, (int, str)) else self.chapter
        quality = quality or self.get_best_quality()
        assert isinstance(chapter, (int, str)), f'Debes definir capítulo {self.chapter}'
        for file in self.files():
            if (file['label'] == quality and file['track'] == chapter):
                return file
        else:
            raise Exception(f'No hay coincidencias')
    
    def pubmedia_exists(self) -> bool:
        return bool(self._rawdata)
    
    @property
    @clean
    def bookname(self) -> str:
        return self._rawdata['pubName']
    
    def get_video_url(self, chapter=None, quality=None) -> str:
        return self._match(chapter, quality)['file']['url']

    def get_checksum(self, chapter=None, quality=None) -> str:
        return self._match(
            quality=quality or self.get_best_quality(),
            chapter=chapter if isinstance(chapter, (int, str)) else self.chapter
        )['file']['checksum']

    def get_available_qualities(self) -> List[str]:
        qualities = set()
        for item in self.files():
            qualities.update([item['label']])
        return sorted(qualities)
    
    def get_best_quality(self):
        return self.get_available_qualities()[-1]

    def check_chapternumber(self) -> bool:
        try:
            return self.chapter in (int(file['track']) for file in self.files()) or self.chapter in (int(file['track']) for file in self.__class__(self.lang, self.booknum).files())
        except KeyError:
            return False
    
    def get_all_chapternumber(self) -> List[int]:
        chapters = set((int(item['track'])) for item in self.__class__(self.lang, self.booknum).files() if item['hasTrack'])
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
                chapter_from_url(item['file']['url']) == self.chapter):
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

if __name__ == '__main__':
    jw = SignsBible(JWLanguage('SCH'), 40, 24, [14, 15, 16])
    print(jw.markers)
