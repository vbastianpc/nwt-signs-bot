import json
from typing import List, Dict, Optional


USERS_FILE = 'users.json'


class UserController:

    def __init__(self, telegram_id):
        self.telegram_id = telegram_id

    def quality(self, telegram_id: int = None):
        telegram_id = telegram_id or self.telegram_id
        user = self.get_user(telegram_id)
        return user['quality']

    def lang(self, telegram_id: int = None):
        telegram_id = telegram_id or self.telegram_id
        user = self.get_user(telegram_id)
        return user['lang']

    @classmethod
    def add_user(cls, telegram_id: int, name: str, lang='SCH', quality='720p'):
        users = [user for user in cls.read_users() if user['telegram_id'] != telegram_id] # avoid duplicate users
        users.append(
            {
                'telegram_id': telegram_id,
                'name': name,
                'lang': lang,
                'quality': quality,
            }
        )
        cls._save(users)
    
    @classmethod
    def remove_user(cls, telegram_id: int):
        if telegram_id in cls.get_users_id():
            users = [user for user in cls.read_users() if user['telegram_id'] != telegram_id]
            cls._save(users)
            return True

    @staticmethod
    def read_users() -> List[Optional[Dict]]:
        try:
            return json.load(open(USERS_FILE, 'r'))
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    @classmethod
    def get_user(cls, telegram_id: int) -> Dict:
        for user in cls.read_users():
            if user['telegram_id'] == telegram_id:
                return user
        raise Exception(f'No user {telegram_id} found.')

    @classmethod
    def get_users_id(cls) -> List[int]:
        users = cls.read_users()
        return [user['telegram_id'] for user in users]
    
    @classmethod
    def get_users_name_id(cls):
        result = []
        for user in cls.read_users():
            result.append((user['name'], user['telegram_id']))
        return result
    
    @classmethod
    def pretty_users(cls):
        users = []
        for u in cls.read_users():
            users.append((f'[{u["name"]}](tg://user?id={u["telegram_id"]}) {u["lang"]} {u["quality"]} `{u["telegram_id"]}`'))
        return users

    @classmethod
    def set_user(cls, telegram_id: int, lang='', quality='') -> None:
        user = cls.get_user(telegram_id)
        user['lang'] = lang or user['lang']
        user['quality'] = quality or user['quality']
        users = [user if u['telegram_id'] == telegram_id else u for u in cls.read_users()]
        cls._save(users)

    @staticmethod
    def _save(users: List[Dict]) -> None:
        json.dump(
            users,
            open(USERS_FILE, 'w', encoding='utf-8'),
            indent=2,
            ensure_ascii=False
        )

