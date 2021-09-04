import json
from pathlib import Path
import logging
from typing import List, Union
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

PATH_DATA = Path('jw_data.json')
PATH_DATA.touch()

# TODO Reescribir en base de datos en sql. Mantener nombres de metodos

class LocalData:
    def __init__(self,
                 code_lang: str = None,
                 quality: str = None,
                 booknum: Union[str, int] = None,
                 chapter: Union[str, int] = None,
                 verses: List[str] = [],
                 **kwargs,
                 ):
        self.code_lang = code_lang
        self.quality = quality
        self.booknum = str(booknum) if booknum else booknum
        self.chapter = str(chapter) if chapter else chapter
        self.verses = [str(verse) for verse in verses]
        self.new_verses = {}
        self._all = self._read_all()
        self.data = self._all.get(code_lang, {}).get(quality) or {}
        self.existing_verses = self.get_entry().get('verses') or {}
        self._path = None
    
    @property
    def path(self):
        ps = self._path or self.get_entry().get('file')
        if ps:
            return Path(ps)
        else:
            return Path("Dummy text because this path doesn't exists")
    
    @path.setter
    def path(self, value):
        self._path = value

    def add_verse(self, verse, versename, file_id):
        self.new_verses[str(verse)] = dict(
            name=versename,
            file_id=file_id,
            addedDatetime=datetime.now().isoformat(sep=' ', timespec='seconds'),
        )
    
    def get_fileid(self, verse):
        verse_info = self.existing_verses.get(str(verse)) or {}
        return verse_info.get('file_id')

    def get_versename(self, verse):
        verse_info = self.existing_verses.get(str(verse)) or {}
        return verse_info.get('name')

    def save(self, checksum: str, modifiedDatetime: str, filesize: int) -> None:
        self._all \
            .setdefault(self.code_lang, {}) \
            .setdefault(self.quality, {}) \
            .setdefault(self.booknum, {})[self.chapter] = dict(
                file=str(self.path),
                verses={**self.new_verses, **self.existing_verses},
                checksum=checksum,
                modifiedDatetime=modifiedDatetime,
                filesize=filesize,
            )
        
        with open(PATH_DATA, 'w', encoding='utf-8') as f:
            json.dump(self._all, f, ensure_ascii=False, indent=2, sort_keys=True)
        self.data = self._all.get(self.code_lang, {}).get(self.quality) or {}

    @staticmethod
    def _read_all() -> dict:
        try:
            return json.loads(PATH_DATA.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            print('No leido')
            return {}

    def get_entry(self):
        try:            
            return self.data[self.booknum][self.chapter]
        except KeyError:
            return {}
    
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
            if (True if not self.booknum else booknum == self.booknum):
                for chapter, dfile in isorted(dchapters):
                    if (True if not self.chapter else chapter == self.chapter):
                        for verse, info in isorted(dfile['verses']):
                            # concatenated verse in self.verses
                            vinv = any([v if v in self.verses  else None for v in verse.split()])
                            if (True if not self.verses else vinv):
                                yield info['name'], info['file_id']

    @property
    def filesize(self):
        # TODO entry filesize. nuevos metodos checksum modified date etc
        return self.get_entry().get('filesize')

    @property
    def checksum(self):
        return self.get_entry().get('checksum')
    
    @property
    def modifiedDatetime(self):
        return self.get_entry().get('modifiedDatetime')
    
    @property
    def addedDatetime(self):
        return self.get_entry().get('addedDatetime')
    
    def discard_verses(self):
        self.existing_verses = {}


    def __str__(self):
        return '<LocalData object>\n' + json.dumps({
            'file': str(self.path),
            'verses': {**self.new_verses, **self.existing_verses},
        }, indent=2, ensure_ascii=False)

def isorted(dictionary):
    try:
        return sorted(dictionary.items(), key=lambda x: int(x[0]))
    except ValueError:
        return sorted(dictionary.items(), key=lambda x: int(x[0].split()[0]))