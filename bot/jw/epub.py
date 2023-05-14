import re
from pathlib import Path
from zipfile import ZipFile
import requests

from urllib.parse import urlunsplit
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from bot.jw import BiblePassage


EPUB_PATH = Path('bible-epub')

class BibleEpub(BiblePassage):
    def dirpath(self):
        path = EPUB_PATH / f'nwt_{self.language.meps_symbol}' # nwt_E
        if path.exists() and path.is_dir():
            return path
        else:
            raise FileNotFoundError(f'{path.absolute()} not found')

    def download(self, overwrite=False):
        if self.epub_file.exists() and not overwrite:
            return
        params = dict(
            output="json",
            pub='nwt',
            fileformat="EPUB",
            alllangs=0,
            langwritten=self.language.meps_symbol,
            txtCMSLang=self.language.meps_symbol,
            isBible='1'
        )
        url = urlunsplit(('https', 'b.jw-cdn.org', '/apis/pub-media/GETPUBMEDIALINKS', urlencode(params)))
        r = requests.get(url)
        print(f'{r.status_code=!r}')
        assert r.status_code == 200

        url = r.json()['files'][self.language.meps_symbol]['EPUB'][0]['file']['url']
        with requests.get(url, stream=True) as r:
            with open(self.epub_file, mode="wb") as f:
                for chunk in r.iter_content(chunk_size=128*1024):
                    f.write(chunk)
        return

    def unzip(self):
        directory_to_extract = Path(self.epub_file).parent / self.epub_file.stem
        directory_to_extract.mkdir(exist_ok=True)
        with ZipFile(self.epub_file, 'r') as zip_ref:
            zip_ref.extractall(directory_to_extract)

    @property
    def epub_file(self):
        for file in EPUB_PATH.glob(f'*_{self.language.meps_symbol}.epub'):
            if file.is_file():
                return file

    def get_text(self, fmt='HTML', head_url=True, versenum_url=True) -> str:
        return self.head(fmt, head_url) + '\n' + self.verse_texts(fmt, versenum_url)

    def head(self, fmt=None, with_url=False) -> str:
        c = self.citation()
        if fmt == None:
            return self.citation()
        url = self.url_share_jw()
        if fmt == 'HTML':
            text = "<strong>{}</strong>"
            text = text.format(f'<a href="{url}">{c}</a>' if with_url else c)
        elif fmt in ['Markdown', 'Obsidian']:
            text = f'[{c}]({url})' if with_url else c
        if fmt == 'Obsidian':
            original_verses = self.verses
            text = f'> [!BIBLE]+ {text} '
            internal_links = []
            for verse in original_verses:
                self.verses = verse
                internal_links.append(f'[[{self.citation()}|]]')
            self.verses = original_verses
            text += ' '.join(internal_links)
        return text

    def _get_target_file(self) -> Path:
        verse = self.verses[0] if self.verses else 1
        versenav = self.dirpath() / f'OEBPS/bibleversenav{self.book.number}_{self.chapternumber}.xhtml'
        nav_soup = BeautifulSoup(versenav.read_bytes(), 'html.parser')
        try:
            target_file = nav_soup.body.table \
                .find('a', href=re.compile(f'xhtml#chapter{self.chapternumber}_verse{verse}')) \
                .get('href').split('#')[0]
        except AttributeError as e:
            raise FileNotFoundError from e
        return (self.dirpath() / 'OEBPS') / target_file

    def verse_texts(self, fmt=None, with_url=False) -> str:
        # if fmt == None:
        #     nbsp = ' '
        #     emsp = '    '
        # elif fmt in ['HTML', 'Markdown', 'Obsidian']:
        #     nbsp = '&nbsp;'
        #     emsp = '&emsp;'
        # elif fmt == 'Markdown':
        #     nbsp = chr(160)
        #     ensp = chr(8194)
        #     emsp = chr(8195)
        nbsp = ' '
        emsp = '    '
        b = BeautifulSoup(self._get_target_file().read_text(encoding='utf-8'), 'html.parser')

        text = ''
        verses = self.verses
        for v in verses:
            self.verses = [v]
            if fmt is None:
                text_number = f'{v}'
            elif fmt == 'HTML':
                text_number = f'<a href="{self.url_share_jw()}">{v}</a>' if with_url else f'<strong>{v}</strong>'
            elif fmt in ['Markdown', 'Obsidian']:
                text_number = f'[{v}]({self.url_share_jw(v)})' if with_url else f'**{v}**'

            e = b.find('span', id=f'chapter{self.chapternumber}_verse{v}').next
            while True:
                if (e is None or
                (e.name == 'div' and 'groupFootnote' in e.get('class')) or
                (isinstance(e, Tag) and e.get('id', '').startswith('chapter'))
                ):
                    break # while

                if e.name == 'p':
                    if 'ss' in e.get('class'): # hebrew heading verse, ej: Sal 119:9
                        e = e.next_sibling
                        continue # while
                    text += '\n'
                    if 'sz' in e.get('class'): # prosa, salmos etc
                        text += 2*emsp if fmt in ['Markdown', 'Obsidian'] and text.endswith('\n') else emsp
                    elif 'sb' in e.get('class'): # standard paragraph
                        text += '\n' + emsp
                    elif 'sl' in e.get('class'): # starting new verse align to left en prosa
                        text += ''
                if isinstance(e, NavigableString):
                    e: NavigableString
                    try:
                        int(e)
                    except ValueError:
                        text += '' if e in ['\n', '\xa0'] else e.string.replace('\xa0', nbsp).replace('*', '')
                    else:
                        # ignore verses <strong><sup>2</sup></strong>
                        text += text_number
                e = e.next
        self.verses = verses
        if fmt == 'Obsidian':
            text = '> ' + text.replace('\n', '\n> ')
        elif fmt == None:
            text = text.replace('\n\n', '\n')

        def rstrip(text: str, strings: list):
            """Recursive rstrip"""
            new = text
            for s in strings:
                new = new.rstrip(s)
            return new if new == text else rstrip(new, strings)

        text = rstrip(text, [' ', '>', '&emsp;', '\n'])
        return text

if __name__ == '__main__':
    from telegram import Bot

    from bot.secret import TOKEN
    from bot.secret import ADMIN

    epub = BibleEpub.from_human('prov 27:9', 'es')    

    print(epub.get_text())

    bot = Bot(TOKEN)

    bot.send_message(ADMIN, epub.get_text('HTML'), parse_mode='HTML', disable_web_page_preview=True)

    print('end')