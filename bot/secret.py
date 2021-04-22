import json

try:
    with open('SECRETS.json', 'r') as f:
        secrets = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    secrets = {}

TOKEN = secrets.get('TOKEN')
ADMIN = secrets.get('ADMIN')
CHANNEL_ID = secrets.get('CHANNEL_ID')
