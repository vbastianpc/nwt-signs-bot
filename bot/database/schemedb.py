"""
CREATE TABLE IF NOT EXISTS SignLanguage (
    CodeLang  VARCHAR NOT NULL PRIMARY KEY,
	Locale VARCHAR,
    Name VARCHAR,
	Vernacular VARCHAR,
	RsConfigSymbol VARCHAR,
	LibrarySymbol VARCHAR
);

CREATE TABLE IF NOT EXISTS BibleBook (
    BookNumber INT NOT NULL,
	CodeLang REFERENCES SignLanguage,
	BookName VARCHAR,
	PRIMARY KEY (BookNumber, CodeLang)
);

CREATE TABLE IF NOT EXISTS BibleChapter (
    CodeLang VARCHAR,
	BookNumber INT,
	ChapterNumber  INT,
    FOREIGN KEY (CodeLang, BookNumber) REFERENCES BibleBook (CodeLang, BookNumber),
    PRIMARY KEY (CodeLang, BookNumber, ChapterNumber)
);

CREATE TABLE IF NOT EXISTS VideoFile (
    CodeLang VARCHAR,
	BookNumber INT,
	ChapterNumber INT,
	Quality VARCHAR,
	URL VARCHAR,
	Checksum VARCHAR,
	Filesize INT,
	ModifiedDatetime VARCHAR,
	FOREIGN KEY (CodeLang, BookNumber, ChapterNumber) REFERENCES BibleChapter (CodeLang, BookNumber, ChapterNumber) ON DELETE CASCADE,
	PRIMARY KEY (CodeLang, BookNumber, ChapterNumber, Quality)
);

CREATE TABLE IF NOT EXISTS VideoMarker (
    CodeLang VARCHAR,
	BookNumber INT,
	ChapterNumber INT,
	VerseNumber INT,
	StartTime FLOAT,
	Duration FLOAT,
	EndTransitionDuration FLOAT,
	FOREIGN KEY (CodeLang, BookNumber, ChapterNumber) REFERENCES BibleChapter (CodeLang, BookNumber, ChapterNumber) ON DELETE CASCADE,
	PRIMARY KEY (CodeLang, BookNumber, ChapterNumber, VerseNumber)
);

CREATE TABLE IF NOT EXISTS SentVerse (
    CodeLang VARCHAR,
	BookNumber INT,
	ChapterNumber INT,
	VerseNumbers VARCHAR,
	Quality VARCHAR,
	FileID VARCHAR,
	AddedDatetime VARCHAR,
	FOREIGN KEY (CodeLang, BookNumber, ChapterNumber) REFERENCES BibleChapter (CodeLang, BookNumber, ChapterNumber) ON DELETE CASCADE,
    PRIMARY KEY (CodeLang, BookNumber, ChapterNumber, Quality, VerseNumbers)
);

CREATE TABLE IF NOT EXISTS Users (
    UserID INT  NOT NULL PRIMARY KEY,
	FullName VARCHAR,
	CodeLang REFERENCES SignLanguage,
	Quality VARCHAR, 
	AddedDatetime VARCHAR
);


INSERT INTO SignLanguage (CodeLang, Locale, Name, Vernacular, RsConfigSymbol, LibrarySymbol)
VALUES ("SCH", "csg", "lengua de señas chilena", "lengua de señas chilena", "r377", "lp-sch");

INSERT INTO BibleBook (BookNumber, CodeLang, BookName)
VALUES (1, "SCH", "Génesis");

INSERT INTO BibleChapter (CodeLang, BookNumber, ChapterNumber)
VALUES ("SCH", 1, 3);

INSERT INTO BibleChapter (CodeLang, BookNumber, ChapterNumber)
VALUES ("SCH", 1, 4);

INSERT INTO VideoFile (CodeLang, BookNumber, ChapterNumber, Quality, Checksum, URL)
VALUES ("SCH", 1, 3, "720p", "skjdflsdkfdslfkdfkl", "https://jw.org");


DELETE FROM BibleChapter WHERE BookNumber=1;

"""
from datetime import datetime

from sqlalchemy.engine import Engine
from sqlalchemy import Column, Integer, Float, String, ForeignKey, ForeignKeyConstraint, event, create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class SignLanguage(Base):
    __tablename__ = 'SignLanguage'
    code_lang = Column('CodeLang', String, primary_key=True)
    locale = Column('Locale', String)
    name = Column('Name', String)
    vernacular = Column('Vernacular', String)
    rsconf = Column('RsConfigSymbol', String)
    lib = Column('LibrarySymbol', String)


class BibleBook(Base):
    __tablename__ = 'BibleBook'
    booknum = Column('BookNumber', Integer, primary_key=True)
    code_lang = Column('CodeLang', String, ForeignKey('SignLanguage.CodeLang'), primary_key=True)
    bookname = Column('BookName', String)


