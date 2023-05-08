import re
import requests
import json
from pathlib import Path

from bot.logs import get_logger


logger = get_logger(__name__)
DIR = Path(__file__).parent / 'fonts'
DIR.mkdir(exist_ok=True)
FFDIR = DIR / 'font-family.json'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
}

def weight_style(font_face):
    font_weight = re.search('font-weight:(\d+)', font_face.group(1))
    font_style = re.search('font-style:(\w+)', font_face.group(1))
    return (
         int(font_weight.group(1)) if font_weight else 0,
         font_style.group(1) if font_style else None
     )


def f1(font_face):
    font_weight, font_style = weight_style(font_face)
    if font_style != 'italic' and font_weight > 400:
        return True


def f2(font_face):
    _, font_style = weight_style(font_face)
    if font_style != 'italic':
        return True


def find_best_url_font(font_faces: list):
    font_faces = list(filter(f1, font_faces)) or list(
        filter(f2, font_faces)) or font_faces
    best = font_faces[0]
    attrs = best.group(1)
    urls = re.findall(r'url\("(.*?)"', attrs)
    urls = (
        list(filter(lambda x: x.endswith('.otf'), urls)) or
        list(filter(lambda x: x.endswith('.ttf'), urls)) or
        list(filter(lambda x: x.endswith('.woff'), urls))
    )
    return urls[0]


def fetch_fonts():
    css = requests.get(
        'https://wol.jw.org/assets/css/+2+17b206c9be641a997763d161730d8a9075df42b3.css',
        headers=HEADERS
    ).content.decode()
    data = dict()
    for match in re.finditer(r'\.jwac\.ms-(\w+),\.ms-\w+\{font-family:(\w+)', css):
        script, font_family = match.groups()
        font_faces = list(re.finditer(f'@font-face{{(font-family:{font_family};src:(.*?))}}', css))

        if not font_faces:
            # get alternative font_family
            font_family = re.search(f'\.sw,.jwac.ms-{script}+.bibleCitation .v{{font-family:([\w-]+)', css).group(1)
            font_faces = list(re.finditer(f'@font-face{{font-family:{font_family};src:(.*?);', css))

        data[script] = find_best_url_font(font_faces)
    json.dump(data, FFDIR.open('w'), indent=4)


def download_fonts():
    for url in json.load(FFDIR.open('r')).values():
        with open(DIR / Path(url).name, 'wb') as f:
            f.write(requests.get(url, headers=HEADERS).content)


def select_font(script):
    url = json.load(FFDIR.open('r'))[script]
    return Path(DIR) / Path(url).name


if __name__ == '__main__':
    logger.info('fetching fonts')
    # fetch_fonts()
    logger.info('downloading fonts')
    download_fonts()
    logger.info(select_font('ROMAN'))
