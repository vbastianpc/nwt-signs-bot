# from pathlib import Path
# Path('database.db').unlink()

import sqlite3
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

from telegram import Bot

from bot.logs import get_logger
from bot.secret import ADMIN
from bot.secret import TOKEN
from bot.utils import dt_now
from bot.database import PATH_DB
from bot.database import report
from bot.database import get
from bot.database import add
from bot.database import fetch
from bot.database.schema import User
from bot.utils.fonts import fetch_fonts, download_fonts


logger = get_logger(__name__)

rbi8 = 'Rbi8_E.jwpub'
contents = 'contents'
rbi8db = 'Rbi8_E.db'

def get_rbi8_db(overwrite=False):
    url = 'https://download-a.akamaihd.net/files/media_publication/2d/Rbi8_E.jwpub'
    if overwrite is False and Path(rbi8).exists():
        logger.info('Already exists rbi8.db')
    else:
        with open(rbi8, 'wb') as f:
            logger.info(f'Downloading {url}')
            f.write(requests.get(url).content)
    with ZipFile(rbi8) as jwpub:
        with jwpub.open(contents, 'r') as c:
            with open(contents, 'wb') as f:
                f.write(c.read())
    
    with ZipFile(contents) as z:
        with z.open(rbi8db, 'r') as r:
            with open(rbi8db, 'wb') as f:
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


def fetch_rbi8db():
    rbi8_con = sqlite3.connect(rbi8db)
    con = sqlite3.connect(PATH_DB)
    rbi8_cur = rbi8_con.cursor()
    cur = con.cursor()
    chapters = rbi8_cur.execute("""
        SELECT BookNumber,
            ChapterNumber,
            FirstVerseId,
            LastVerseId
        FROM BibleChapter
    """).fetchall()
    cur.execute("""INSERT INTO Bible (VerseId, BookNumber, ChapterNumber, VerseNumber)
                   VALUES (0, 0, 0, 0) ON CONFLICT DO NOTHING""")
    for data in chapters:
        book_number, chapter_number, first_verse_id, last_verse_id = data
        labels = rbi8_cur.execute(f"""SELECT Label FROM BibleVerse
                                      WHERE BibleVerseId BETWEEN {first_verse_id} AND {last_verse_id}""")
        for label in labels:
            versenum = parse_label_verse(label[0])
            if versenum != 0:
                cur.execute("""INSERT INTO Bible(BookNumber, ChapterNumber, VerseNumber, IsApocryphal)
                               VALUES (?, ?, ?, ?)
                               ON CONFLICT DO NOTHING""",
                            (book_number, chapter_number, versenum, False))
        # cur.execute("""INSERT INTO Bible (BookNumber, ChapterNumber, VerseNumber)
        #                VALUES (?, ?, ?) ON CONFLICT DO NOTHING""",
        #             (book_number, chapter_number, 0))
        # cur.execute("""INSERT INTO Bible (BookNumber, ChapterNumber, VerseNumber)
        #                VALUES (?, ?, ?) ON CONFLICT DO NOTHING""",
        #             (book_number, 0, 0))
    con.commit()
    con.close()
    rbi8_con.close()


if __name__ == '__main__':
    logger.info('Starting configuration...')
    get_rbi8_db(overwrite=False)
    fetch_rbi8db()
    logger.info('rbi8 bible ok')
    fetch.languages()
    logger.info(f'There are {report.count_languages()} languages stored in the database')
    fetch.editions()
    logger.info(f'There are {report.count_bible_editions()} bible editions stored in the database')
    for language_code in ['en', 'es', 'vi', 'ko', 'csg', 'ase']:
        fetch.books(language_code=language_code)
    for book_code in [('csg', 19), ('csg', 40), ('csg', 1), ('ase', 19)]:
        book = get.book(book_code[0], book_code[1])
        assert book
        fetch.chapters_and_videomarkers(book)
    bot = Bot(TOKEN)
    member = bot.get_chat_member(chat_id=ADMIN, user_id=ADMIN)
    sign_language = get.language(code='csg')
    add.or_update_user(
        ADMIN,
        first_name=member.user.first_name,
        last_name=member.user.last_name,
        user_name=member.user.username,
        is_premium=member.user.is_premium,
        bot_language_code=member.user.language_code,
        sign_language_code=sign_language.code,
        sign_language_name=sign_language.vernacular, # TODO function requests get one language vernacular
        status=User.AUTHORIZED,
        added_datetime=dt_now()
    )
    logger.info(f'User {member.user.first_name} added to database')
    # fetch_fonts()
    # download_fonts()
    logger.info('Configuration succesful!')
    logger.info('done')
