"""
https://dbdiagram.io/d/61417a16825b5b0146029d49
"""
from datetime import datetime, timedelta

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import Boolean
from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy.sql.sqltypes import String
from sqlalchemy.sql.sqltypes import DateTime


class Base:
    """https://stackoverflow.com/a/55749579
    https://stackoverflow.com/a/54034230"""

    def __repr__(self):
        params = [f'{k}={v!r}' for k, v in self.__dict__.items() if k not in ['_sa_instance_state', '_sa_adapter']]
        params = ',\n    '.join(params)
        return f'<{self.__class__.__name__}(\n    {params}\n)>'


Base = declarative_base(cls=Base)


class Language(Base):
    __tablename__ = 'Language'
    id = Column('LanguageId', Integer, primary_key=True)
    meps_symbol = Column('LanguageMepsSymbol', String, unique=True, nullable=False)
    code = Column('LanguageCode', String, unique=True, nullable=False)
    name = Column('LanguageName', String)
    vernacular = Column('LanguageVernacular', String)
    rsconf = Column('RsConfigSymbol', String)
    lib = Column('LibrarySymbol', String)
    is_sign_language = Column('IsSignLanguage', Boolean)
    script = Column('LanguageScript', String)
    is_rtl = Column('IsRTL', Boolean)

    bible = relationship('Bible', back_populates='language', foreign_keys='[Bible.language_id]')  # type: Bible
    sign_language_users = relationship('User', back_populates='sign_language',
                                       foreign_keys='[User.sign_language_id]')  # type: User
    bot_language_users = relationship('User', back_populates='bot_language',
                                      foreign_keys='[User.bot_language_id]')  # type: User
    overlay_users = relationship('User', back_populates='overlay_language',
                                 foreign_keys='[User.overlay_language_id]')  # type: User
    overlay_verses = relationship('File', back_populates='overlay_language',
                                  foreign_keys='[File.overlay_language_id]')  # type: File


class Bible(Base):
    __tablename__ = 'Bible'
    __table_args__ = (UniqueConstraint('LanguageId', 'SymbolEdition'), )

    id = Column('BibleId', Integer, primary_key=True)
    language_id = Column('LanguageId', Integer, ForeignKey('Language.LanguageId'), nullable=False)
    name = Column('Name', String)
    symbol = Column('SymbolEdition', String)
    url = Column('URL', String)

    language = relationship('Language', back_populates='bible', foreign_keys=[language_id])  # type: Language
    books = relationship('Book', back_populates='bible', foreign_keys='[Book.bible_id]')  # type: Book


class Book(Base):
    __tablename__ = 'Book'
    __table_args__ = (UniqueConstraint('BookNumber', 'BibleId'), )

    id = Column('BookId', Integer, primary_key=True)
    bible_id = Column('BibleId', Integer, ForeignKey('Bible.BibleId'), nullable=False)
    number = Column('BookNumber', Integer)
    chapter_count = Column('ChapterCount', Integer)

    name = Column('StandardName', String, default='')
    standard_abbreviation = Column('StandardAbbreviation', String, default='')
    official_abbreviation = Column('OfficialAbbreviation', String, default='')

    standard_singular_bookname = Column('StandardSingularBookName', String, default='')
    standard_singular_abbreviation = Column('StandardSingularAbbreviation', String, default='')
    official_singular_abbreviation = Column('OfficialSingularAbbreviation', String, default='')

    standard_plural_bookname = Column('StandardPluralBookName', String, default='')
    standard_plural_abbreviation = Column('StandardPluralAbbreviation', String, default='')
    official_plural_abbreviation = Column('OfficialPluralAbbreviation', String, default='')

    book_display_title = Column('BookDisplayTitle', String, default='')
    chapter_display_title = Column('ChapterDisplayTitle', String, default='')

    bible = relationship('Bible', back_populates='books', foreign_keys=[bible_id])  # type: Bible
    chapters = relationship('Chapter', back_populates='book', foreign_keys='[Chapter.book_id]')  # type: Chapter
    # files = relationship(
    #     'File',
    #     cascade="all,delete",
    #     back_populates='bible_book',
    #     passive_deletes=True,
    #     foreign_keys='[File.bible_book_id]'
    # )


