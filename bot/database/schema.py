"""
https://dbdiagram.io/d/61417a16825b5b0146029d49
"""
from datetime import datetime, timedelta
from typing import Type

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import Boolean
from sqlalchemy.sql.sqltypes import Integer
from sqlalchemy.sql.sqltypes import Float
from sqlalchemy.sql.sqltypes import String
from sqlalchemy.dialects.sqlite import DATETIME

DateTime = DATETIME(storage_format="%(year)04d-%(month)02d-%(day)02d %(hour)02d:%(minute)02d:%(second)02d")
class Base:
    """https://stackoverflow.com/a/55749579
    https://stackoverflow.com/a/54034230"""
    def __repr__(self):
        params = [f'{k}={v!r}' for k, v in self.__dict__.items() if k not in ['_sa_instance_state', '_sa_adapter']]
        params = ',\n    '.join(params)
        return f'<{self.__class__.__name__}(\n    {params}\n)>'

Base = declarative_base(cls=Base)

class Bible(Base):
    __tablename__ = 'Bible'
    __table_args__ = (UniqueConstraint('BookNumber', 'ChapterNumber', 'VerseNumber'),)
    id = Column('VerseId', Integer, primary_key=True)
    book = Column('BookNumber', Integer)
    chapter = Column('ChapterNumber', Integer)
    verse = Column('VerseNumber', Integer)
    is_omitted = Column('IsOmitted', Boolean, default=False)

    video_markers: list['VideoMarker'] = relationship('VideoMarker',
                                                      back_populates='verse',
                                                      foreign_keys='[VideoMarker.verse_id]')

class Language(Base):
    __tablename__ = 'Language'
    code = Column('LanguageCode', String, primary_key=True)
    meps_symbol = Column('LanguageMepsSymbol', String, unique=True, nullable=False)
    name = Column('LanguageName', String)
    vernacular = Column('LanguageVernacular', String)
    rsconf = Column('RsConfigSymbol', String)
    lib = Column('LibrarySymbol', String)
    is_sign_language = Column('IsSignLanguage', Boolean)
    script = Column('LanguageScript', String)
    is_rtl = Column('IsRTL', Boolean)
    has_web_content = Column('HasWebContent', Boolean)
    is_counted = Column('IsCounted', Boolean)

    edition = relationship('Edition', back_populates='language', foreign_keys='[Edition.language_code]')
    sign_language_users: list['User'] = relationship('User', back_populates='sign_language',
                                                           foreign_keys='[User.sign_language_code]')
    bot_language_users: list['User'] = relationship('User', back_populates='bot_language',
                                                           foreign_keys='[User.bot_language_code]')
    overlay_users: list['User'] = relationship('User', back_populates='overlay_language',
                                                     foreign_keys='[User.overlay_language_code]')
    overlay_files: list['File'] = relationship('File', back_populates='overlay_language',
                                                     foreign_keys='[File.overlay_language_code]')


class Edition(Base):
    __tablename__ = 'Edition'
    __table_args__ = (UniqueConstraint('LanguageCode', 'SymbolEdition'), )

    id = Column('EditionId', Integer, primary_key=True)
    language_code = Column('LanguageCode', Integer, ForeignKey('Language.LanguageCode'), nullable=False)
    name = Column('Name', String)
    symbol = Column('SymbolEdition', String)
    url = Column('URL', String)
    hebrew = Column('Hebrew', String, default=' ')
    greek = Column('Greek', String, default=' ')

    language: Language = relationship('Language', back_populates='edition', foreign_keys=[language_code])
    books: 'Book' = relationship('Book', back_populates='edition', foreign_keys='[Book.edition_id]')


