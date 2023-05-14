from pathlib import Path
import re
import json
from subprocess import run
import shlex
from datetime import datetime

from bot.logs import get_logger
from bot.utils.browser import LazyBrowser
from bot.database import get
from bot.jw import Jw_Url


logger = get_logger(__name__)


def clean(func):
    def function(self):
        s = re.sub('(nbsp;|amp;|&)', ' ', func(self))
        return re.sub(' +', ' ', s)
    return function

# TODO
# Este clase lee y escribe en la base de datos a través de localdatabase
# metodos para pubmedia señas
#   si existe el versículo solicitado
#   si por lo menos existe el capítulo
#   obtener todos los capítulos disponibles
#   hacer lo que hace manage_video_markers
#

class ParsePubmedia(Jw_Url):
    __slots__ = ('browser')

    def __init__(self,
                   language_code: str,
                   booknumber: int,
                   chapternumber: int | None,
                   verses: int | str | list[int | str] | None = None
                   ):
        super().__init__(language_code, booknumber, chapternumber, verses)
        self.browser = LazyBrowser()

    @property
    def data(self) -> dict:
        # fetch Lazy Property?
        url_1 = self.url_pubmedia()
        url_2 = self.url_pubmedia(all_chapters=True)

        if self.browser.url in [url_1, url_2]:
            # print('cached track or without track')
            return self.browser.response.json()

        r = self.browser.open(url_1)
        if r.status_code == 200:
            # print(f'exists rawdata with track {self.chapternum}')
            return r.json()
    
        # print(f'doesnt exists rawdata with track {self.chapternum}. Trying without track')
        r = self.browser.open(url_2)
        if r.status_code == 200:
            # print('exists rawdata without track')
            return r.json()
        else:
            # print('this book doesnt exists in that language')
            self.browser.open_fake_page('')
            return {}

    def files(self) -> dict:
        for files in self.data['files'][self.language.meps_symbol].values():
            for file in files:
                yield file

    def _match(self, chapternum=None, quality=None) -> dict:
        chapternum = int(chapternum) if chapternum is not None else self.chapternumber
        quality = quality or self.best_quality
        assert isinstance(chapternum, (int, str)), f'Debes definir capítulo'
        for file in self.files():
            if (file['label'] == quality and file['track'] == chapternum):
                return file
        else:
            raise Exception(f'No hay coincidencias')

    def pubmedia_exists(self) -> bool:
        return bool(self.data)

    def get_video_url(self, chapternum=None, quality=None) -> str:
        return self._match(chapternum, quality)['file']['url']

    def get_checksum(self, chapternum=None) -> str:
        return self._match(chapternum)['file']['checksum']

    def get_modified_datetime(self, chapternum=None) -> datetime:
        return datetime.fromisoformat(self._match(chapternum)['file']['modifiedDatetime'])

    def get_available_qualities(self) -> list[str]:
        qualities = set()
        for item in self.files():
            qualities.update([item['label']])
        return sorted(qualities)
    
    @property
    def best_quality(self) -> str:
        return self.get_available_qualities()[-1]

    def check_chapternumber(self) -> bool:
        try:
            return self.chapternumber in (int(file['track']) for file in self.files())
        except KeyError:
            return False

    def get_all_chapternumber(self) -> list[int]:
        chapters = set((int(item['track'])) for item in self.__class__(self.language_meps_symbol, self.booknum).files() if item['hasTrack'])
        return sorted(chapters)

    def get_markers(self) -> list[dict]:
        return self._api_markers() or self._ffprobe_markers()
    
    def _ffprobe_markers(self) -> list[dict]:
        url = self.get_video_url(quality=self.get_available_qualities()[0])
        return ffprobe_markers(url)

    def _api_markers(self) -> list[dict]:
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

def chapter_from_url(url) -> int | None:
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
