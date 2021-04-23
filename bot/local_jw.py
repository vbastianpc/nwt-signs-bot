import json
import os
import requests
import string
from subprocess import run
import shlex
import logging
import time

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


NWT_PATH = os.path.join('video', 'download')
VERSES_PATH = os.path.join('video', 'verses')
LOCAL_JW_DATA = 'jw_data.json'

os.makedirs(NWT_PATH, exist_ok=True)
os.makedirs(VERSES_PATH, exist_ok=True)

# TODO reescribir orientado a objetos. Definir clases
def download_video(url):
    filename = os.path.join(NWT_PATH, os.path.basename(url))
    logger.info(f'response = requests.get({url})')
    with open(filename, "wb") as file:
        response = requests.get(url)
        file.write(response.content)
    return filename


def create_local_jw(filename='', filesize=0):
    return {
        'filesize': filesize,
        'file': filename,
        'verses': {},
    }


def get_local_jw():
    try:
        with open(LOCAL_JW_DATA, 'r', encoding='utf-8') as f:
            all_local = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}
    else:
        return all_local


def get_entry_local_jw(booknum, bibleBookChapter, lang, label):
    all_local = get_local_jw()
    all_local.setdefault(lang, {})
    all_local[lang].setdefault(booknum, {})
    all_local[lang][booknum].setdefault(label, {})
    all_local[lang][booknum][label].setdefault(
        bibleBookChapter, create_local_jw())
    return all_local[lang][booknum][label][bibleBookChapter]


def save_local_jw(entry, booknum, bibleBookChapter, lang, label):
    all_local = get_local_jw()
    all_local.setdefault(lang, {})
    all_local[lang].setdefault(booknum, {})
    all_local[lang][booknum].setdefault(label, {})
    all_local[lang][booknum][label].setdefault(
        bibleBookChapter, create_local_jw())
    all_local[lang][booknum][label][bibleBookChapter] = entry
    with open(LOCAL_JW_DATA, 'w', encoding='utf-8') as f:
        json.dump(all_local, f, ensure_ascii=False, indent=2, sort_keys=True)


def split_video(inputvideo, marker, height=None):
    start, title = marker['startTime'], marker['label']
    duration, transition = marker['duration'], marker['endTransitionDuration']
    hd, md, sd, ht, mt, st = duration.split(':') + transition.split(':')
    end = int(hd)*60*60 + int(md)*60 + float(sd) - int(ht)*60*60 - int(mt)*60 - float(st)
    output = ''.join([x if (x.isalnum() or x in "._- ") else '_' for x in title])
    outdir = os.path.join(VERSES_PATH, output + '.mp4')
    opt = f'-vf scale=-2:{height}' if height else ''
    opt += ' -map_chapters -1 -metadata title="" -metadata comment=@nwtsigns_bot'
    cmd = f'ffmpeg -v warning -hide_banner -y -ss {start} -i "{inputvideo}" -t {end} {opt} "{outdir}"'
    try:
        run(shlex.split(cmd), capture_output=True)
    except:
        return None
    else:
        return outdir


def concatenate(inputvideos):
    intermediates = []
    for video in inputvideos:
        out = '{}.ts'.format(time.time())
        intermediates.append(out)
        ts = 'ffmpeg -v warning -hide_banner -y -i "{}" -c copy "{}"'.format(video, out)
        run(shlex.split(ts))
    output = os.path.dirname(inputvideos[0]) + '/' + ' - '.join([os.path.splitext(os.path.basename(i))[0] for i in inputvideos]) + '.mp4'
    concat = '|'.join(intermediates)
    cmd = 'ffmpeg -v warning -hide_banner -y -i "concat:{}" -c copy "{}"'.format(concat, output)
    run(shlex.split(cmd), capture_output=True)
    run(shlex.split('rm ' + ' '.join(intermediates)), capture_output=True)
    return output

