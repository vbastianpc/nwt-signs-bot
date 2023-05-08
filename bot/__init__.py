import os
import logging
from datetime import datetime
import pytz

class MyCommand:
    START = 'start'
    SIGNLANGUAGE = 'signlanguage'
    BOTLANGUAGE = 'botlanguage'
    INLINE = 'inline'
    FEEDBACK = 'feedback'
    HELP = 'help'
    BOOKNAMES = 'booknames'
    CANCEL = 'cancel'
    OK = 'ok'
    SETTINGS = 'settings'
    OVERLAY = 'overlay'

class AdminCommand:
    ADD = 'add'
    BAN = 'ban'
    USERS = 'users'
    SETCOMMANDS = 'setcommands'
    NOTIFY = 'notify'
    BACKUP = 'backup'
    LOGS = 'logs'
    LOGFILE = 'logfile'
    STATS = 'stats'
    TEST = 'test'
    RESET_CHAPTER = 'reset_chapter'
