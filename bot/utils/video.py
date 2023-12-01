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

def split(marker: VideoMarker, overlay_text: str = None, script: str = None, with_delogo: bool = False) -> Path:
    end = parse_time(marker.duration) - parse_time(marker.end_transition_duration)
    output = Path(safechars(marker.label) + ".mp4")

    frame = Path(__file__).parent / 'frame.png'
    run(
        shlex.split(f'ffmpeg -y -ss {marker.start_time} -i "{marker.chapter.url}" -vf edgedetect -frames:v 1 -update 1 "{frame}"'),
        capture_output=True, check=True
    )
    image = Image.open(frame)
    if overlay_text and not with_delogo:
        x, y = coord_empty_space(image)
        vf = '-vf ' +  drawtext(overlay_text, x, y, 30 * image.height / 720, select_font(script))
    elif overlay_text and with_delogo:
        box = find_box(image)
        x, y = box[0] + 2, box[1] + 2
        dt = drawtext(overlay_text, x, y, 30 * image.height / 720, select_font(script))
        vf = '-vf ' + f"delogo=x={box[0]}:y={box[1]}:w={box[2] - box[0]}:h={box[3] - box[1]}:show=0,{dt}"
    else:
        vf = ''

    metapath = Path('metadata.txt')
    metapath.write_text(
        ';FFMETADATA1\n'
        f'title={marker.label}\n'
        f'comment=t.me/nwtsigns_bot\n'
        '[CHAPTER]\n'
        'TIMEBASE=1/1000\n'
        'START=0\n'
        f'END={parse_time(marker.duration) * 1000}\n'
        f'title="{marker.label}"\n',
        encoding='utf-8'
    )
    print(f'function: label={marker.label}')

    cmd = (
        f'ffmpeg -hide_banner -v warning -y -ss {marker.start_time} -i "{marker.chapter.url}" -i "{metapath}" '
        f'-map_metadata 1 -map_chapters 1 -t {end} -preset veryfast {vf} "{output}"'
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
    assert len(inputvideos) == len(title_chapters)
    output = Path((outname or ' - '.join([Path(i).stem for i in inputvideos])) + '.mp4')
    metadata = (
        ';FFMETADATA1\n'
        f'title={title if title else output.stem}\n'
        'comment=t.me/nwtsigns_bot\n'
    )

    metapath = Path('metadata.txt')
    intermediates = []
    offset = 0
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
        overlay_text: str,
        x: int,
        y: int,
        fontsize: float,
        fontfile: str,
    ) -> str:
    overlay_text = overlay_text.replace(':', r'\:')
    params = {
        'fontfile': fontfile,
        'text': overlay_text,
        'fontcolor': '0xD7D7D7', # '0xA2A2A2'
        'fontsize': fontsize,
        'x': x,
        'y': y
    }
    return '"drawtext=' + ":".join([f"{k}='{v}'" for k, v in params.items()]) + '"'


def coord_empty_space(image: Image.Image) -> tuple[int, int]:
    box = [10, 30, 160, 80] # horizontal box width=150, height=50
    for _ in range(300):
        if not np.array(image.crop(box)).any():
            y = box[1] + round(25 * image.height / 720)
            break
        box[1] += 1
        box[3] += 1
    else:
        raise StopIteration

    box2 = [10, 0, 11, 150] # vertical line width=1, height=150
    for _ in range(200):
        if np.array(image.crop(box2)).any():
            x = box2[0]
            break
        box2[0] += 1
        box2[2] += 1
    else:
        raise StopIteration
    return x, y


def find_box(image: Image.Image) -> list[int, int, int, int]:
    box = [0, 20, 1, 150] # vertical line width=1, height=150
    for _ in range(200):
        if np.array(image.crop(box)).any():
            x = box[0] # save x
            break
        box[0] += 1 # move ➡️ x left
        box[2] += 1 # move ➡ x right
    box = [0, 40, 300, 41] # horizontal rectangle width=300, height=1
    for _ in range(100):
        if np.array(image.crop(box)).any():
            y = box[1] # save y
            break
        box[1] += 1 # move ⬇ y top 
        box[3] += 1 # move ⬇ y bottom
    box = [x, y + 5, x + 50, y + 6]
    for _ in range(100):
        if not np.array(image.crop(box)).any():
            y1 = box[1]
            break
        box[1] += 1
        box[3] += 1
    box = [x, y + 5, x + 50, y1 - 5]
    for _ in range(600):
        if not np.array(image.crop(box)).any():
            x1 = box[0]
            break
        box[0] += 1
        box[2] += 1
    return [x - 2, y - 2, x1 + 2, y1 + 2] # a little bigger box

