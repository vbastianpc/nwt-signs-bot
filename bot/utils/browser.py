import mechanicalsoup


class LazyBrowser(mechanicalsoup.StatefulBrowser):
    def __init__(self):
        agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'
        self.last_url = None
        self.response = None
        super().__init__(user_agent=agent)
        
    def open(self, url):
        if self.last_url == url or self.url == url:
            print('Lazy')
            return self.response
        else:
            print('Not Lazy')
            self.last_url = url
            self.response = super().open(url)
            return self.response
