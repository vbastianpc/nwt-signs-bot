import os
from pathlib import Path
import json

from bot.models.jwpubmedia import JWInfo


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


def code_sign_languages():
    sign_languages = JWInfo().signs_languages
    return [sign_language['code'] for sign_language in sign_languages]


CODE_SIGN_LANGS = code_sign_languages()
