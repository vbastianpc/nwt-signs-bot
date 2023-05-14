
from typing import Final
from urllib.parse import urlunsplit
from urllib.parse import urlencode
from urllib.parse import unquote

from bot.logs import get_logger
from bot.jw import BaseBible


logger = get_logger(__name__)


class Domain:
    JW : Final[str] = 'www.jw.org'
    PUBMEDIA_JWAPI : Final[str] = 'pubmedia.jw-api.org'
    WOL : Final[str] = 'wol.jw.org'
    DATA_JWAPI : Final[str] = 'data.jw-api.org'
    JW_CDN : Final[str] = 'b.jw-cdn.org'


class BiblePassage(BaseBible):
    def url_pubmedia(self, all_chapters=True) -> str:
        """API JSON for sign languages get markers
        https://pubmedia.jw-api.org/GETPUBMEDIALINKS?output=json&alllangs=0&langwritten=ASL&txtCMSLang=ASL&pub=nwt&booknum=21&track=11
        """
        query = dict(
            output='json',
            alllangs=0,
            langwritten=self.book.edition.language.meps_symbol,
            txtCMSLang=self.book.edition.language.meps_symbol,
            pub=self.book.edition.symbol,
            booknum=self.book.number,
        )
        if self.chapternumber is not None and not all_chapters:
            query['track'] = self.chapternumber
        return urlunsplit((
            'https',
            'pubmedia.jw-api.org',
            'GETPUBMEDIALINKS',
            urlencode(query),
            None
        ))

    # Todos los lenguajes de señas (jw y wol), vernacular, name, lang_code
    def url_languages(self, domain : str = Domain.DATA_JWAPI):
        """API JSON get languages
        'https://data.jw-api.org/mediator/v1/languages/E/all'
        'https://www.jw.org/en/languages/'
        """
        if domain == Domain.DATA_JWAPI:
            return f'https://data.jw-api.org/mediator/v1/languages/{self.book.edition.language.meps_symbol}/all'
        elif domain == Domain.JW:
            return f'https://www.jw.org/{self.book.edition.language.code}/languages/'
        else:
            raise ValueError

    def url_wol_libraries(self):
        """WOL human url to get rsconf, locale, lib
        'https://wol.jw.org/en/wol/li/r1/lp-e'
        """
        l = self.book.edition.language
        return f'https://wol.jw.org/{l.code}/wol/li/{l.rsconf}/{l.lib}'

    def url_citation(self):
        """API JSON get bible citation. Example: "Ecclesiastes 11:9, 10"
        'https://wol.jw.org/wol/api/v1/citation/r266/lp-asl/bible/21/11/9/21/11/10?pub=nwt'
        """
        assert self.chapternumber is not None
        assert self.verses is not None and self.verses != []
        assert self.book.edition.language.rsconf is not None
        assert self.book.edition.language.lib is not None
        return (
            'https://wol.jw.org/wol/api/v1/citation'
            f'/{self.book.edition.language.rsconf}/{self.book.edition.language.lib}/bible'
            f'/{self.book.number}/{self.chapternumber}/{self.verses[0]}'
            f'/{self.book.number}/{self.chapternumber}/{self.verses[-1]}'
            f'?pub={self.book.edition.symbol}'
        )

    def url_share_jw(self, suppress_app_links=False):
        """Link open JWL, JWSL or browser.

        if suppress_app_links = True enforce open in browser on apple devices. Not always. 
        Reference: apple:   https://www.jw.org/.well-known/apple-app-site-association
                   android: https://www.jw.org/.well-known/assetlinks.json
                   windows: https://www.jw.org/.well-known/windows-app-web-link

        'https://www.jw.org/finder?wtlocale=E&prefer=lang&bible=21011009-21011010&pub=nwtsty'
        """
        if not self.chapternumber:
            bible_value = self.book.number
        else:
            assert self.verses is not None and self.verses != []
            bible_value = f'{self.book.number:0=2}{self.chapternumber:0=3}{self.verses[0]:0=3}'
            if len(self.verses) > 1:
                bible_value += f'-{self.book.number:0=2}{self.chapternumber:0=3}{self.verses[-1]:0=3}'
        query = dict(
            wtlocale=self.book.edition.language.meps_symbol,
            prefer='lang',
            bible=bible_value,
            pub=self.book.edition.symbol    
        )
        return urlunsplit((
            'https',
            'www.jw.org',
            'finder',
            urlencode(query),
            'suppress_app_links' if suppress_app_links else None
        ))

    def url_book_content(self, suppress_app_links=False) -> str:
        """Book content. Not working in sign languages
        'https://www.jw.org/finder?wtlocale=ASL&prefer=lang&docid=1001070525'
        """
        q = dict(
            wtlocale=self.book.edition.language.meps_symbol,
            prefer='lang',
            docid=1001070504 + self.book.number
        )
        return urlunsplit(('https', 'www.jw.org', 'finder', urlencode(q), 'suppress_app_links' if suppress_app_links else None))
   
    def url_bible_wol(self):
        """WOL human url
        'https://wol.jw.org/ASL/wol/b/r266/lp-asl/nwt/21/11'
        """
        return urlunsplit((
            'https',
            'wol.jw.org',
            f'/{self.book.edition.language.meps_symbol}/wol/b/{self.book.edition.language.rsconf}'
            f'/{self.book.edition.language.lib}/{self.book.edition.symbol}/{self.book.number}/{self.chapternumber}',
            None,
            None
        ))

    def url_bible_wol_discover(self):
        """Similar bible_wol, but select specific verses
        'https://wol.jw.org/ase/wol/b/r266/lp-asl/nwt/21/11#study=discover&v=21:11:9-21:11:10'
        """
        assert self.chapternumber

        fragment = dict(study='discover')
        if self.verses:
            v = f'{self.book.number}:{self.chapternumber}:{self.verses[0]}'
            if len(self.verses) > 1:
                v = v + f'-{self.book.number}:{self.chapternumber}:{self.verses[-1]}'
            fragment.update({'v': v})
        l = self.book.edition.language
        return urlunsplit((
            'https',
            'wol.jw.org',
            f'/{l.code}/wol/b/{l.rsconf}/{l.lib}/{self.book.edition.symbol}'
            f'/{self.book.number}/{self.chapternumber}',
            None,
            unquote(urlencode(fragment))
        ))


