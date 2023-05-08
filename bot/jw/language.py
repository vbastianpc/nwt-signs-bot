from typing import List, Dict, Optional
import requests

from bot.utils.browser import LazyBrowser
from bot.utils.models import LazyProperty
from bot.jw import URL_LANGUAGES
from bot.jw import URL_LIBRARIES
from bot.logs import get_logger


logger = get_logger(__name__)


# It's a little weird and confused meps_symbol, locale, code, symbol, langcode, etc
# convention for all my scripts:
# meps_symbol: E
# code: en
#
# in API https://data.jw-api.org/mediator/v1/languages/S/all
# code: E
# locale: en
# 
# in API https://www.jw.org/en/languages/
# langcode: E
# symbol: en
#
# in https://wol.jw.org/en/wol/li/r1/lp-e
# data-meps-symbol: E
# data-locale: en

class JWLanguage:
    wol_browser = LazyBrowser()
    browser = LazyBrowser()

    def __init__(self, meps_symbol=None, code=None):
        if meps_symbol and code:
            raise TypeError('meps_symbol and code are mutually exclusive arguments')
        self._meps_symbol = meps_symbol
        self._code = code
    
    @property
    def meps_symbol(self) -> Optional[str]:
        return self._meps_symbol or self._get_lang_data('code', code=self._code)
    
    @meps_symbol.setter
    def meps_symbol(self, value):
        self._code = None
        self._meps_symbol = value
    
    @property
    def code(self) -> Optional[str]:
        return self._code or self._get_lang_data('locale', self._meps_symbol)

    @code.setter
    def code(self, value):
        self._meps_symbol = None
        self._code = value
    
    @property
    def name(self) -> Optional[str]:
        return self._get_lang_data('name', meps_symbol=self._meps_symbol, code=self._code)
    
    @property
    def vernacular(self) -> Optional[str]:
        return self._get_lang_data('vernacular', meps_symbol=self._meps_symbol, code=self._code)

    @property
    def is_sign_language(self) -> Optional[bool]:
        return self._get_lang_data('isSignLanguage', meps_symbol=self._meps_symbol, code=self._code)
    
    @property
    def is_rtl(self) -> bool:
        return self._get_lang_data('isRTL', meps_symbol=self._meps_symbol, code=self._code)

    @property
    def rsconf(self) -> Optional[str]:
        return self._get_tag_attribute('data-rsconf', self.meps_symbol)
    
    @property
    def lib(self) -> Optional[str]:
        return self._get_tag_attribute('data-lib', self.meps_symbol)
    
    @property
    def script(self) -> str:
        return self._get_lang_data('script', meps_symbol=self._meps_symbol, code=self._code)

    def is_wol_available(self, meps_symbol=None) -> bool:
        self.wol_browser.open(URL_LIBRARIES)
        if self.wol_browser.page.find('a', {'data-meps-symbol': meps_symbol or self.meps_symbol}):
            return True
        else:
            return False
    
    @LazyProperty
    def all_langs(self) -> List[Dict]:
        return self.browser.open(URL_LANGUAGES).json()['languages']
    
    @property
    def signs_languages(self) -> List[Dict]:
        return [item for item in self.all_langs if item['isSignLanguage']]

    def _get_lang_data(self, key, meps_symbol=None, code=None) -> Optional[str]:
        if meps_symbol:
            return next((lang[key] for lang in self.all_langs if lang['code'] == meps_symbol))
        elif code:
            return next((lang[key] for lang in self.all_langs if lang['locale'] == code))
        else:
            raise TypeError('Missing required argument: meps_symbol or code')

    def _get_tag_attribute(self, attribute_name, meps_symbol) -> Optional[str]:
        self.wol_browser.open(URL_LIBRARIES)
        try:
            value = self.wol_browser.page.find('a', {'data-meps-symbol': meps_symbol}).get(attribute_name)
        except:
            return None
        else:
            return value

    def __repr__(self):
        return f"JWLanguage(meps_symbol={self.meps_symbol!r})"
