import re
from pathlib import Path
from typing import Optional, List, Union
import requests
from zipfile import ZipFile


from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag, PageElement

from bot.jw.bible import BaseBible
from bot.jw.language import JWLanguage


EPUB_PATH = Path('bible-epub')


class Epub(BaseBible):
    def __init__(
            self,
            language_code: str = None,
            booknum: Optional[int] = None,
            chapternum: Optional[int] = None,
            verses: Union[int, str, List[str], List[int]] = [],
            download=True,
    ):
        super().__init__(language_code, booknum, chapternum, verses)
        if download and not self.epub_file:
            self.download()
            self.unzip()

    def dirpath(self):
        path = EPUB_PATH / f'nwt_{self.language_meps_symbol}'
        if path.exists() and path.is_dir():
            return path
        else:
            for e in EPUB_PATH.glob(f'*_{self.language_meps_symbol}'):
                if e.is_dir:
                    return e
            else:
                raise FileNotFoundError(f'{EPUB_PATH}/*_{self.language_meps_symbol} not found')

    def download(self, pub='nwt'):
        api_url = "https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS"
        params = {
            "output": "json",
            "pub": pub,
            "fileformat": "EPUB",
            "alllangs": 0,
            "langwritten": self.language_meps_symbol,
            "txtCMSLang": self.language_meps_symbol,
            'isBible': '1'
        }
        p = "&".join([f'{key}={value}' for key, value in params.items()])
        print(f'{api_url}?{p}')
        r = requests.get(api_url, params)
        print(f'{r.status_code=!r}')
        if r.status_code == 200:
            pass
        elif r.status_code == 404 and pub != 'bi12':
            return self.download(pub='bi12')
        elif pub == 'bi12':
            raise ValueError(f'{self.language_meps_symbol!r} Bible unavailable')
        url = r.json()['files'][self.language_meps_symbol]['EPUB'][0]['file']['url']
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
        for file in EPUB_PATH.glob(f'*_{self.language_meps_symbol}.epub'):
            if file.is_file():
                return file

    @property
    def bookname(self) -> Optional[str]:
        file = self.dirpath() / f'OEBPS/bibleversenav{self.booknum}_1.xhtml'
        nav_soup = BeautifulSoup(file.read_bytes(), 'html.parser')
        return nav_soup.title.text

    def get_text(self) -> str:
        return f'<a href="{self.share_url(is_sign_language=False)}">{self.bookname} {self.chapternum}</a>\n' + self.verse_text()

    def verse_text(self) -> List[str]:
        versenav = self.dirpath() / f'OEBPS/bibleversenav{self.booknum}_{self.chapternum}.xhtml'
        nav_soup = BeautifulSoup(versenav.read_bytes(), 'html.parser')
        verses = []
        for versenum in self.verses:
            target_file, id_ = nav_soup.body.table.find('a', href=re.compile(
                f'xhtml#chapter{self.chapternum}_verse{versenum}')).get('href').split('#')
            target_file = (self.dirpath() / 'OEBPS') / target_file
            b = BeautifulSoup(target_file.read_bytes(), 'html.parser')
            span = b.find('span', id=id_)
            text = self._format_verse(span.next, versenum)
            verses.append(text)
        return ''.join(verses)

    def _format_verse(self, e: PageElement, versenum: int):
        text = f'<a href="{self.share_url(versenum, False)}">{versenum}</a> '
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
    from bot.secret import ADMIN
    from bot.secret import TOKEN
    from telegram import Bot

    epub = Epub(JWLanguage('S'), 43, 1, [1, 2])
    print('ESPAÑOL')
    print(epub.get_text())
    # print('"', epub.get_text(), '"')
    bot = Bot(TOKEN)
    # bot.send_message(chat_id=ADMIN, text=epub.get_text(), parse_mode='HTML', disable_web_page_preview=True)
    print('Enviado')
