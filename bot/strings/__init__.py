from typing import Dict, Iterator, Tuple, List, Union
from pathlib import Path

from ruamel.yaml import YAML
from telegram import BotCommand


STRINGS_PATH = Path(__file__).parent / 'strings'
DEFAULT = STRINGS_PATH / 'es.yaml'
yaml = YAML(typ='safe')


class Self:
     def __set_name__(self, owner, name):
          self.name = name
     
     def __get__(self, obj, type=None) -> Union[str, Dict]:
          p = STRINGS_PATH / f'{obj.language_code}.yaml'
          try:
               return yaml.load(p.read_text())[self.name]
          except (KeyError, FileNotFoundError):
               p = DEFAULT
               return yaml.load(p.read_text())[self.name]
     
     def __set__(self, obj, value) -> None:
          raise AttributeError("Cannot change the value")

class TextGetter:
     language = Self()
     commands = Self()
     admin_commands = Self()
     choose_signlang = Self()
     book_not_found = Self()
     unavailable = Self()
     optional_book = Self()
     optional_chapter = Self()
     optional_verse = Self()
     choose_chapter = Self()
     choose_verse = Self()
     downloading = Self()
     trimming = Self()
     splicing = Self()
     sending = Self()
     barrier_to_entry = Self()
     greetings = Self()
     wait = Self()
     help = Self()
     show_settings = Self()
     menu_signlanguage = Self()
     wrong_signlanguage_code = Self()
     ok_signlanguage_code = Self()
     choose_botlang = Self()
     wrong_botlang = Self()
     ok_new_botlang = Self()
     ok_botlang = Self()
     feedback_1 = Self()
     feedback_2 = Self()
     feedback_3 = Self()
     db_summary = Self()
     wrong_notify = Self()
     waiting_list = Self()
     from_github = Self()
     introduced_himself = Self()
     notify = Self()
     notify_success = Self()
     notify_cancel = Self()
     logfile_notfound = Self()
     setcommands = Self()
     user_added = Self()
     warn_user = Self()
     user_banned = Self()
     user_stopped_bot = Self()


     def __init__(self, language_code) -> None:
          self.language_code = language_code


def get_language(botlang: str) -> Dict:
     return TextGetter(botlang).language


def get_commands(botlang) -> List[BotCommand]:
     return [BotCommand(command, descr) for command, descr in TextGetter(botlang).commands.items()]


def get_admin_commands(botlang) -> List[BotCommand]:
     return [BotCommand(command, descr) for command, descr in TextGetter(botlang).admin_commands.items()]


def botlangs_vernacular() -> Iterator[Tuple[str, str]]:
     return ((p.stem, yaml.load(p.read_text())['language']['vernacular']) for p in STRINGS_PATH.glob('*.yaml'))


def botlangs() -> List[str]:
     return [p.stem for p in STRINGS_PATH.glob('*.yaml')]
