from bot.database import SESSION
from bot.database.schemedb import Language
from bot.database.schemedb import BibleBook
from bot.database.schemedb import Chapter
from bot.database.schemedb import VideoMarker
from bot.database.schemedb import File
from bot.database.schemedb import File2User
from bot.database.schemedb import User
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


def modify_BookNamesAbbreviation_langcode_to_languageid():
    booknames_abb = db.get_bible_books()

    for book in booknames_abb:
        lang = db.get_language(code=book.language_id)
        book.language_id = lang.id
        SESSION.add(book)
    SESSION.commit()



if __name__ == '__main__':
    pass