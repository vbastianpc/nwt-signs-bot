import os
from typing import Type

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