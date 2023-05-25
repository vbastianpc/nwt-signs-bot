from collections.abc import Iterator
from typing import Protocol
from pathlib import Path
from random import choice
import re

from ruamel.yaml import YAML
from telegram import BotCommand


STRINGS_PATH = Path(__file__).parent / 'strings'
DEFAULT_LANGUAGE = 'es'
DEFAULT_PATH = STRINGS_PATH / f'{DEFAULT_LANGUAGE}.yaml'
yaml = YAML(typ='safe')


class MyCallable(Protocol):
    def __call__(self, *args: str | int) -> str: ...

class Self:
    def __set_name__(self, owner, name):
        self.name = name # pylint: disable=attribute-defined-outside-init

    def __get__(self, obj, type=None) -> str | MyCallable: # pylint: disable=redefined-builtin
        p = STRINGS_PATH / f'{obj.language_code}.yaml'
        pt = r'{[ f.:<>\d]*}'
        try:
            value = yaml.load(p.read_text())[self.name]
        except (KeyError, FileNotFoundError):
            value = yaml.load(DEFAULT_PATH.read_text())[self.name]

        if isinstance(value, str):
            if re.search(pt, value):
                def f(*args: str | int):
                    return value.format(*args)
            else:
                return value

        elif isinstance(value, list):
            if any([re.search(pt, v) for v in value]):
                def f(*args: str | int):
                    return choice(value).format(*args)
            else:
                return choice(value)

        elif isinstance(value, dict):
            return value

        return f

    def __set__(self, obj, value) -> None:
        raise AttributeError("Cannot change the value")


class TextTranslator:
    language = Self()
    commands = Self()
    admin_commands = Self()
    barrier_to_entry = Self()
    wait = Self()
    step_1 = Self()
    step_2 = Self()
    step_3 = Self()
    start = Self()
    yes = Self()
    no = Self()
    enabled = Self()
    disabled = Self()
    book_not_found = Self()
    missing_chapter = Self()
    chapter_not_exists = Self()
    verse_not_exists = Self()
    verses_not_exists = Self()
    that_verse_no = Self()
    but_these_verses = Self()
    that_chapter_no = Self()
    but_these_chapters = Self()
    that_book_no = Self()
    but_these_books = Self()
    is_apocrypha = Self()
    not_language = Self()
    not_signlanguage = Self()
    choose_book = Self()
    choose_chapter = Self()
    choose_verse = Self()
    fetching_videomarkers = Self()
    downloading = Self()
    trimming = Self()
    sending = Self()
    help = Self()
    pro_tips = Self()
    overlay_info = Self()
    overlay_activated = Self()
    overlay_deactivated = Self()
    fallback = Self()
    current_settings = Self()
    menu_signlanguage = Self()
    ok_signlanguage_code = Self()
    choose_botlang = Self()
    ok_botlang = Self()
    books_fetch_botlang = Self()
    no_bible = Self()
    no_botlang_but = Self()
    feedback_1 = Self()
    feedback_2 = Self()
    feedback_3 = Self()
    stat = Self()
    stats = Self()
    waiting_list = Self()
    from_github = Self()
    introduced_himself = Self()
    db_summary = Self()
    wrong_notify = Self()
    notify = Self()
    notify_success = Self()
    notify_cancel = Self()
    logfile_notfound = Self()
    setcommands = Self()
    user_added = Self()
    warn_user = Self()
    user_banned = Self()
    user_stopped_bot = Self()
    checksum_touched = Self()
    checksum_failed = Self()


    def __init__(self, language_code) -> None:
        self.language_code = language_code


def get_language(botlang: str) -> dict:
    return TextTranslator(botlang).language


def get_commands(botlang) -> list[BotCommand]:
    return [BotCommand(command, descr) for command, descr in TextTranslator(botlang).commands.items()]


def get_admin_commands(botlang) -> list[BotCommand]:
    return [BotCommand(command, descr) for command, descr in TextTranslator(botlang).admin_commands.items()]


def botlangs_vernacular() -> Iterator[tuple[str, str]]:
    return ((p.stem, yaml.load(p.read_text())['language']['vernacular']) for p in STRINGS_PATH.glob('*.yaml'))


def botlangs() -> list[str]:
    return [p.stem for p in STRINGS_PATH.glob('*.yaml')]


if __name__ == '__main__':
    print(*map(lambda k: f'    {k} = Self()', yaml.load(DEFAULT_PATH.read_text()).keys()), sep='\n')