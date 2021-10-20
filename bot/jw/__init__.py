

# URL Principal. bookname, chapters, qualities, url videos, markers
URL_PUBMEDIA = 'https://pubmedia.jw-api.org/GETPUBMEDIALINKS?output=json&alllangs=0&langwritten={lang_code}&txtCMSLang={lang_code}&pub=nwt&booknum={booknum}&track={track}'

# Todos los lenguajes de señas (jw y wol), vernacular, name, lang_code
URL_LANGUAGES = 'https://data.jw-api.org/mediator/v1/languages/S/all'

# solo wol: rsconf, locale, lib, iswolavailable, (vernacular, name, lang_code)
URL_LIBRARIES = 'https://wol.jw.org/es/wol/li/r4/lp-s'

# para obtener marcadores
URL_WOLBIBLE = 'https://wol.jw.org/{locale}/wol/b/{rsconf}/{lib}/nwt/{booknum}/{chapter}'

# citas de biblia, solo si hay wol. No se ocupa
URL_CITATION = 'https://wol.jw.org/wol/api/v1/citation/{rsconf}/{lib}/bible/{startBook}/{startChapter}/{startVerse}/{endBook}/{endChapter}/{endVerse}?pub=nwtst'


# https://wol.jw.org/wol/vidlink/r377/lp-sch?pub=nwt&langwritten=SCH&booknum=4&track=30&txtCMSLang=SCH&fileformat=mp4%2Cm4v&output=json
# https://b.jw-cdn.org/apis/pub-media/GETPUBMEDIALINKS?track=30&output=json&alllangs=0&langwritten=SCH&pub=nwt&booknum=4
