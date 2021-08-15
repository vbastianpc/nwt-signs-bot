from pathlib import Path
from os import PathLike
from subprocess import run
import logging
import requests
import shlex
import time
from typing import Dict
import json

from utils import safechars



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


NWT_PATH = Path('../video/download')
VERSES_PATH = Path('../video/verses')

NWT_PATH.mkdir(parents=True, exist_ok=True)
VERSES_PATH.mkdir(parents=True, exist_ok=True)

class Video:
    @classmethod
    def download(cls, url) -> PathLike:
        path = NWT_PATH / Path(url).name
        logger.info(f'response = requests.get({url})')
        logger.info(f'{path}')
        with open(path, "wb") as f:
            response = requests.get(url)
            f.write(response.content)
        return path

    @classmethod
    def split(cls, inputvideo, marker, height=None) -> PathLike:
        end = parse_time(marker['duration']) - parse_time(marker['endTransitionDuration'])
        output = VERSES_PATH / (safechars(marker["label"]) + ".mp4")
        cmd = (
            'ffmpeg -v warning -hide_banner -y '
            f'-ss {marker["startTime"]} '
            f'-i "{inputvideo}" '
            f'-t {end} ' + 
            ( f'-vf scale=-2:{height}' if height else '' ) + 
            f' -map_chapters -1 -metadata title="{marker["label"]}" -metadata comment=t.me/nwtsigns_bot '
            '-preset veryfast '
            f'"{output}"'
        )
        run(shlex.split(cmd), capture_output=True)
        return output

    @classmethod
    def concatenate(cls, inputvideos, outname=None, title_chapters=None, title=None) -> PathLike:
        intermediates = []
        metadata = ';FFMETADATA1\n'
        offset = 0
        metapath = NWT_PATH / 'metadata.txt'
        output = NWT_PATH / ((outname or ' - '.join([Path(i).stem for i in inputvideos])) + '.mp4')

        for i, video in enumerate(inputvideos):
            out = f'{time.time()}.ts'
            intermediates.append(out)
            ts = f'ffmpeg -v warning -hide_banner -y -i "{video}" -c copy "{out}"'
            run(shlex.split(ts))
            stream = cls.show_streams(video)
            metadata += (
                '[CHAPTER]\n'
                'TIMEBASE=1/1000\n'
                f'START={offset*1000}\n'
                f'END={(offset + float(stream["duration"]))*1000}\n'
                f'title={title_chapters[i] if title_chapters else Path(video).stem}\n'
            )
            offset += float(stream['duration'])
        
        concat = '|'.join(intermediates)
        metapath.write_text(metadata)
        cmd = (
            'ffmpeg -v warning -hide_banner -y '
            f'-i "concat:{concat}"  '
            f'-i "{metapath}" -map_metadata 1 '
            f'-metadata title="{title if title else output.stem}" '
            '-metadata comment=t.me/nwtsigns_bot '
            f'-c copy "{output}"' 
        )
        print(cmd)
        run(shlex.split(cmd), capture_output=True)
        for i in intermediates:
            Path(i).unlink()
        return output
    
    @staticmethod
    def show_streams(video) -> Dict:
        console = run(
            shlex.split(f'ffprobe -v quiet -show_streams -print_format json -i "{video}"'),
            capture_output=True
        )
        streams = json.loads(console.stdout.decode())['streams']
        return streams[0]


def parse_time(stamptime):
    """Expects stamptime = "01:02:03.4567" or float or int """
    try:
        return float(stamptime)
    except ValueError:
        hours, minutes, seconds = stamptime.split(':')
        return int(hours)*60*60 + int(minutes)*60 + float(seconds)
    