from bot.database import SESSION
from bot.database.schema import Language
from bot.database import localdatabase as db


def modify_user_botlang_to_botlangid():
    users = db.get_users()

    for user in users:
        bot_lang_code = user.bot_language_id
        lang = SESSION.query(Language).filter(
            Language.code == bot_lang_code
        ).one_or_none()
        user.bot_language_id = lang.id
        SESSION.add(user)
    SESSION.commit()



if __name__ == '__main__':
    pass