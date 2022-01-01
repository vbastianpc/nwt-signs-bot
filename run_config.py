from telegram import Bot

from bot import ADMIN, TOKEN
from bot.booknames.booknames import add_booknames
from bot.database import report
from bot.database import localdatabase as db
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
            SESSION.commit()
        except:
            SESSION.rollback()
        i += 1
    print(f'There are {report.count_languages()} languages stored in the database')


if __name__ == '__main__':
    bot = Bot(TOKEN)
    msg = bot.send_message(chat_id=ADMIN, text='Preparing configuration...')
    add_all_languages()
    for lang_locale in ['en', 'es', 'vi']:
        add_booknames(lang_locale)
    msg = msg.edit_text(f'{msg.text}\nThere are {report.count_languages()} languages stored in the database')
    print(f'{msg.text!r}')
    member = bot.get_chat_member(chat_id=ADMIN, user_id=ADMIN)
    db.set_user(
        ADMIN,
        full_name=member.user.full_name,
        bot_lang=member.user.language_code,
        brother=True
    )
    msg.edit_text(f'{msg.text}\nUser {member.user.full_name} added to database.\nConfiguration succesful!')
    
