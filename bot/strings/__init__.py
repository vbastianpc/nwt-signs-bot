from typing import Iterator, Optional, Tuple, List
from pathlib import Path
import json

from ruamel.yaml import YAML
from telegram import BotCommand


STRINGS_PATH = Path(__file__).parent / 'strings'
yaml = YAML(typ='safe')

def botlangs_vernacular() -> Iterator[Tuple[str, str]]:
     return ((p.stem, yaml.load(p.read_text())['language']['vernacular']) for p in STRINGS_PATH.glob('*.yaml'))


def botlangs() -> List[str]:
     return [p.stem for p in STRINGS_PATH.glob('*.yaml')]


def get_commands(botlang) -> List[BotCommand]:
     p = STRINGS_PATH / f'{botlang}.yaml'
     if not p.exists():
          p = STRINGS_PATH / 'es.yaml'
     return [BotCommand(command, descr) for command, descr in yaml.load(p.read_text())['commands'].items()]

def get_admin_commands(botlang) -> List[BotCommand]:
     p = STRINGS_PATH / f'{botlang}.yaml'
     if not p.exists():
          p = STRINGS_PATH / 'es.yaml'
     return [BotCommand(command, descr) for command, descr in yaml.load(p.read_text())['admin_commands'].items()]
