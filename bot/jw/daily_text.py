from datetime import date

from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

from bot.database.schema import Language
from bot.utils.browser import browser


class DailyText:
    def __init__(self, language: Language, dt: date = None):
        self.language = language
        self.date = dt or date.today()
    
    @property
    def url(self) -> str:
        return f'https://wol.jw.org/wol/dt/{self.language.rsconf}/{self.language.lib}' \
               f'/{self.date.year}/{self.date.month}/{self.date.day}'

    def get_text(self) -> str:
        res = browser.open(self.url, translate_url=False)
        soup = BeautifulSoup(res.json()['items'][0]['content'], 'html.parser')
        url = f'https://wol.jw.org/{self.language.code}/wol/h/{self.language.rsconf}/{self.language.lib}' \
              f'/{self.date.year}/{self.date.month}/{self.date.day}'
        header = f'<b><a href="{url}">' + soup.find('header').text.replace('\n', '') + '</a></b>\n\n'
        text = '<i>' + soup.find('p').text.replace('\xa0', ' ') + '</i>\n\n'
        comment = soup.findAll('p')[1].text.replace('\xa0', ' ')
        return header + text + comment




if __name__ == '__main__':
    from bot.database import get

    daily = DailyText(get.language(code='es'))
    daily.get_text()

