from typing import List, Dict, Optional
import requests

from bot.utils.browser import LazyBrowser
from bot.utils.models import LazyProperty
from bot.jw import URL_LANGUAGES
from bot.jw import URL_LIBRARIES
from bot import get_logger


logger = get_logger(__name__)


class JWLanguage:
    browser = LazyBrowser()

    def __init__(self, code=None, locale=None):
        if code and locale:
            raise TypeError('code and locale are mutually exclusive arguments')
        self._code = code
        self._locale = locale
    
    @property
    def code(self) -> Optional[str]:
        return self._code or self._get_lang_data('code', locale=self._locale)
    
    @code.setter
    def code(self, value):
        self._locale = None
        self._code = value
    
    @property
    def locale(self) -> Optional[str]:
        return self._locale or self._get_lang_data('locale', self._code)

    @locale.setter
    def locale(self, value):
        self._code = None
        self._locale = value
    
    @property
    def name(self) -> Optional[str]:
        return self._get_lang_data('name', code=self._code, locale=self._locale)
    
    @property
    def vernacular(self) -> Optional[str]:
        return self._get_lang_data('vernacular', code=self._code, locale=self._locale)

    @property
    def rsconf(self) -> Optional[str]:
        return self._get_tag_attribute('data-rsconf', self.code)
    
    @property
    def lib(self) -> Optional[str]:
        return self._get_tag_attribute('data-lib', self.code)

    def is_wol_available(self, code=None) -> bool:
        self.browser.open(URL_LIBRARIES)
        if self.browser.page.find('a', {'data-meps-symbol': code or self.code}):
            return True
        else:
            return False
    
    @LazyProperty
    def all_langs(self) -> List[Dict]:
        return requests.get(URL_LANGUAGES).json()['languages']
    
    @property
    def signs_languages(self) -> List[Dict]:
        return [item for item in self.all_langs if item['isSignLanguage']]

    def _get_lang_data(self, key, code=None, locale=None) -> Optional[str]:
        if code:
            return next((lang[key] for lang in self.all_langs if lang['code'] == code), None)
        elif locale:
            return next((lang[key] for lang in self.all_langs if lang['locale'] == locale), None)
        else:
            raise TypeError('Missing required argument: code or locale')

    def _get_tag_attribute(self, attribute_name, code) -> Optional[str]:
        self.browser.open(URL_LIBRARIES)
        try:
            value = self.browser.page.find('a', {'data-meps-symbol': code}).get(attribute_name)
        except:
            return None
        else:
            return value

    def __str__(self):
        return f"JWLanguage\n\tcode={self.code!r}\n\tlocale={self.locale!r}\n\tname={self.name!r}\n\t" \
            f"vernacular={self.vernacular!r}\n\trsconf={self.rsconf!r}\n\tlib={self.lib!r}"
