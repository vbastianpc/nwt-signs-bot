"""
https://dbdiagram.io/d/61417a16825b5b0146029d49
"""
from datetime import datetime, timedelta

from bot.utils import dt_now
from bot.utils import represent as rep

from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import Boolean, Integer, String, DateTime


Base = declarative_base()


class Language(Base):
    __tablename__ = 'Language'
    id = Column('LanguageId', Integer, primary_key=True)
    meps_symbol = Column('LanguageCode', String, unique=True, nullable=False) #, sqlite_on_conflict_unique='IGNORE')
    code = Column('LanguageLocale', String, unique=True, nullable=False) #, sqlite_on_conflict_unique='IGNORE')
    name = Column('LanguageName', String)
    vernacular = Column('LanguageVernacular', String)
    rsconf = Column('RsConfigSymbol', String)
    lib = Column('LibrarySymbol', String)
    is_sign_language = Column('IsSignLanguage', Boolean)
    script = Column('LanguageScript', String)
    is_rtl = Column('IsRTL', Boolean)

    bible = relationship('Bible', back_populates='language', foreign_keys='[Bible.language_id]')
    sign_language_users = relationship('User', back_populates='sign_language', foreign_keys='[User.sign_language_id]')
    bot_language_users = relationship('User', back_populates='bot_language', foreign_keys='[User.bot_language_id]')
    overlay_users = relationship('User', back_populates='overlay_language', foreign_keys='[User.overlay_language_id]')
    overlay_verses = relationship('File', back_populates='overlay_language', foreign_keys='[File.overlay_language_id]')

    def __repr__(self):
        return f"<Language(code={self.code!r}, code={self.code!r}, name={self.name!r}, "\
            f"vernacular={self.vernacular!r}, rsconf={self.rsconf!r}, lib={self.lib!r})>"

class Bible(Base):
    __tablename__ = 'Bible'

    id = Column('BibleId', Integer, primary_key=True)
    language_id = Column('LanguageId', Integer, ForeignKey('Language.LanguageId'), nullable=False)
    name = Column('Name', String)
    symbol = Column('SymbolEdition', String)
    url = Column('URL', String)

    language = relationship('Language', back_populates='bible', foreign_keys=[language_id])
    books = relationship('Book', back_populates='bible', foreign_keys='[Book.bible_id]')


class Book(Base):
    __tablename__ = 'Book'
    __table_args__ = (UniqueConstraint('BookNumber', 'BibleId'), )

    id = Column('BookId', Integer, primary_key=True)
    bible_id = Column('BibleId', Integer, ForeignKey('Bible.BibleId'), nullable=False)
    number = Column('BookNumber', Integer)
    chapter_count = Column('ChapterCount', Integer)

    name = Column('StandardName', String)
    standard_abbreviation = Column('StandardAbbreviation', String)
    official_abbreviation = Column('OfficialAbbreviation', String)

    standard_singular_bookname = Column('StandardSingularBookName', String)
    standard_singular_abbreviation = Column('StandardSingularAbbreviation', String)
    official_singular_abbreviation = Column('OfficialSingularAbbreviation', String)

    standard_plural_bookname = Column('StandardPluralBookName', String)
    standard_plural_abbreviation = Column('StandardPluralAbbreviation', String)
    official_plural_abbreviation = Column('OfficialPluralAbbreviation', String)

    book_display_title = Column('BookDisplayTitle', String)
    chapter_display_title = Column('ChapterDisplayTitle', String)

    bible = relationship('Bible', back_populates='books', foreign_keys=[bible_id])
    chapters = relationship('Chapter', back_populates='book', foreign_keys='[Chapter.book_id]')
    # files = relationship(
    #     'File',
    #     cascade="all,delete",
    #     back_populates='bible_book',
    #     passive_deletes=True,
    #     foreign_keys='[File.bible_book_id]'
    # )

    def __repr__(self):
        return f"<BibleBook(number={self.number!r}, bookname={self.name!r})>"


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

    book = relationship('Book', back_populates='chapters', foreign_keys=[book_id])
    files = relationship('File', back_populates='chapter', foreign_keys='[File.chapter_id]')
    video_markers = relationship(
        'VideoMarker',
        # cascade="all,delete",
        back_populates='chapter',
        foreign_keys='[VideoMarker.chapter_id]'
        # passive_deletes=True,
    )

    def __repr__(self):
        return f"<Chapter(number={self.number!r}, checksum={self.checksum!r})>"    


