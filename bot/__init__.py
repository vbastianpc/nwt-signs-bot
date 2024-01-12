from enum import StrEnum
from pathlib import Path


PATH_ROOT = Path(__file__).parent.parent

class MyCommand(StrEnum):
    START = 'start'
    SIGNLANGUAGE = 'signlanguage'
    BOTLANGUAGE = 'botlanguage'
    FEEDBACK = 'feedback'
    BIBLE = 'bible'
    HELP = 'help'
    BOOKNAMES = 'booknames'
    CANCEL = 'cancel'
    OK = 'ok'
    SETTINGS = 'settings'
    OVERLAY = 'overlay'
    OVERLAYINFO = 'overlayinfo'
    DELOGO = 'delogo'
    

class AdminCommand(StrEnum):
    ADD = 'add'
    BAN = 'ban'
    USERS = 'users'
    SETCOMMANDS = 'setcommands'
    NOTIFY = 'notify'
    BACKUP = 'backup'
    FLUSHLOGS = 'flushlogs'
    STATS = 'stats'
    TEST = 'test'
    RESET_CHAPTER = 'reset_chapter'
    ENV = 'env'
    RESTART = 'restart'
    GIT = 'git'