class Book(Base):
    __tablename__ = 'Book'
    __table_args__ = (UniqueConstraint('BookNumber', 'EditionId'), )

    id = Column('BookId', Integer, primary_key=True)
    edition_id = Column('EditionId', Integer, ForeignKey('Edition.EditionId'), nullable=False)
    number = Column('BookNumber', Integer)

    name = Column('StandardName', String, default='')
    standard_abbreviation = Column('StandardAbbreviation', String, default='')
    official_abbreviation = Column('OfficialAbbreviation', String, default='')

    standard_singular_bookname = Column('StandardSingularBookName', String, default='')
    standard_singular_abbreviation = Column('StandardSingularAbbreviation', String, default='')
    official_singular_abbreviation = Column('OfficialSingularAbbreviation', String, default='')

    standard_plural_bookname = Column('StandardPluralBookName', String, default='')
    standard_plural_abbreviation = Column('StandardPluralAbbreviation', String, default='')
    official_plural_abbreviation = Column('OfficialPluralAbbreviation', String, default='')

    refreshed = Column('RefreshedOnDate', DateTime)

    book_display_title = Column('BookDisplayTitle', String, default='')
    chapter_display_title = Column('ChapterDisplayTitle', String, default='')

    edition: Edition = relationship('Edition', back_populates='books', foreign_keys=[edition_id])
    chapters: list['Chapter'] = relationship('Chapter', back_populates='book', foreign_keys='[Chapter.book_id]')

    @property
    def language(self) -> Language:
        return self.edition.language


class Chapter(Base):
    __tablename__ = 'Chapter'
    __table_args__ = (UniqueConstraint('BookId', 'ChapterNumber'), )

    id = Column('ChapterId', Integer, primary_key=True)
    book_id = Column('BookId', Integer, ForeignKey('Book.BookId'), nullable=False)
    number = Column('ChapterNumber', Integer)
    checksum = Column('Checksum', String)
    modified_datetime = Column('ModifiedDatetime', DateTime)
    url = Column('URL', String)

    book: Book = relationship('Book', back_populates='chapters', foreign_keys=[book_id])
    files: list['File'] = relationship('File', back_populates='chapter', foreign_keys='[File.chapter_id]')
    video_markers: list['VideoMarker'] = relationship(
        'VideoMarker',
        # cascade="all,delete",
        back_populates='chapter',
        foreign_keys='[VideoMarker.chapter_id]'
        # passive_deletes=True,
    )

    @property
    def edition(self) -> Edition:
        return self.book.edition

    @property
    def language(self) -> Language:
        return self.book.edition.language

    def get_file(self, verses: list[int], overlay_language_code: str | None, delogo: bool) -> Type['File'] | None:
        if any((file := f) for f in reversed(self.files)
               if f.raw_verses == ' '.join(map(str, verses)) and
                  f.overlay_language_code == overlay_language_code and
                  f.is_deprecated is False and
                  f.delogo is delogo):
            return file
        return None

    def get_videomarker(self, verse: int) -> Type['VideoMarker'] | None:
        videomarkers = [videomarker for videomarker in self.video_markers if videomarker.versenum == verse]
        return videomarkers[0] if videomarkers else None


class VideoMarker(Base):
    __tablename__ = 'VideoMarker'

    id = Column('VideoMarkerId', Integer, primary_key=True)
    chapter_id = Column('ChapterId', Integer, ForeignKey('Chapter.ChapterId'), nullable=False)
    verse_id = Column('VerseId', Integer, ForeignKey('Bible.VerseId'), nullable=False)
    versenum = Column('VerseNumber', Integer)
    label = Column('Label', String)
    duration = Column('Duration', String)
    start_time = Column('StartTime', String)
    end_transition_duration = Column('EndTransitionDuration', String)

    chapter: Chapter = relationship('Chapter', back_populates='video_markers', foreign_keys=[chapter_id])
    verse: Bible = relationship('Bible', back_populates='video_markers', foreign_keys=[verse_id])

    @property
    def book(self) -> Book:
        return self.chapter.book

    @property
    def edition(self) -> Edition:
        return self.chapter.book.edition

    @property
    def language(self) -> Language:
        return self.chapter.book.edition.language


