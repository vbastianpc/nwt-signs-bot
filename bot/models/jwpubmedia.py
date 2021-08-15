from pathlib import Path
from mechanicalsoup import browser
import requests
import logging
import re
from typing import List, Dict
import json
from subprocess import run
import shlex

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
                 quality: str = None,
                 booknum: str = None,
                 chapter: str = None,
                 verses: List[str] = [],
                 videopath: str = None,
                 ):
        self.lang = lang
        self.booknum = booknum
        self.chapter = chapter
        self.verses = verses
        self.quality = quality
        self.videopath = videopath
    
    @LazyProperty
    def data(self):
        url = URL_PUBMEDIA.format(lang=self.lang, booknum=self.booknum)
        print(url)
        r = requests.get(url)
        if r.status_code == 200:
            return r.json()
    
    def book_exists(self):
        return bool(self.data)
    
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
    
    def match_marker(self, verseNumber):
        for marker in self.markers:
            if marker['verseNumber'] == int(verseNumber):
                return marker
        raise Exception('Verse number not found')

    def verse_name(self, verseNumber):
        return self.match_marker(verseNumber)['label']

    @property
    def bookname(self):
        return self.data['pubName']        
    
    @LazyProperty
    def markers(self) -> List[Dict]:
        mks = self.wol_markers or self.jw_api_markers or self.ffprobe_markers
        logger.info('Getting endTransitionDuration from JW-API markers!')
        for marker in mks:
            marker['endTransitionDuration'] = next(
                (jam['endTransitionDuration'] for jam in self.jw_api_markers if jam['verseNumber'] == marker['verseNumber']),
                marker['endTransitionDuration'],
            )
        return mks

    @LazyProperty
    def wol_markers(self) -> List[Dict]:
        return scrap_wol_markers(self.lang, self.booknum, self.chapter)
    
    @LazyProperty
    def ffprobe_markers(self):
        return ffprobe_markers(self.videopath)

    @LazyProperty
    def jw_api_markers(self):
        for item in self._items():
            if (item['markers'] and
                self.chapter_from_url(item['file']['url']) == self.chapter):
                return item['markers']['markers']
        logger.info('JW-API markers not found :(')
        return []

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
        return [str(marker['verseNumber']) for marker in self.markers]

    @staticmethod
    def get_signs_languages():
        """Deprecated. Only shows WOL availables languages. JW.ORG signs languages are missing. Example Vietnamese SLV"""
        url = 'https://data.jw-api.org/mediator/v1/languages/S/web'
        data = requests.get(url).json()
        return {lang['code']: remove_html_tags(
            lang['name']) for lang in data['languages'] if lang['isSignLanguage']}

    @staticmethod
    def signs_languages():
        browser = custom_browser()
        browser.open('https://www.jw.org/es/choose-language?onlySL=1')
        langs = []
        def find_code(item):
            for c in item.find('div', class_='optionLabel').attrs['class']:
                if c.startswith('ml-'):
                    return c.split('-')[1]
            raise Exception
        for item in browser.page.find_all('li', class_='signLanguage'):
            langs.append({
                'code': find_code(item),
                'label': item.find('div', class_='altLabel').text,
                'vernacular': item.find('div', class_='optionLabel').text,
                'href': item.find('a').get('href')
            })
        return langs

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


def scrap_wol_markers(lang, booknum, chapter):
    logger.info('Scrapping WOL markers!')
    browser = custom_browser()
    browser.open(f'https://wol.jw.org/wol/finder?wtlocale={lang}')
    locale, _, _, rsconf, lib = browser.get_url().split('/')[-5:]
    url = f'https://wol.jw.org/{locale}/wol/b/{rsconf}/{lib}/nwt/{booknum}/{chapter}'
    print(url)
    browser.open(url)
    try:
        bare_markers = json.loads(browser.page.find("input", id='videoMarkers').get('data-json-markers'))
    except AttributeError:
        logger.info('WOL markers not found :(')
        return []
    bookname = browser.page.find('h1').text
    if isinstance(bare_markers, dict):
        # some languages is type list (asl), others type dict (sch)
        bare_markers = [marker for _, marker in sorted(bare_markers.items(), key=lambda x: int(x[0]))]
    return [{
        'duration': marker['duration'],
        "verseNumber": int(marker['verse']),
        "startTime": marker['startTime'],
        "label": f"{bookname} {chapter}:{marker['verse']}",
        "endTransitionDuration": 0,
        }
        for marker in bare_markers
    ]

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


def custom_browser():
    agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
    return mechanicalsoup.StatefulBrowser(user_agent=agent)


def remove_html_tags(text): return re.compile(r'<[^>]+>').sub('', text).strip()

if __name__ == '__main__':
    # jw = JWPubMedia('SLV', booknum='1', chapter='1')
    # jw = JWPubMedia('SLV', booknum='40', chapter='5', videopath='/Users/bastianpalavecino/Downloads/nwt_40_Mt_SLV_05_r720P.mp4')
    # print(
    #     json.dumps(jw.markers, indent=2, ensure_ascii=False)
    # )
    # print(jw.available_chapters())
    # print(jw.available_verses())
    # s = scrap_wol_markers('SLV', 40, 1, 'libro')
    # markers = jw.markers
    # print(
    #     json.dumps(
    #         ffprobe_markers('/Users/bastianpalavecino/Downloads/nwt_01_Ge_SLV_02_r720P.mp4'),
    #         indent=2,
    #         ensure_ascii=False,
    #     )
    # )
    # print(
    #     json.dumps(
    #         scrap_wol_markers('SCH', 1, 1),
    #         indent=2,
    #         ensure_ascii=False,
    #     )
    # )
    print(
        json.dumps(JWPubMedia.signs_languages(), indent=2, ensure_ascii=False)
    )
