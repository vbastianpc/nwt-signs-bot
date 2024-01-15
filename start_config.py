import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile
import time
from telegram import Bot

from bot.logs import get_logger
from bot.secret import ADMIN
from bot.secret import TOKEN
from bot.utils import how_to_say
from bot.database import PATH_DB
from bot.database import get
from bot.database import add
from bot.database import fetch
from bot.database.schema import User
from bot.utils.browser import browser
from bot.utils.fonts import fetch_fonts
from bot.utils.fonts import download_fonts


logger = get_logger(__name__)

url = 'https://download-a.akamaihd.net/files/media_publication/96/nwt_E.jwpub'
nwt = Path(url).name
contents = 'contents'
nwtdb = Path(url).stem + '.db'

def get_nwt_db(overwrite=False):
    if overwrite is False and Path(nwt).exists():
        logger.info('Already exists nwt.db')
    else:
        logger.info('Downloading nwt Bible')
        with open(nwt, 'wb') as f:
            logger.info(f'Downloading {url}')
            f.write(browser.open(url).content)
    with ZipFile(nwt) as jwpub:
        with jwpub.open(contents, 'r') as c:
            with open(contents, 'wb') as f:
                f.write(c.read())

    with ZipFile(contents) as z:
        with z.open(nwtdb, 'r') as r:
            with open(nwtdb, 'wb') as f:
                f.write(r.read())
    Path(contents).unlink()


def parse_label_verse(html_tag):
    if not html_tag:
        return 0
    root = ET.fromstring(html_tag)
    if root.attrib['class'] == 'vl':
        return int(root.text)
    elif root.attrib['class'] == 'cl':
        return 1


def fetch_nwtdb():
    nwt_con = sqlite3.connect(nwtdb)
    con = sqlite3.connect(PATH_DB)
    nwt_cur = nwt_con.cursor()
    cur = con.cursor()
    chapters = nwt_cur.execute('SELECT BookNumber, ChapterNumber, FirstVerseId, LastVerseId ' \
                               'FROM BibleChapter').fetchall()
    cur.execute('INSERT INTO Bible (VerseId, BookNumber, ChapterNumber, VerseNumber, IsOmitted) ' \
                'VALUES (0, 0, 0, 0, 0) ON CONFLICT DO NOTHING')
    for data in chapters:
        booknum, chapternum, first_verse_id, last_verse_id = data
        labels = [label[0] for label in nwt_cur.execute(f'SELECT Label FROM BibleVerse ' \
                                 f'WHERE BibleVerseId BETWEEN {first_verse_id} AND {last_verse_id}')]
        for versenum in map(parse_label_verse, labels):
            cur.execute('INSERT INTO Bible(BookNumber, ChapterNumber, VerseNumber, IsOmitted) ' \
                            'VALUES (?, ?, ?, ?) ON CONFLICT DO NOTHING', (booknum, chapternum, versenum, False))
    # https://www.jw.org/finder?wtlocale=E&docid=1001070203&srcid=share&par=17-18
    omitted= [
        (40, 17, 21, 21), # Mat 17:21
        (40, 18, 11, 11), # Mat 18:11
        (40, 23, 14, 14), # Mat 23:14
        (41, 7, 16, 16),  # Mar 7:16
        (41, 9, 44, 44),  # Mar 9:44
        (41, 9, 46, 46),  # Mar 9:46
        (41, 11, 26, 26), # Mar 11:26
        (41, 15, 28, 28), # Mar 15:28
        (41, 16, 9, 20),  # Mar 16:9-20
        (42, 17, 36, 36), # Luc 17:36
        (42, 23, 17, 17), # Luc 23:17
        (43, 5, 4, 4),    # John 5:4
        (43, 7, 53, 53),  # John 7:53
        (43, 8, 1, 11),   # John 8:1-11
        (44, 8, 37, 37),  # Acts 8:37
        (44, 15, 34, 34), # Acts 15:34
        (44, 24, 7, 7),   # Acts 24:7
        (44, 28, 29, 29), # Acts 28:29
        (45, 16, 24, 24), # Rom 16:24
    ]
    for booknum, chapternum, first, last in omitted:
        for verse in range(first, last + 1):
            cur.execute('INSERT INTO Bible(BookNumber, ChapterNumber, VerseNumber, IsOmitted) ' \
                        'VALUES (?, ?, ?, ?) ON CONFLICT DO UPDATE SET IsOmitted=excluded.IsOmitted',
                        (booknum, chapternum, verse, True))
    con.commit()
    con.close()
    nwt_con.close()
    logger.info('nwt bible ok')


if __name__ == '__main__':
    logger.info('Starting configuration...')
    fetch.languages()

    bot_language = get.parse_language(input('Type your bot language: (en|es|vi) ') or 'en')
    sign_language = get.parse_language(input('Type your main sign language code: ') or 'ase')
    sign_language2 = get.parse_language(input('Type your secondary sign language code: '))
    sign_language3 = get.parse_language(input('Type your tertiary sign language code: '))
    get_nwt_db(overwrite=False)
    fetch_nwtdb()
    t0 = time.time()
    fetch.editions()
    fetch.books('en')
    for lang in set([
        bot_language,
        sign_language,
        sign_language2,
        sign_language3,
    ]):
        if lang:
            fetch.books(language_code=lang.code)
    logger.info('Connecting to Telegram API Bot')
    bot = Bot(TOKEN)
    member = bot.get_chat_member(chat_id=ADMIN, user_id=ADMIN)
    logger.info('Adding user admin')
    user = add.or_update_user(
        ADMIN,
        first_name=member.user.first_name,
        last_name=member.user.last_name or '',
        user_name=member.user.username,
        is_premium=member.user.is_premium,
        bot_language_code=bot_language.code,
        sign_language_code=sign_language.code,
        sign_language_code2=sign_language2.code if sign_language2 else None,
        sign_language_code3=sign_language3.code if sign_language3 else None,
        status=User.AUTHORIZED
    )
    logger.info(f'User {member.user.first_name} added to database')

    fetch_fonts()
    download_fonts()
    logger.info('Configuration succesful!')
