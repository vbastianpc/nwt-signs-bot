import time
from datetime import datetime
from requests.models import Response

import mechanicalsoup

from bot.logs import get_logger
from bot.secret import URL_FUNCTION

logger = get_logger(__name__)


class LazyBrowser(mechanicalsoup.StatefulBrowser):
    __slots__ = ['tabs']
    def __init__(self):
        self.tabs = {}
        super().__init__(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')
        self.translate_url = None

    def open(self, url, *args, timeout=60, **kwargs) -> Response:
        """translate=True necessary when url hostname is www.jw.org and ip request from AWS servers"""
        if self.translate_url is None:
            prefix = URL_FUNCTION if 'www.jw.org' in url else ''
        else:
            prefix = URL_FUNCTION if self.translate_url else ''
        url = prefix + url
        if url in self.tabs:
            try:
                header_expires = self.tabs[url].headers.get('Expires')
                dt_expires = datetime.strptime(header_expires, "%a, %d %b %Y %H:%M:%S %Z")
            except:
                logger.info("Expiration datetime not found. Return cache tab")
                return self.tabs[url]
            if header_expires and dt_expires > datetime.now():
                logger.info(f'Not expired yet {dt_expires.isoformat()}')
                return self.tabs[url]
            else:
                logger.info('Expired')

        if len(self.tabs) >= 10:
            old_tab = list(self.tabs)[0]
            logger.info(f'Closing tab {old_tab}')
            self.tabs.pop(old_tab)
        t0 = time.time()
        kwargs = dict(timeout=timeout) | kwargs
        logger.info(f'Loading {url}')
        res = super().open(url, *args, **kwargs)
        logger.info(f'{time.time() - t0:.3f}s')
        self.tabs |= {url: res}
        return res


browser = LazyBrowser()

if __name__ == '__main__':
    browser.open('https://www.jw.org/en')
    browser.open('https://wol.jw.org/wol/finder?wtlocale=BRS&pub=nwt')
    print('end')