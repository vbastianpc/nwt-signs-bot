from pathlib import Path
from subprocess import run
import shlex
import time
from typing import Dict
import json

from bot import get_logger
from bot.utils import safechars
from bot.database.schemedb import VideoMarker


logger = get_logger(__name__)


def split(inputvideo, marker: VideoMarker, height=None) -> Path:
    end = parse_time(marker.duration) - parse_time(marker.end_transition_duration)
    output = Path(safechars(marker.label) + ".mp4")
    cmd = (
        'ffmpeg -v warning -hide_banner -y '
        f'-ss {marker.start_time} '
        f'-i "{inputvideo}" '
        f'-t {end} ' + 
        ( f'-vf scale=-2:{height}' if height else '' ) + 
        f' -map_chapters -1 -metadata title="{marker.label}" -metadata comment=t.me/nwtsigns_bot '
        '-preset veryfast '
        f'"{output}"'
    )
    logger.info(cmd)
    run(shlex.split(cmd), capture_output=True)
    return output


def show_streams(video) -> Dict:
    console = run(
        shlex.split(f'ffprobe -v quiet -show_streams -print_format json -i "{video}"'),
        capture_output=True
    )
    streams = json.loads(console.stdout.decode())['streams']
    return streams[0]


def concatenate(inputvideos, outname=None, title_chapters=None, title=None) -> Path:
    intermediates = []
    metadata = ';FFMETADATA1\n'
    offset = 0
    metapath = Path('metadata.txt')
    output = Path((outname or ' - '.join([Path(i).stem for i in inputvideos])) + '.mp4')

    for i, video in enumerate(inputvideos):
        out = f'{time.time()}.ts'
        intermediates.append(out)
        ts = f'ffmpeg -v warning -hide_banner -y -i "{video}" -c copy "{out}"'
        run(shlex.split(ts))
        stream = show_streams(video)
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
    run(shlex.split(cmd), capture_output=True)
    for i in intermediates:
        Path(i).unlink()
    metapath.unlink()
    return output


def parse_time(stamptime) -> float:
    """Expects stamptime = "01:02:03.4567" or float or int """
    try:
        return float(stamptime)
    except ValueError:
        hours, minutes, seconds = stamptime.split(':')
        return int(hours)*60*60 + int(minutes)*60 + float(seconds)

def make_thumbnail(inputvideo: Path) -> Path:
    thumb = inputvideo.parent / (inputvideo.stem + '.jpg')
    run(
        shlex.split(f'ffmpeg -v error -stats -i "{inputvideo}" -vframes 1 -vf scale=240:-2 -q:v 2 "{thumb}"'),
        capture_output=True, check=True
    )
    return thumb
