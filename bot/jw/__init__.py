from urllib.parse import urlunsplit, urlencode


# URL Principal. bookname, chapters, qualities, url videos, markers
URL_PUBMEDIA = 'https://pubmedia.jw-api.org/GETPUBMEDIALINKS?output=json&alllangs=0&langwritten={language_meps_symbol}&txtCMSLang={language_meps_symbol}&pub=nwt&booknum={booknum}&track={track}'

# Todos los lenguajes de señas (jw y wol), vernacular, name, lang_code
URL_LANGUAGES = 'https://data.jw-api.org/mediator/v1/languages/E/all'
# alternative https://www.jw.org/en/languages/

# solo wol: rsconf, locale, lib, iswolavailable, (vernacular, name, lang_code)
URL_LIBRARIES = 'https://wol.jw.org/es/wol/li/r4/lp-s'

# para obtener marcadores desde wol
URL_WOLBIBLE = 'https://wol.jw.org/{language_code}/wol/b/{rsconf}/{lib}/nwt/{booknum}/{chapter}'


# citas de biblia, solo si hay wol. No se ocupa
URL_CITATION = 'https://wol.jw.org/wol/api/v1/citation/{rsconf}/{lib}/bible/{startBook}/{startChapter}/{startVerse}/{endBook}/{endChapter}/{endVerse}?pub=nwtsty'

def SHARE_URL(language_meps_symbol, booknum, chapter, first_verse=0, last_verse=0, is_sign_language=True):
    scheme = 'https'
    netloc = 'www.jw.org'
    path = 'finder'
    query = dict(
        wtlocale=language_meps_symbol,
        prefer='lang',
        bible=f'{booknum:0=2}{chapter:0=3}{first_verse:0=3}' + ('' if first_verse == last_verse or last_verse == 0 else f'-{booknum:0=2}{chapter:0=3}{last_verse:0=3}'),
    )
    if is_sign_language:
        query.update(dict(pub="nwt"))
    return urlunsplit((scheme, netloc, path, urlencode(query), ''))


URL_WOL_DISCOVER = 'https://wol.jw.org/{language_code}/wol/b/{rsconf}/{lib}/nwt/{booknum}/{chapter}#v={booknum}:{chapter}:{first_verse}-{booknum}:{chapter}:{last_verse}'
# others
# https://www.jw.org/en/library/bible/study-bible/books/json/html/40024013-40024014
# https://www.jw.org/en/library/bible/json/

# https://www.jw.org/csg/biblioteca/biblia/nwt/libros/json/translations/
# https://www.jw.org/csg/biblioteca/biblia/nwt/libros/json/data/
# https://www.jw.org/csg/biblioteca/biblia/nwt/libros/json/html/
# https://www.jw.org/csg/biblioteca/biblia/nwt/libros/json/multimedia/

# data-wol_link_api_url=https://b.jw-cdn.org/apis/wol-link
# https://www.jw.org/csg/languages/
# data-bible_editions_api="/csg/biblioteca/biblia/json/"

# https://www.jw.org/download/?booknum=0&output=html&pub=nwt&fileformat=PDF%2CEPUB%2CJWPUB%2CRTF%2CTXT%2CBRL%2CBES%2CDAISY&alllangs=0&langwritten=SCH&txtCMSLang=SCH&isBible=1
# data-jsonurl="https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS?booknum=0&output=json&pub=nwt&fileformat=PDF%2CEPUB%2CJWPUB%2CRTF%2CTXT%2CBRL%2CBES%2CDAISY&alllangs=0&langwritten=SCH&txtCMSLang=SCH"
# https://wol.jw.org/wol/vidlink/r377/lp-sch?pub=nwt&langwritten=SCH&booknum=4&track=30&txtCMSLang=SCH&fileformat=mp4%2Cm4v&output=json
# https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS?track=30&output=json&alllangs=0&langwritten=SCH&pub=nwt&booknum=4