class BibleChapter(Base):
    __tablename__ = 'BibleChapter'
    code_lang = Column('CodeLang', String, primary_key=True)
    booknum = Column('BookNumber', Integer, primary_key=True)
    chapter = Column('ChapterNumber', Integer, primary_key=True)
    files = relationship(
        "VideoFile",
        cascade="all,delete",
        back_populates='parent',
        passive_deletes=True,
    )
    video_markers = relationship(
        'VideoMarker',
        cascade="all,delete",
        back_populates='parent',
        passive_deletes=True,
    )
    sent_verses = relationship(
        'SentVerse',
        cascade="all,delete",
        back_populates='parent',
        passive_deletes=True,
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ['CodeLang', 'BookNumber'],
            ['BibleBook.CodeLang', 'BibleBook.BookNumber']
        ),
    )

class VideoFile(Base):
    __tablename__ = 'VideoFile'
    code_lang = Column('CodeLang', String, primary_key=True)
    booknum = Column('BookNumber', Integer, primary_key=True)
    chapter = Column('ChapterNumber', Integer, primary_key=True)
    quality = Column('Quality', String, primary_key=True)
    url = Column('URL', String)
    checksum = Column('Checksum', String)
    filesize = Column('Filesize', Integer)
    modified_datetime = Column('ModifiedDatetime', String)
    parent = relationship('BibleChapter', back_populates='files')
    __table_args__ = (
        ForeignKeyConstraint(
            ['CodeLang', 'BookNumber', 'ChapterNumber'],
            ['BibleChapter.CodeLang', 'BibleChapter.BookNumber', 'BibleChapter.ChapterNumber'],
            ondelete="CASCADE"
        ),
    )


class VideoMarker(Base):
    __tablename__ = 'VideoMarker'
    code_lang = Column('CodeLang', String, primary_key=True)
    booknum = Column('BookNumber', Integer, primary_key=True)
    chapter = Column('ChapterNumber', Integer, primary_key=True)
    versenum = Column('VerseNumber', Integer, primary_key=True)
    start_time = Column('StartTime', Float)
    duration = Column('Duration', Float)
    end_transition_duration = Column('EndTransitionDuration', Float)
    parent = relationship('BibleChapter', back_populates='video_markers')
    __table_args__ = (
        ForeignKeyConstraint(
            ['CodeLang', 'BookNumber', 'ChapterNumber'],
            ['BibleChapter.CodeLang', 'BibleChapter.BookNumber', 'BibleChapter.ChapterNumber'],
            ondelete="CASCADE"
        ),
    )


class SentVerse(Base):
    __tablename__ = 'SentVerse'
    code_lang = Column('CodeLang', String, primary_key=True)
    booknum = Column('BookNumber', Integer, primary_key=True)
    chapter = Column('ChapterNumber', Integer, primary_key=True)
    versenums = Column('VerseNumbers', String, primary_key=True)
    quality = Column('Quality', String, primary_key=True)
    file_id = Column('FileID', String)
    added_datetime = Column('AddedDatetime', String)
    parent = relationship('BibleChapter', back_populates='sent_verses')
    __table_args__ = (
        ForeignKeyConstraint(
            ['CodeLang', 'BookNumber', 'ChapterNumber'],
            ['BibleChapter.CodeLang', 'BibleChapter.BookNumber', 'BibleChapter.ChapterNumber'],
            ondelete="CASCADE"
        ),
    )


class User(Base):
    __tablename__ = 'Users'
    user_id = Column('UserID', Integer, primary_key=True)
    full_name = Column('FullName', String)
    code_lang = Column('CodeLang', String, ForeignKey('SignLanguage.CodeLang'))
    quality = Column('Quality', String)
    added_datetime = Column('AddedDatetime', String)


engine = create_engine(f'sqlite:///database.db', echo=False)
Base.metadata.create_all(engine)


if __name__ == '__main__':
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine


    engine = create_engine(f'sqlite:///{datetime.now().isoformat(timespec="seconds")}.db', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    session.add(SignLanguage(code_lang='SCH', locale='csg'))
    session.flush()

    session.add(BibleBook(booknum=1, code_lang='SCH', bookname='Génesis'))
    session.add(BibleBook(booknum=40, code_lang='SCH', bookname='Mateo'))
    session.add(BibleBook(booknum=43, code_lang='SCH', bookname='Juan'))
    session.flush()

    session.add(BibleChapter(code_lang='SCH', booknum=1, chapter=4))
    session.add(BibleChapter(code_lang='SCH', booknum=40, chapter=14))
    session.add(VideoFile(code_lang='SCH', booknum=1, chapter=4, quality='720p', checksum='sdkjfhs', url='https://GENESIS'))
    session.add(VideoFile(code_lang='SCH', booknum=40, chapter=14, quality='720p', checksum='dgdfgsfghgf', url='https://MATEO'))
    session.commit()

    session.add(VideoMarker(code_lang='SCH', booknum=40, chapter=14, versenum=10, start_time=10.5))

    # session.delete(session.query(BibleChapter).filter(BibleChapter.booknum == 40)[0])
    session.query(BibleChapter).filter(BibleChapter.booknum == 1).delete()
    session.commit()
