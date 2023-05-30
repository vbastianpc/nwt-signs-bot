from pathlib import Path
from subprocess import run
import shlex
import time
import json

import numpy as np
from PIL import Image

from bot.logs import get_logger
from bot.utils import safechars
from bot.utils.fonts import select_font
from bot.database.schema import VideoMarker


logger = get_logger(__name__)

def split(marker: VideoMarker, overlay_text: str = None, script: str = None) -> Path:
    end = parse_time(marker.duration) - parse_time(marker.end_transition_duration)
    output = Path(safechars(marker.label) + ".mp4")
    if overlay_text:
        logger.info('Add overlay to ffmpeg')
    cmd = (
        'ffmpeg -hide_banner -v warning -y '
        f'-ss {marker.start_time} '
        f'-i "{marker.chapter.url}" '
        f'-t {end} '
        f' -map_chapters -1 -metadata title="{marker.label}" -metadata comment=t.me/nwtsigns_bot '
        '-preset veryfast ' + drawtext(marker.chapter.url, overlay_text, script, marker.start_time) +
        f' "{output}"'
    )
    logger.info(cmd)
    run(shlex.split(cmd), capture_output=True, check=True)
    return output


def show_streams(video) -> dict[str, str | int]:
    console = run(
        shlex.split(f'ffprobe -v quiet -show_streams -print_format json -i "{video}"'),
        capture_output=True,
        check=True
    )
    streams = json.loads(console.stdout.decode())['streams']
    return streams[0]


def concatenate(inputvideos: list[Path], outname: str=None, title_chapters: list[str]=None, title:str=None) -> Path:
    intermediates = []
    metadata = ';FFMETADATA1\n'
    offset = 0
    metapath = Path('metadata.txt')
    output = Path((outname or ' - '.join([Path(i).stem for i in inputvideos])) + '.mp4')

    assert len(inputvideos) == len(title_chapters)
    for i, video in enumerate(inputvideos):
        out = f'{time.time()}.ts'
        intermediates.append(out)
        ts = f'ffmpeg -v warning -hide_banner -y -i "{video}" -c copy "{out}"'
        run(shlex.split(ts),capture_output=True , check=True)
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
    metapath.write_text(metadata, encoding='utf-8')
    cmd = (
        'ffmpeg -v warning -hide_banner -y '
        f'-i "concat:{concat}"  '
        f'-i "{metapath}" -map_metadata 1 '
        f'-metadata title="{title if title else output.stem}" '
        '-metadata comment=t.me/nwtsigns_bot '
        f'-c copy "{output}"' 
    )
    run(shlex.split(cmd), capture_output=True, check=True)
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

def make_thumbnail(inputvideo: Path, name=None) -> Path:
    thumb = inputvideo.parent / ((name or inputvideo.stem) + '.jpg')
    run(
        shlex.split(f'ffmpeg -v error -stats -y -i "{inputvideo}" -vframes 1 -vf scale=320:-2 -q:v 2 "{thumb}"'),
        capture_output=True, check=True
    )
    return thumb


def drawtext(
        inputvideo: str,
        overlay_text: str | None = None,
        script: str = None,
        start_time: int = 0
    ) -> str:
    if not overlay_text:
        return ''
    overlay_text = overlay_text.replace(':', r'\:')
    x, y, height = coord(inputvideo, start_time)
    params = {
        'fontfile': f"'{select_font(script)}'",
        'text': f"'{overlay_text}'",
        'fontcolor': '0xD7D7D7', # '0xA2A2A2'
        'fontsize': 30 * height / 720, # if r720P else 22,
        'x': x,
        'y': y
    }

    return '-vf drawtext="' + ':'.join([f"{k}={v}" for k, v in params.items()]) + '"'


def coord(inputvideo: str, start_time: float = 0.0) -> tuple[int, int]:
    frame = Path(__file__).parent / 'frame.png'
    run(
        shlex.split(f'ffmpeg -y -ss {start_time} -i "{inputvideo}" -vf edgedetect -frames:v 1 -update 1 "{frame}"'),
        capture_output=True, check=True
    )
    image = Image.open(frame) # already mode L, grayscale because -vf edgedetect
    # frame.unlink()
    box = [0, 30, 150, 80] # horizontal box width=150, height=50
    for _ in range(300):
        if not np.array(image.crop(box)).any():
            y = box[1] + round(25 * image.height / 720)
            break
        box[1] += 1
        box[3] += 1

    box2 = [0, 0, 1, 150] # vertical line width=1, height=150
    for _ in range(200):
        if np.array(image.crop(box2)).any():
            x = box2[0]
            break
        box2[0] += 1
        box2[2] += 1
    return x, y, image.height


# 720p
# image.crop((0, 67, 150, 68)).convert('L').filter(ImageFilter.FIND_EDGES)
# fontsize=32
# fontcolor=0xD7D7D7
#     Normal: x=93 y=107
#     Con letras hebreas: x=93 y=160
# 480p
# image.crop((0, 62, 150, 63)).convert('L').filter(ImageFilter.FIND_EDGES)
# fontsize=22
# fontcolor=0xA2A2A2
# x=65 y=90
