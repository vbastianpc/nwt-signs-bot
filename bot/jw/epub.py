import re
from pathlib import Path
from typing import Optional, List
import requests
from zipfile import ZipFile


from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag, PageElement

from bot.jw import SHARE_URL
from bot.jw.bible import BaseBible
from bot.jw.language import JWLanguage


EPUB_PATH = Path('bible-epub')

class Epub(BaseBible):
    def __init__(self, *args, download=True, **kwargs):
        super().__init__(*args, **kwargs)
        if download and not self.epub_file:
            self.download()
            self.unzip()

    def dirpath(self):
        path = EPUB_PATH / f'nwt_{self.lang.code}'
        if path.exists() and path.is_dir():
            return path
        else:
            for e in EPUB_PATH.glob(f'*_{self.lang.code}'):
                if e.is_dir:
                    return e
            else:
                raise FileNotFoundError(f'{EPUB_PATH}/*_{self.lang.code} not found')

    def download(self, pub='nwt'):
        api_url = "https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS"
        params = {
            "output": "json",
            "pub": pub, 
            "fileformat": "EPUB",
            "alllangs": 0,
            "langwritten": self.lang.code,
            "txtCMSLang": self.lang.code,
            'isBible': '1'
        }
        r = requests.get(api_url, params)
        if r.status_code == 404 and pub != 'bi12':
            return self.download(pub='bi12')
        elif pub == 'bi12':
            raise ValueError(f'{self.lang.code!r} Bible unavailable')
        url = r.json()['files'][self.lang.code]['EPUB'][0]['file']['url']
        with requests.get(url, stream=True) as r:
            with open(EPUB_PATH / Path(url).name, mode="wb") as f:
                for chunk in r.iter_content(chunk_size=128*1024):
                    f.write(chunk)
        return EPUB_PATH / Path(url).name

    def unzip(self):
        directory_to_extract = Path(self.epub_file).parent / self.epub_file.stem
        directory_to_extract.mkdir(exist_ok=True)    
        with ZipFile(self.epub_file, 'r') as zip_ref:
            zip_ref.extractall(directory_to_extract)

    @property
    def epub_file(self):
        for file in EPUB_PATH.glob(f'*_{self.lang.code}.epub'):
            if file.is_file():
                return file
    
    @property
    def bookname(self) -> Optional[str]:
        file = self.dirpath() / f'OEBPS/biblechapternav{self.booknum}.xhtml'
        nav_soup = BeautifulSoup(file.read_bytes(), 'html.parser')
        return nav_soup.title.text
    
    
    def get_text(self) -> str:
        url = SHARE_URL(self.lang.code, self.booknum, self.chapter, self.verses[0], self.verses[-1])
        return f'<a href="{url}">{self.bookname} {self.chapter}</a>\n' + \
            "".join(self.verse_text())


    def verse_text(self) -> List[str]:
        versenav = self.dirpath() / f'OEBPS/bibleversenav{self.booknum}_{self.chapter}.xhtml'
        nav_soup = BeautifulSoup(versenav.read_bytes(), 'html.parser')
        verses = []
        for versenum in self.verses:
            target_file, id_ = nav_soup.body.table.find('a', text=versenum).get('href').split('#')
            target_file = (self.dirpath() / 'OEBPS') /target_file
            b = BeautifulSoup(target_file.read_bytes(), 'html.parser')
            span = b.find('span', id=id_)
            text = self._format_verse(span.next, versenum)
            verses.append(text)
        return verses

    def _format_verse(self, e: PageElement, versenum: int):
        text = f'<a href="{SHARE_URL(self.lang.code, self.booknum, self.chapter, versenum)}">{versenum}</a> '
        i = 0
        while True:
            i += 1
            if (e is None or
               (e.name == 'div' and '' in 'groupFootnote' in e.get('class')) or
               (isinstance(e, Tag) and e.get('id') and e.get('id').startswith('chapter'))
            ):
                break

            if e.name == 'p':
                text += '\n'
                if 'sz' in e.get('class'):
                    text += '    '
                elif 'sb' in e.get('class'):
                    text += '  '
                elif 'sl' in e.get('class'):
                    text += ''
            if isinstance(e, NavigableString):
                try:
                    int(e)
                except ValueError:
                    text += e
                else:
                    pass
            e = e.next

        text = re.sub(r'(\xa0)+', ' ', text)
        text = re.sub(r'(\n)+', '\n', text)
        return text.replace('*', '')


if __name__ == '__main__':
    import sys
    from bot import ADMIN, TOKEN
    from telegram import Bot

    epub = Epub(JWLanguage('S'), 43, 1, [1, 2])
    print('ESPAÑOL')
    print(epub.get_text())
    # print('"', epub.get_text(), '"')
    bot = Bot(TOKEN)
    # bot.send_message(chat_id=ADMIN, text=epub.get_text(), parse_mode='HTML', disable_web_page_preview=True)
    print('Enviado')
    

