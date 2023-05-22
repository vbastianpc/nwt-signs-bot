import time
from datetime import datetime
from requests.models import Response

import mechanicalsoup

from bot.logs import get_logger
from bot.secret import URL_FUNCTION

logger = get_logger(__name__)


class LazyBrowser(mechanicalsoup.StatefulBrowser):
    __slots__ = ['prefix', 'tabs']
    def __init__(self, translate_url=True):
        self.prefix = URL_FUNCTION if translate_url else ''
        self.tabs = {}
        super().__init__(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')

    def open(self, url, *args, timeout=10, **kwargs) -> Response:
        if url in self.tabs:
            expires = self.tabs[url].headers.get('Expires')
            expires = datetime.strptime(expires, "%a, %d %b %Y %H:%M:%S %Z") if expires else datetime.now()
            if expires > datetime.now():
                logger.info(f'Not expired yet {expires.isoformat()}')
                return self.tabs[url]
            else:
                logger.info(f'Expired {expires.isoformat()}')

        if len(self.tabs) >= 10:
            old_tab = list(self.tabs)[0]
            logger.info(f'Closing tab {old_tab}')
            self.tabs.pop(old_tab)
        t0 = time.time()
        kwargs = dict(timeout=timeout) | kwargs
        logger.info(f'Loading {self.prefix + url}')
        res = super().open(self.prefix + url, *args, **kwargs)
        logger.info(f'{time.time() - t0:.3f}s')
        self.tabs |= {url: res}
        return res


browser = LazyBrowser()

if __name__ == '__main__':
    browser.open('https://www.jw.org/en')
    browser.open('https://www.jw.org/es')
    print('end')