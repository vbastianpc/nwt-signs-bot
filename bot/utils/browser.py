import time
from datetime import datetime
from requests.models import Response
import pytz

import mechanicalsoup

from bot.logs import get_logger
from bot.secret import URL_FUNCTION

logger = get_logger(__name__)


class LazyBrowser(mechanicalsoup.StatefulBrowser):
    __slots__ = ['tabs']
    def __init__(self):
        self.tabs = {}
        super().__init__(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')

    def open(self, url, *args, timeout=60, **kwargs) -> Response:
        """translate=True necessary when url hostname is www.jw.org and ip request from AWS servers"""
        url = URL_FUNCTION + url if 'www.jw.org' in url else url
        logger.info(f'Loading {url}')
        if url in self.tabs:
            try:
                header_expires = self.tabs[url].headers.get('Expires')
                dt_expires = datetime.strptime(header_expires, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=pytz.UTC)
                now = datetime.now(tz=pytz.UTC)
                logger.info(f'expires={dt_expires.isoformat()!r}, now={now.isoformat()!r}')
            except:
                logger.info("Expiration datetime not found. Return cache tab")
                return self.tabs[url]
            if header_expires and dt_expires > now:
                logger.info(f'Lazy tab. Not expired')
                return self.tabs[url]
            logger.info(f'Expired {dt_expires.isoformat()}')

        if len(self.tabs) >= 10:
            old_tab = list(self.tabs)[0]
            logger.info(f'Closing tab {old_tab}')
            self.tabs.pop(old_tab)
        t0 = time.time()
        kwargs = {'timeout': timeout} | kwargs
        res = super().open(url, *args, **kwargs)
        logger.info(f'{time.time() - t0:.3f}s')
        self.tabs |= {url: res}
        return res


browser = LazyBrowser()

if __name__ == '__main__':
    browser.open('https://www.jw.org/en')
    browser.open('https://wol.jw.org/wol/finder?wtlocale=BRS&pub=nwt')
    print('end')