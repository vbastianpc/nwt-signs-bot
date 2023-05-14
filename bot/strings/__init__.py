from collections.abc import Iterator
from typing import Protocol
from pathlib import Path
from random import choice

from ruamel.yaml import YAML
from telegram import BotCommand


STRINGS_PATH = Path(__file__).parent / 'strings'
DEFAULT = STRINGS_PATH / 'es.yaml'
yaml = YAML(typ='safe')


class MyCallable(Protocol):
    def __call__(self, *args: str | int) -> str: ...

class Self:
    def __set_name__(self, owner, name):
        self.name = name # pylint: disable=attribute-defined-outside-init

    def __get__(self, obj, type=None) -> MyCallable: # pylint: disable=redefined-builtin
        p = STRINGS_PATH / f'{obj.language_code}.yaml'
        try:
            value = yaml.load(p.read_text())[self.name]
        except (KeyError, FileNotFoundError):
            value = yaml.load(DEFAULT.read_text())[self.name]
        if isinstance(value, str):
            def f(*args: str | int):
                return value.format(*args)
        elif isinstance(value, list):
            def f(*args: str | int):
                return choice(value).format(*args)
        elif isinstance(value, dict):
            def f(key=None) -> dict | str:
                return value[key] if key is not None else value
        return f

    def __set__(self, obj, value) -> None:
        raise AttributeError("Cannot change the value")


class TextGetter:
    language = Self()
    commands = Self()
    admin_commands = Self()

    barrier_to_entry = Self()
    wait = Self()
    welcome = Self()
    greetings = Self()
    yes = Self()
    no = Self()
    enable = Self()
    disable = Self()

    choose_signlang = Self()
    book_not_found = Self()
    missing_chapter = Self()
    chapter_not_exists = Self()
    verse_not_exists = Self()
    verses_not_exists = Self()
    not_language = Self()
    is_apocrypha = Self()
    unavailable_pubmedia = Self()
    optional_book = Self()
    optional_chapter = Self()
    optional_verse = Self()

    choose_chapter = Self()
    choose_verse = Self()

    empty_pubmedia = Self()

    downloading = Self()
    trimming = Self()
    splicing = Self()
    sending = Self()

    help = Self()
    protips = Self()

    current_settings = Self()
    menu_signlanguage = Self()
    ok_signlanguage_code = Self()
    choose_botlang = Self()
    ok_botlang = Self()
    bible_fetch_botlang = Self()

    overlay_description = Self()
    overlay_activated = Self()
    overlay_deactivated = Self()

    feedback_1 = Self()
    feedback_2 = Self()
    feedback_3 = Self()

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
    return TextGetter(botlang).language


def get_commands(botlang) -> list[BotCommand]:
    return [BotCommand(command, descr) for command, descr in TextGetter(botlang).commands().items()]


def get_admin_commands(botlang) -> list[BotCommand]:
    return [BotCommand(command, descr) for command, descr in TextGetter(botlang).admin_commands().items()]


def botlangs_vernacular() -> Iterator[tuple[str, str]]:
    return ((p.stem, yaml.load(p.read_text())['language']['vernacular']) for p in STRINGS_PATH.glob('*.yaml'))


def botlangs() -> list[str]:
    return [p.stem for p in STRINGS_PATH.glob('*.yaml')]
