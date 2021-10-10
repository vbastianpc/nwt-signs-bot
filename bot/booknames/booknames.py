import logging

from bot.utils.browser import LazyBrowser
from bot.jw.jwlanguage import JWLanguage
from bot.database import SESSION
from bot.database.schemedb import BookNamesAbbreviation


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


browser = LazyBrowser()
lang = JWLanguage()

def add_booknames(lang_locale):
    lang.locale = lang_locale
    url = f'https://wol.jw.org/wol/finder?pub=nwt&wtlocale={lang.code}'
    browser.open(url)

    booklinks = browser.page.find_all('a', class_='bookLink')
    for booklink in booklinks:
        SESSION.add(
            BookNamesAbbreviation(
                lang_locale=lang_locale,
                booknum=int(booklink.get('data-bookid')),
                full_name=booklink.find('span', class_='title ellipsized name').text.strip('.'),
                long_abbr_name=booklink.find('span', class_='title ellipsized abbreviation').text.strip('.'),
                abbr_name=booklink.find('span', class_='title ellipsized official').text.strip('.'),
            )
        )
        try:
            SESSION.flush()
        except:
            SESSION.rollback()
    SESSION.commit()
    print(f'{lang_locale!r} bible booknames added')