class VideoMarker(Base):
    __tablename__ = 'VideoMarker'

    id = Column('VideoMarkerId', Integer, primary_key=True)
    chapter_id = Column('ChapterId', Integer, ForeignKey('Chapter.ChapterId'), nullable=False)
    versenum = Column('VerseNumber', Integer)
    label = Column('Label', String)
    duration = Column('Duration', String)
    start_time = Column('StartTime', String)
    end_transition_duration = Column('EndTransitionDuration', String)

    chapter = relationship('Chapter', back_populates='video_markers', foreign_keys=[chapter_id])

    def __repr__(self):
        return f"<VideoMarker(label={self.label!r}, versenum={self.versenum!r}, start_time={self.start_time!r}, " \
            f"duration={self.duration!r}, end_transition_duration={self.end_transition_duration!r})>"

class File(Base): # old File
    __tablename__ = 'File'

    id = Column('FileId', Integer, primary_key=True)
    chapter_id = Column('ChapterId', Integer, ForeignKey('Chapter.ChapterId'), nullable=False)
    telegram_file_id = Column('TelegramFileId', String, unique=True)
    telegram_file_unique_id = Column('TelegramFileUniqueId', String, unique=True)
    duration = Column('Duration', Integer)
    name = Column('FileName', String) # Path.stem it must be in written sign language. "Mateo 24:14 - SCH"
    raw_verses = Column('RawVerseNumbers', String)
    is_single_verse = Column('IsSingleVerse', Boolean)
    size = Column('FileSize', Integer)
    added_datetime = Column('AddedDatetime', DateTime)
    overlay_language_id = Column('OverlayLanguageId', Integer, ForeignKey('Language.LanguageId'))

    chapter = relationship('Chapter', back_populates='files', foreign_keys=[chapter_id])
    overlay_language = relationship('Language', back_populates='overlay_verses', foreign_keys=[overlay_language_id])
    
    users = relationship('User', back_populates='files', secondary='File2User')

    def get_language(self) -> Language:
        return self.chapter.book.bible.language
    
    def get_book(self) -> Book:
        return self.chapter.book

    def __repr__(self):
        """This is best https://stackoverflow.com/a/55749579. Change later"""
        return rep(self, id=self.id, chapter_id=self.chapter_id, telegram_file_id=self.telegram_file_id,
            telegram_file_unique_id=self.telegram_file_unique_id, duration=self.duration, name=self.name, raw_verses=self.raw_verses,
            size=self.size, added_datetime=self.added_datetime, overlay_language_id=self.overlay_language_id)

class User(Base):
    __tablename__ = 'User'

    id = Column('UserId', Integer, primary_key=True)
    telegram_user_id = Column('TelegramUserId', Integer, unique=True)
    full_name = Column('FullName', String)
    sign_language_id = Column('SignLanguageId', Integer, ForeignKey('Language.LanguageId'))
    bot_language_id = Column('BotLanguageId', Integer, ForeignKey('Language.LanguageId'))
    overlay_language_id = Column('OverlayLanguageId', Integer, ForeignKey('Language.LanguageId'))
    status = Column('Status', Integer)
    added_datetime = Column('AddedDatetime', DateTime)
    last_active_datetime = Column('LastActiveDatetime', DateTime)
    
    bot_language = relationship('Language', back_populates='bot_language_users', foreign_keys=[bot_language_id])
    sign_language = relationship('Language', back_populates='sign_language_users', foreign_keys=[sign_language_id])
    overlay_language = relationship('Language', back_populates='overlay_users', foreign_keys=[overlay_language_id])
    files = relationship('File', back_populates='users', secondary='File2User')

    def __repr__(self):
        return f"<User(id={self.id!r}, telegram_user_id={self.telegram_user_id!r}, status={self.status!r}, " \
            f"sign_language_id={self.sign_language_id!r}, full_name={self.full_name!r}," \
            f"added_datetime={self.added_datetime!r}, overlay_language_id={self.overlay_language_id})>"

    def is_accepted(self) -> bool:
        return True if self.status == 1 else False
    
    def is_waiting(self) -> bool:
        return True if self.status == 0 else False
    
    def is_banned(self) -> bool:
        return True if self.status == -1 else False
    
    def is_active(self) -> bool:
        _30_days_ago = dt_now() - timedelta(days=30)
        return self.last_active_datetime > _30_days_ago
    

class File2User(Base):
    __tablename__ = 'File2User'

    id = Column('File2UserId', Integer, primary_key=True)
    file_id = Column('FileId', Integer, ForeignKey('File.FileId'), nullable=False)
    user_id = Column('UserId', Integer, ForeignKey('User.UserId'), nullable=False)
    datetime = Column('Datetime', DateTime)

    def __repr__(self):
        return f"<UserRequest(file_id={self.file_id!r}, user_id={self.user_id!r}, " \
            f"datetime={self.datetime!r})>"