# others
# https://www.jw.org/en/library/bible/study-bible/books/json/html/40024013-40024014
# https://www.jw.org/en/library/bible/json/

# https://www.jw.org/csg/biblioteca/biblia/nwt/libros/json/translations/
# https://www.jw.org/csg/biblioteca/biblia/nwt/libros/json/data/
# https://www.jw.org/csg/biblioteca/biblia/nwt/libros/json/html/
# https://www.jw.org/csg/biblioteca/biblia/nwt/libros/json/multimedia/

# data-wol_link_api_url=https://b.jw-cdn.org/apis/wol-link
# data-bible_editions_api="/csg/biblioteca/biblia/json/"

# https://www.jw.org/download/?booknum=0&output=html&pub=nwt&fileformat=PDF%2CEPUB%2CJWPUB%2CRTF%2CTXT%2CBRL%2CBES%2CDAISY&alllangs=0&langwritten=SCH&txtCMSLang=SCH&isBible=1
# data-jsonurl="https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS?booknum=0&output=json&pub=nwt&fileformat=PDF%2CEPUB%2CJWPUB%2CRTF%2CTXT%2CBRL%2CBES%2CDAISY&alllangs=0&langwritten=SCH&txtCMSLang=SCH"
# https://wol.jw.org/wol/vidlink/r377/lp-sch?pub=nwt&langwritten=SCH&booknum=4&track=30&txtCMSLang=SCH&fileformat=mp4%2Cm4v&output=json
# https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS?track=30&output=json&alllangs=0&langwritten=SCH&pub=nwt&booknum=4

if __name__ == '__main__':



    print('end')
