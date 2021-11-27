from typing import Dict, Iterator, Optional, Tuple, List, Union
from pathlib import Path
import json

from ruamel.yaml import YAML
from telegram import BotCommand


STRINGS_PATH = Path(__file__).parent / 'strings'
yaml = YAML(typ='safe')

class TextGetter:
     def __init__(self, language_code):
          self.language_code = language_code
     
     def __call__(self, key) -> Union[str, dict]:
          p = STRINGS_PATH / f'{self.language_code}.yaml'
          if not p.exists():
               p = STRINGS_PATH / 'es.yaml'
          return yaml.load(p.read_text())[key]


def get_language(botlang: str) -> Dict:
     return TextGetter(botlang)('language')


def get_commands(botlang) -> List[BotCommand]:
     return [BotCommand(command, descr) for command, descr in TextGetter(botlang)('commands').items()]


def get_admin_commands(botlang) -> List[BotCommand]:
     return [BotCommand(command, descr) for command, descr in TextGetter(botlang)('admin_commands').items()]


def botlangs_vernacular() -> Iterator[Tuple[str, str]]:
     return ((p.stem, yaml.load(p.read_text())['language']['vernacular']) for p in STRINGS_PATH.glob('*.yaml'))


def botlangs() -> List[str]:
     return [p.stem for p in STRINGS_PATH.glob('*.yaml')]
