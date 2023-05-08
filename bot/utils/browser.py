import mechanicalsoup

from bot.logs import get_logger

logger = get_logger(__name__)

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'

class LazyBrowser(mechanicalsoup.StatefulBrowser):
    def __init__(self):
        self.last_url = None
        self.response = None
        super().__init__(user_agent=USER_AGENT)

    def open(self, url):
        if self.last_url == url or self.url == url:
            return self.response
        else:
            self.last_url = url
            logger.info('Opening %s', url)
            self.response = super().open(url)
            logger.info('Ok      %s', url)
            return self.response