class Chapter(Base):
    __tablename__ = 'Chapter'
    __table_args__ = (UniqueConstraint('BookId', 'ChapterNumber', 'Checksum'), )

    id = Column('ChapterId', Integer, primary_key=True)
    book_id = Column('BookId', Integer, ForeignKey('Book.BookId'), nullable=False)
    number = Column('ChapterNumber', Integer)
    checksum = Column('Checksum', String)
    modified_datetime = Column('ModifiedDatetime', DateTime)
    url = Column('URL', String)
    title = Column('Title', String)

    book = relationship('Book', back_populates='chapters', foreign_keys=[book_id])  # type: Book
    files = relationship('File', back_populates='chapter', foreign_keys='[File.chapter_id]')  # type: File
    video_markers = relationship(
        'VideoMarker',
        # cascade="all,delete",
        back_populates='chapter',
        foreign_keys='[VideoMarker.chapter_id]'
        # passive_deletes=True,
    )  # type: VideoMarker


class VideoMarker(Base):
    __tablename__ = 'VideoMarker'

    id = Column('VideoMarkerId', Integer, primary_key=True)
    chapter_id = Column('ChapterId', Integer, ForeignKey('Chapter.ChapterId'), nullable=False)
    versenum = Column('VerseNumber', Integer)
    label = Column('Label', String)
    duration = Column('Duration', String)
    start_time = Column('StartTime', String)
    end_transition_duration = Column('EndTransitionDuration', String)

    chapter = relationship('Chapter', back_populates='video_markers', foreign_keys=[chapter_id])  # type: Chapter


class File(Base):  # old File
    __tablename__ = 'File'

    id = Column('FileId', Integer, primary_key=True)
    chapter_id = Column('ChapterId', Integer, ForeignKey('Chapter.ChapterId'), nullable=False)
    telegram_file_id = Column('TelegramFileId', String, unique=True)
    telegram_file_unique_id = Column('TelegramFileUniqueId', String, unique=True)
    duration = Column('Duration', Integer)
    name = Column('FileName', String)
    raw_verses = Column('RawVerseNumbers', String)
    is_single_verse = Column('IsSingleVerse', Boolean)
    size = Column('FileSize', Integer)
    added_datetime = Column('AddedDatetime', DateTime)
    overlay_language_id = Column('OverlayLanguageId', Integer, ForeignKey('Language.LanguageId'))

    chapter = relationship('Chapter', back_populates='files', foreign_keys=[chapter_id])  # type: Chapter
    overlay_language = relationship('Language', back_populates='overlay_verses',
                                    foreign_keys=[overlay_language_id])  # type: Language
    users = relationship('User', back_populates='files', secondary='File2User')  # type: User

    def get_language(self) -> Language:
        return self.chapter.book.bible.language

    def get_book(self) -> Book:
        return self.chapter.book


class User(Base):
    __tablename__ = 'User'
    AUTHORIZED = 1
    WAITING = 0
    DENIED = -1

    id = Column('UserId', Integer, primary_key=True)
    telegram_user_id = Column('TelegramUserId', Integer, unique=True, nullable=False)
    full_name = Column('FullName', String)
    sign_language_id = Column('SignLanguageId', Integer, ForeignKey('Language.LanguageId'))
    bot_language_id = Column('BotLanguageId', Integer, ForeignKey('Language.LanguageId'))
    overlay_language_id = Column('OverlayLanguageId', Integer, ForeignKey('Language.LanguageId'))
    status = Column('Status', Integer)
    added_datetime = Column('AddedDatetime', DateTime)
    last_active_datetime = Column('LastActiveDatetime', DateTime)

    bot_language = relationship('Language', back_populates='bot_language_users',
                                foreign_keys=[bot_language_id])  # type: Language
    sign_language = relationship('Language', back_populates='sign_language_users',
                                 foreign_keys=[sign_language_id])  # type: Language
    overlay_language = relationship('Language', back_populates='overlay_users',
                                    foreign_keys=[overlay_language_id])  # type: Language
    files = relationship('File', back_populates='users', secondary='File2User')  # type: File

    def is_authorized(self) -> bool:
        return self.status == self.AUTHORIZED

    def is_waiting(self) -> bool:
        return self.status == self.WAITING

    def is_denied(self) -> bool:
        return self.status == self.DENIED

    def is_active(self) -> bool:
        _30_days_ago = datetime.now() - timedelta(days=30)
        return self.last_active_datetime > _30_days_ago


class File2User(Base):
    __tablename__ = 'File2User'

    id = Column('File2UserId', Integer, primary_key=True)
    file_id = Column('FileId', Integer, ForeignKey('File.FileId'), nullable=False)
    user_id = Column('UserId', Integer, ForeignKey('User.UserId'), nullable=False)
    datetime = Column('Datetime', DateTime)
