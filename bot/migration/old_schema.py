"""
https://dbdiagram.io/d/641e6e955758ac5f172402c2
"""
from pathlib import Path

from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import Boolean, Integer, String


Base = declarative_base()


class Language(Base):
    __tablename__ = 'Language'
    id = Column('LanguageId', Integer, primary_key=True)
    code = Column('LanguageCode', String, unique=True, nullable=False)
    locale = Column('LanguageLocale', String, unique=True)
    name = Column('LanguageName', String)
    vernacular = Column('LanguageVernacular', String)
    rsconf = Column('RsConfigSymbol', String)
    lib = Column('LibrarySymbol', String)
    is_sign_lang = Column('IsSignLanguage', Boolean)
    bible_books = relationship('BibleBook', back_populates='parent')
    users = relationship('User', back_populates='signlanguage')

    def __repr__(self):
        return f"<Language(code={self.code!r}, locale={self.locale!r}, name={self.name!r}"\
            f"vernacular={self.vernacular!r}, rsconf={self.rsconf!r}, lib={self.lib!r})>"


class BibleBook(Base):
    __tablename__ = 'BibleBook'
    id = Column('BibleBookId', Integer, primary_key=True)
    sign_language_id = Column('LanguageId', Integer, ForeignKey('Language.LanguageId'), nullable=False)
    booknum = Column('BookNumber', Integer)
    bookname = Column('BookName', String)
    parent = relationship('Language', back_populates='bible_books')
    bible_chapters = relationship('BibleChapter', back_populates='parent')
    sent_verses = relationship(
        'SentVerse',
        cascade="all,delete",
        back_populates='parent',
        passive_deletes=True,
    )
    __table_args__ = (UniqueConstraint('BookNumber', 'LanguageId'), )

    def __repr__(self):
        return f"<BibleBook(booknum={self.booknum!r}, bookname={self.bookname!r})>"


class BibleChapter(Base):
    __tablename__ = 'BibleChapter'
    id = Column('BibleChapterId', Integer, primary_key=True)
    bible_book_id = Column('BibleBookId', Integer, ForeignKey('BibleBook.BibleBookId'), nullable=False)
    chapter = Column('ChapterNumber', Integer)
    checksum = Column('Checksum', String)
    parent = relationship('BibleBook', back_populates='bible_chapters')
    video_markers = relationship(
        'VideoMarker',
        cascade="all,delete",
        back_populates='parent',
        # passive_deletes=True,
    )
    __table_args__ = (UniqueConstraint('BibleBookId', 'ChapterNumber', 'Checksum'), )

    def __repr__(self):
        return f"<BibleChapter(chapter={self.chapter!r}, checksum={self.checksum!r})>"    


class VideoMarker(Base):
    __tablename__ = 'VideoMarker'
    id = Column('VideoMarkerId', Integer, primary_key=True)
    bible_chapter_id = Column('BibleChapterId', Integer, ForeignKey('BibleChapter.BibleChapterId'), nullable=False)
    label = Column('Label', String)
    start_time = Column('StartTime', String)
    duration = Column('Duration', String)
    versenum = Column('VerseNumber', Integer)
    end_transition_duration = Column('EndTransitionDuration', String)
    parent = relationship('BibleChapter', back_populates='video_markers')

    def __repr__(self):
        return f"<VideoMarker(label={self.label!r}, versenum={self.versenum!r}, start_time={self.start_time!r}, " \
            f"duration={self.duration!r}, end_transition_duration={self.end_transition_duration!r})>"


class SentVerse(Base):
    __tablename__ = 'SentVerse'
    id = Column('SentVerseId', Integer, primary_key=True)
    bible_book_id = Column('BibleBookId', Integer, ForeignKey('BibleBook.BibleBookId'), nullable=False)
    checksum = Column('Checksum', String)
    chapter = Column('ChapterNumber', Integer)
    raw_verses = Column('RawVerseNumbers', String)
    citation = Column('Citation', String)
    quality = Column('Quality', String)
    telegram_file_id = Column('TelegramFileId', String, unique=True)
    size = Column('Size', Integer)
    added_datetime = Column('AddedDatetime', String)
    parent = relationship('BibleBook', back_populates='sent_verses')

    def __repr__(self):
        return f"<SentVerse(chapter={self.chapter!r}, raw_verses={self.raw_verses!r}, citation={self.citation!r}, " \
            f"quality={self.quality!r}, telegram_file_id={self.telegram_file_id!r}, checksum={self.checksum!r}, " \
            f"added_datetime={self.added_datetime!r}, size={self.size!r})>"


class User(Base):
    __tablename__ = 'User'
    id = Column('UserId', Integer, primary_key=True)
    telegram_user_id = Column('TelegramUserId', Integer, unique=True)
    sign_language_id = Column('LanguageId', Integer, ForeignKey('Language.LanguageId'))
    full_name = Column('FullName', String)
    status = Column('Status', Integer)
    added_datetime = Column('AddedDatetime', String)
    bot_lang = Column('BotLanguage', String)
    signlanguage = relationship('Language', back_populates='users')

    def __repr__(self):
        return f"<User(id={self.id!r}, telegram_user_id={self.telegram_user_id!r}, status={self.status!r}, " \
            f"sign_language_id={self.sign_language_id!r}, full_name={self.full_name!r}," \
            f"added_datetime={self.added_datetime!r})>"

    def is_brother(self):
        return True if self.status == 1 else False


class SentVerseUser(Base):
    __tablename__ = 'SentVerseUser'
    id = Column('SentVerseUserId', Integer, primary_key=True)
    sent_verse_id = Column('SentVerseId', Integer, ForeignKey('SentVerse.SentVerseId'), nullable=False)
    user_id = Column('UserId', Integer, ForeignKey('User.UserId'))
    datetime = Column('Datetime', String)

    def __repr__(self):
        return f"<UserRequest(sent_verse_id={self.sent_verse_id!r}, user_id={self.user_id!r}, " \
            f"datetime={self.datetime!r})>"


class BookNamesAbbreviation(Base):
    __tablename__ = 'BookNamesAbbreviation'
    id = Column('BookNamesAbbreviationId', Integer, primary_key=True)
    lang_locale = Column('LangLocale', String)
    booknum = Column('BookNumber', Integer)
    full_name = Column('BookFullName', String)
    long_abbr_name = Column('BookLongAbbreviationName', String)
    abbr_name = Column('BookAbbreviationName', String)
    __table_args__ = (UniqueConstraint('LangLocale', 'BookNumber'), )

    def __repr__(self):
        return f"<BookNamesAbbreviation(lang_locale={self.lang_locale!r}, booknum={self.booknum!r}, " \
            f"full_name={self.full_name!r}, long_abbr_name={self.long_abbr_name!r}, abbr_name={self.abbr_name!r})>"



from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.engine import Engine



OLD_DB = Path(__file__).parent / '2023-05-26 00 47 13-04 00 database.db'

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def start_database() -> scoped_session:
    engine = create_engine(rf'sqlite:///{OLD_DB}', echo=False)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    return scoped_session(sessionmaker(bind=engine))()


old_session = start_database()