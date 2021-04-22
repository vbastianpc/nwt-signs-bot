import os
import requests
import logging
import re

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_jw_data(booknum: int, lang):
    url = f'https://pubmedia.jw-api.org/GETPUBMEDIALINKS?output=json&alllangs=0&langwritten={lang}&txtCMSLang={lang}&pub=nwt&booknum={booknum}'
    return requests.get(url).json()


def get_url_files(jw_data, lang, label='480p'):
    urls = []
    for _, files in jw_data['files'][lang].items():
        if label:
            urls += [item['file']['url']
                     for item in files if item['label'] == label]
        else:
            urls += [item['file']['url'] for item in files]
    if urls:
        return urls
    else:
        return get_url_files(jw_data, lang, None)


def get_url_file(jw_data, bibleBookChapter, lang, label='480p'):
    return [url for url in get_url_files(jw_data, lang, label) if bibleBookChapter == bibleBookChapter_from_url(url)][0]

# DEPRECATED


def get_checksum(jw_data, bibleBookChapter, lang, label='480p'):
    chsum = []
    for _, files in jw_data['files'][lang].items():
        chsum += [item['file']['checksum']
                  for item in files if item['label'] == label]
    return chsum[0]


def get_filesize(jw_data, bibleBookChapter, lang, label='480p'):
    filesize = []
    for _, files in jw_data['files'][lang].items():
        filesize += [item['filesize']
                     for item in files if item['label'] == label and bibleBookChapter_from_url(item['file']['url']) == bibleBookChapter]
    return filesize[0]


def is_available(jw_data, bibleBookChapter, verses, lang, label='480p') -> bool:
    try:
        _ = get_url_file(jw_data, bibleBookChapter, lang, label)
        _ = [get_marker(jw_data, bibleBookChapter, verse, lang)
             for verse in verses]
    except IndexError:
        return False
    else:
        return True


def bibleBookChapter_from_url(url):
    try:
        bibleBookChapter = str(int(os.path.basename(url).split('_')[4]))
        #logger.info(f'{url} -> {bibleBookChapter}')
        return bibleBookChapter
    except:
        return None


def get_bibleBookChapters(jw_data, lang, label='480p'):
    """Obten todos los capítulos disponibles"""
    # Es más confiable obtener los números de capítulos a partir de url
    # jw_data['files'][lang][format]['file']['url'] y no de
    # jw_data['files'][lang][format]['markers']['bibleBookChapter']
    chapters = sorted({int(bibleBookChapter_from_url(url)) for url in get_url_files(
        jw_data, lang, label) if bibleBookChapter_from_url(url) is not None})
    return [str(chpt) for chpt in chapters]


def get_verseNumbers(jw_data, bibleBookChapter: str, lang):
    verses = sorted({int(mark['verseNumber'])
                     for mark in get_markers(jw_data, bibleBookChapter, lang)})
    return [str(verse) for verse in verses]


def get_labels(jw_data, lang):
    'labels = quality (240p|360p|480p|720p)'
    labels = set()
    for _, files in jw_data['files'][lang].items():
        labels.update([file['label'] for file in files])
    return sorted(labels)


def best_quality(jw_data, lang):
    return get_labels(jw_data, lang)[-1]


def get_marker(jw_data, bibleBookChapter: str, verse: str, lang):
    markers = [filemark for filemark in get_markers(jw_data, bibleBookChapter, lang)
               if str(filemark['verseNumber']) == verse]
    return markers[0]


def get_markers(jw_data, bibleBookChapter: str, lang):
    markers = []
    for _, files in jw_data['files'][lang].items():
        for file in files:
            if file['markers'] is None:
                continue
            if bibleBookChapter_from_url(file['file']['url']) != bibleBookChapter:
                continue
            # logger.info(
            #     f"{os.path.basename(file['file']['url'])} es {bibleBookChapter}")
            markers += [filemark for filemark in file['markers']['markers']]
    # logger.info([mark['label'] for mark in markers])
    return markers


def get_title(jw_data, bibleBookChapter: str, lang):
    titles = []
    for _, files in jw_data['files'][lang].items():
        for file in files:
            if bibleBookChapter_from_url(file['file']['url']) != bibleBookChapter:
                titles.append(file['title'])
    return titles[-1]


def _strip_html_tags(text): return re.compile(r'<[^>]+>').sub('', text).strip()


def get_signs_languages():
    url = 'https://data.jw-api.org/mediator/v1/languages/S/web'
    data = requests.get(url).json()
    return {lang['code']: _strip_html_tags(
        lang['name']) for lang in data['languages'] if lang['isSignLanguage']}
