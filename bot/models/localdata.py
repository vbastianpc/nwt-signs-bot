import json
from pathlib import Path
import logging
from typing import List


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

PATH_DATA = Path('jw_data.json')
PATH_DATA.touch()

# TODO 
class LocalData:
    def __init__(self,
                 lang: str,
                 quality: str,
                 booknum: str = None,
                 chapter: str = None,
                 verses: List[str] = [],
                 ):
        self.lang = lang
        self.quality = quality
        self.booknum = booknum
        self.chapter = chapter
        self.verses = verses
        self.new_verses = {}
        self._all = self._read_all()
        self.data = self._all.get(lang, {}).get(quality) or {}
        self.existing_verses = self.get_entry().get('verses') or {}
        self._path = None
    
    @property
    def path(self):
        ps = self._path or self.get_entry().get('file')
        if ps and Path(ps).exists():
            return Path(ps)
    
    @path.setter
    def path(self, value):
        self._path = value

    def add_verse(self, verse, versename, file_id):
        self.new_verses[verse] = {'name': versename, 'file_id': file_id}
    
    def get_fileid(self, verse):
        verse_info = self.existing_verses.get(verse) or {}
        return verse_info.get('file_id')

    def get_versename(self, verse):
        verse_info = self.existing_verses.get(verse) or {}
        return verse_info.get('name')

    def save(self) -> None:
        self._all \
            .setdefault(self.lang, {}) \
            .setdefault(self.quality, {}) \
            .setdefault(self.booknum, {})[self.chapter] = {
                'file': str(self.path),
                'verses': {**self.new_verses, **self.existing_verses},
            }
        
        with open(PATH_DATA, 'w', encoding='utf-8') as f:
            json.dump(self._all, f, ensure_ascii=False, indent=2, sort_keys=True)
        self.data = self._all.get(self.lang, {}).get(self.quality) or {}

    @staticmethod
    def _read_all() -> dict:
        try:
            return json.loads(PATH_DATA.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            print('No leido')
            return {}

    def get_entry(self):
        try:            
            entry = self.data[self.booknum][self.chapter]
        except KeyError:
            entry = {}
        return entry
    
    def iter_match_verses(self):
        "Iterar versículos coincidentes"
        for verse, info in self.get_entry().get('verses', {}).items():
            if verse in self.verses:
                yield info['name'], info['file_id']

    def iter_verses(self):
        "Iterar en todos los versículos"
        for dbooknums in self.data.values():
            for entry in dbooknums.values():
                for info in entry['verses'].values():
                    yield info['name'], info['file_id']

    def iter_smart(self):
        for booknum, dchapters in isorted(self.data):
            if bool(True if not self.booknum else booknum == self.booknum):
                for chapter, dfile in isorted(dchapters):
                    if bool(True if not self.chapter else chapter == self.chapter):
                        for verse, info in isorted(dfile['verses']):
                            if bool(True if not self.verses else verse in self.verses):
                                yield info['name'], info['file_id']

    @property
    def filesize(self):
        try:
            return self.path.stat().st_size
        except (FileNotFoundError, AttributeError):
            return 0
    
    def discard_verses(self):
        self.existing_verses = {}


    def __str__(self):
        return '<LocalData object>\n' + json.dumps({
            'file': str(self.path),
            'verses': {**self.new_verses, **self.existing_verses()},
        }, indent=2, ensure_ascii=False)

def isorted(dictionary):
    try:
        return sorted(dictionary.items(), key=lambda x: int(x[0]))
    except ValueError:
        return sorted(dictionary.items(), key=lambda x: int(x[0].split()[0]))