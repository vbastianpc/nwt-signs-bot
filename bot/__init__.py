import os


TOKEN = os.getenv('TOKEN_NWT')
if TOKEN is None:
    raise Exception('You must define the environment variable TOKEN_NWT')

try:
    ADMIN = int(os.getenv('USER_ID_ADMIN'))
except TypeError:
    raise Exception('You must define the environment variable USER_ID_ADMIN')
except ValueError:
    raise Exception('Environment variable ADMIN must be a integer')

try:
    CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
except TypeError:
    raise Exception('You must define the environment variable CHANNEL_ID')
except ValueError:
    raise Exception('Environment variable CHANNEL_ID must be a integer')


class MyCommand:
    START = 'start'
    SIGNLANGUAGE = 'signlanguage'
    BOTLANGUAGE = 'botlanguage'
    INLINE = 'inline'
    FEEDBACK = 'feedback'
    HELP = 'help'
    BOOKNAMES = 'booknames'

class AdminCommand:
    AUTH = 'auth'
    DELETE = 'delete'
    USERS = 'users'
    ADMIN = 'admin'
    BACKUP = 'backup'
    TEST = 'test'
    NOTICE = 'notice'
    LOGS = 'logs'
    LOGFILE = 'logfile'
    SETCOMMANDS = 'setcommands'