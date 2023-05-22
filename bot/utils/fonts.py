import re
import json
from pathlib import Path

from bot.utils.browser import browser
from bot.logs import get_logger


logger = get_logger(__name__)
DIR = Path(__file__).parent / 'fonts'
DIR.mkdir(exist_ok=True)
FFDIR = DIR / 'font-family.json'


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
    wol = browser.open('https://wol.jw.org/en/wol/h/r1/lp-e')
    href = wol.soup.find('link', rel='stylesheet', href=re.compile(r'^/assets/css/\+2.*\.css')).get('href')
    css = browser.open(
        # 'https://wol.jw.org/assets/css/+2+cac2f578122dabb5cc955c02ab51b708b49077e6.css',
        'https://wol.jw.org' + href, translate_url=False
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
            f.write(browser.open(url, translate_url=False).content)


def select_font(script):
    url = json.load(FFDIR.open('r'))[script]
    return Path(DIR) / Path(url).name
