from bot.booknames.booknames import add_booknames
from bot.database import report as db
from bot.database.schemedb import Language
from bot.database import SESSION
from bot.jw.jwlanguage import JWLanguage



def add_all_languages():
    jwlanguage = JWLanguage()
    i = 1
    for lang in jwlanguage.all_langs:
        jwlanguage.code = lang['code']
        SESSION.add(
            Language(
                code=lang['code'],
                locale=lang['locale'],
                name=lang['name'],
                vernacular=lang['vernacular'],
                rsconf=jwlanguage.rsconf,
                lib=jwlanguage.lib,
                is_sign_lang=lang['isSignLanguage']
            )
        )
        try:
            SESSION.flush()
        except:
            SESSION.rollback()
        print(i)
        i += 1
    SESSION.commit()
    print(f'There are {db.count_languages()} languages stored in the database')


if __name__ == '__main__':
    # add_all_languages()
    print('Estoy en run_config.py', __name__)
    list(map(add_booknames, ['vi', 'en', 'fr', 'es']))
