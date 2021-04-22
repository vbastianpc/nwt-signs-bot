import json


USERS_FILE = 'users.json'


def get_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_users(users_id):
    with open(USERS_FILE, 'w') as f:
        json.dump(users_id, f, indent=2)


def add_user(user_id, name):
    users_id = get_users()
    users_id[user_id] = {'lang': 'SCH', 'quality': '480p', 'name': name}
    save_users(users_id)


def remove_user(user_id):
    users_id = get_users()
    try:
        users_id.pop(user_id)
    except KeyError:
        return False
    else:
        save_users(users_id)
        return True


def set_user(key):
    def func(user_id, value):
        users = get_users()
        users[str(user_id)][key] = value
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    return func


set_user_lang = set_user(key='lang')
set_user_quality = set_user(key='quality')


def get_user_data(key):
    def func(user_id):
        user = get_users().get(str(user_id), {})
        return user.get(key)
    return func


get_user_lang = get_user_data('lang')
get_user_quality = get_user_data('quality')