class File(Base):
    __tablename__ = 'File'

    id = Column('FileId', Integer, primary_key=True)
    chapter_id = Column('ChapterId', Integer, ForeignKey('Chapter.ChapterId'), nullable=False)
    telegram_file_id = Column('TelegramFileId', String, unique=True)
    telegram_file_unique_id = Column('TelegramFileUniqueId', String, unique=True)
    size = Column('FileSize', Integer)
    duration = Column('Duration', Float)
    citation = Column('Citation', String)
    raw_verses = Column('RawVerseNumbers', String)
    count_verses = Column('CountVerses', Integer)
    added_datetime = Column('AddedDatetime', DateTime)
    overlay_language_code = Column('OverlayLanguageCode', Integer, ForeignKey('Language.LanguageCode')) # deprecated
    overlay_text = Column('OverlayText', String)
    is_deprecated = Column('IsDeprecated', Boolean, default=False)
    delogo = Column('Delogo', Boolean)

    chapter: Chapter = relationship('Chapter', back_populates='files', foreign_keys=[chapter_id])
    overlay_language: Language = relationship('Language', back_populates='overlay_files',
                                    foreign_keys=[overlay_language_code]) # deprecated
    users: list['User'] = relationship('User', back_populates='files', secondary='File2User')

    @property
    def book(self) -> Book:
        return self.chapter.book

    @property
    def edition(self) -> Edition:
        return self.chapter.book.edition

    @property
    def language(self) -> Language:
        return self.chapter.book.edition.language


class User(Base):
    __tablename__ = 'User'
    AUTHORIZED = 1
    WAITING = 0
    DENIED = -1

    id = Column('UserId', Integer, primary_key=True)
    telegram_user_id = Column('TelegramUserId', Integer, unique=True, nullable=False)
    first_name = Column('FirstName', String, default='')
    last_name = Column('LastName', String, default='')
    user_name = Column('UserName', String, default='')
    is_premium = Column('IsPremium', Boolean)
    sign_language_code = Column('SignLanguageCode', Integer, ForeignKey('Language.LanguageCode'))
    sign_language_code2 = Column('SignLanguageCode2', Integer, ForeignKey('Language.LanguageCode'))
    sign_language_code3 = Column('SignLanguageCode3', Integer, ForeignKey('Language.LanguageCode'))
    bot_language_code = Column('BotLanguageCode', Integer, ForeignKey('Language.LanguageCode'))
    overlay_language_code = Column('OverlayLanguageCode', Integer, ForeignKey('Language.LanguageCode'))
    status = Column('Status', Integer, default=WAITING)
    added_datetime = Column('AddedDatetime', DateTime)
    last_active_datetime = Column('LastActiveDatetime', DateTime)
    delogo = Column('Delogo', Boolean, default=False, nullable=False)

    bot_language: Language = relationship('Language', back_populates='bot_language_users',
                                          foreign_keys=[bot_language_code])
    sign_language: Language = relationship('Language', back_populates='sign_language_users',
                                           foreign_keys=[sign_language_code])
    sign_language2: Language = relationship('Language', back_populates='sign_language_users',
                                            foreign_keys=[sign_language_code2])
    sign_language3: Language = relationship('Language', back_populates='sign_language_users',
                                            foreign_keys=[sign_language_code3])
    overlay_language: Language = relationship('Language', back_populates='overlay_users',
                                              foreign_keys=[overlay_language_code])
    files: list[File] = relationship('File', back_populates='users', secondary='File2User')

    def is_authorized(self) -> bool:
        return self.status == self.AUTHORIZED

    def is_waiting(self) -> bool:
        return self.status == self.WAITING

    def is_denied(self) -> bool:
        return self.status == self.DENIED

    def is_active(self) -> bool:
        _30_days_ago = datetime.now() - timedelta(days=30)
        return self.last_active_datetime > _30_days_ago

    @property
    def full_name(self) -> str:
        return f'{self.first_name} {self.last_name}' if self.last_name else self.first_name

    @property
    def sign_languages(self) -> list[Language]:
        return list(filter(None, [self.sign_language, self.sign_language2, self.sign_language3]))


class File2User(Base):
    __tablename__ = 'File2User'

    id = Column('File2UserId', Integer, primary_key=True)
    file_id: int = Column('FileId', Integer, ForeignKey('File.FileId'), nullable=False)
    user_id: int = Column('UserId', Integer, ForeignKey('User.UserId'), nullable=False)
    datetime = Column('Datetime', DateTime)
