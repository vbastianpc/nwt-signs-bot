"""
CREATE TABLE IF NOT EXISTS SignLanguages (
    CodeLang  VARCHAR NOT NULL PRIMARY KEY,
	Locale VARCHAR,
    Name VARCHAR,
	Vernacular VARCHAR,
	RsConfigSymbol VARCHAR,
	LibrarySymbol VARCHAR
);

CREATE TABLE IF NOT EXISTS Booknames (
    Booknum INT NOT NULL,
	CodeLang REFERENCES SignLanguages,
	Bookname VARCHAR,
	PRIMARY KEY (Booknum, CodeLang)
);

CREATE TABLE IF NOT EXISTS Chapters (
    CodeLang VARCHAR,
	Booknum INT,
	Chapter  INT,
    FOREIGN KEY (CodeLang, Booknum) REFERENCES Booknames (CodeLang, Booknum),
    PRIMARY KEY (CodeLang, Booknum, Chapter)
);

CREATE TABLE IF NOT EXISTS Files (
    CodeLang VARCHAR,
	Booknum INT,
	Chapter INT,
	Quality VARCHAR,
	URL VARCHAR,
	Checksum VARCHAR,
	Filesize INT,
	ModifiedDatetime VARCHAR,
	FOREIGN KEY (CodeLang, Booknum, Chapter) REFERENCES Chapters (CodeLang, Booknum, Chapter) ON DELETE CASCADE,
	PRIMARY KEY (CodeLang, Booknum, Chapter, Quality)
);

CREATE TABLE IF NOT EXISTS Markers (
    CodeLang VARCHAR,
	Booknum INT,
	Chapter INT,
	VerseNumber INT,
	StartTime FLOAT,
	Duration FLOAT,
	EndTransitionDuration FLOAT,
	FOREIGN KEY (CodeLang, Booknum, Chapter) REFERENCES Chapters (CodeLang, Booknum, Chapter) ON DELETE CASCADE,
	PRIMARY KEY (CodeLang, Booknum, Chapter, VerseNumber)
);

CREATE TABLE IF NOT EXISTS SentVerses (
    CodeLang VARCHAR,
	Booknum INT,
	Chapter INT,
	VerseNumbers VARCHAR,
	Quality VARCHAR,
	FileID VARCHAR,
	AddedDatetime VARCHAR,
	FOREIGN KEY (CodeLang, Booknum, Chapter) REFERENCES Chapters (CodeLang, Booknum, Chapter) ON DELETE CASCADE,
    PRIMARY KEY (CodeLang, Booknum, Chapter, Quality, VerseNumbers)
);

CREATE TABLE IF NOT EXISTS Users (
    UserID INT  NOT NULL PRIMARY KEY,
	FullName VARCHAR,
	CodeLang REFERENCES SignLanguages,
	Quality VARCHAR, 
	AddedDatetime VARCHAR
);


INSERT INTO SignLanguages (CodeLang, Locale, Name, Vernacular, RsConfigSymbol, LibrarySymbol)
VALUES ("SCH", "csg", "lengua de señas chilena", "lengua de señas chilena", "r377", "lp-sch");

INSERT INTO Booknames (Booknum, CodeLang, Bookname)
VALUES (1, "SCH", "Génesis");

INSERT INTO Chapters (CodeLang, Booknum, Chapter)
VALUES ("SCH", 1, 3);

INSERT INTO Chapters (CodeLang, Booknum, Chapter)
VALUES ("SCH", 1, 4);

INSERT INTO Files (CodeLang, Booknum, Chapter, Quality, Checksum, URL)
VALUES ("SCH", 1, 3, "720p", "skjdflsdkfdslfkdfkl", "https://jw.org");


DELETE FROM Chapters WHERE Booknum=1;

"""
from datetime import datetime

from sqlalchemy.engine import Engine
from sqlalchemy import Column, Integer, Float, String, ForeignKey, delete, create_engine, ForeignKeyConstraint, event
from sqlalchemy.orm import session, sessionmaker, backref, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import Boolean, Float



@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

Base = declarative_base()

class SignLanguages(Base):
    __tablename__ = 'SignLanguages'
    code_lang = Column('CodeLang', String, primary_key=True)
    locale = Column('Locale', String)
    name = Column('Name', String)
    vernacular = Column('Vernacular', String)
    rsconf = Column('RsConfigSymbol', String)
    lib = Column('LibrarySymbol', String)


class Booknames(Base):
    __tablename__ = 'Booknames'
    booknum = Column('Booknum', Integer, primary_key=True)
    code_lang = Column('CodeLang', String, ForeignKey('SignLanguages.CodeLang'), primary_key=True)
    bookname = Column('Bookname', String)


class Chapters(Base):
    __tablename__ = 'Chapters'
    code_lang = Column('CodeLang', String, primary_key=True)
    booknum = Column('Booknum', Integer, primary_key=True)
    chapter = Column('Chapter', Integer, primary_key=True)
    files = relationship(
        "Files",
        cascade="all,delete",
        back_populates='parent',
        passive_deletes=True,
    )
    markers = relationship(
        'Markers',
        cascade="all,delete",
        back_populates='parent',
        passive_deletes=True,
    )
    sent_verses = relationship(
        'SentVerses',
        cascade="all,delete",
        back_populates='parent',
        passive_deletes=True,
    )
    __table_args__ = (
        ForeignKeyConstraint(
            ['CodeLang', 'Booknum'],
            ['Booknames.CodeLang', 'Booknames.Booknum']
        ),
    )

class Files(Base):
    __tablename__ = 'Files'
    code_lang = Column('CodeLang', String, primary_key=True)
    booknum = Column('Booknum', Integer, primary_key=True)
    chapter = Column('Chapter', Integer, primary_key=True)
    quality = Column('Quality', String, primary_key=True)
    url = Column('URL', String)
    checksum = Column('Checksum', String)
    filesize = Column('Filesize', Integer)
    modified_datetime = Column('ModifiedDatetime', String)
    parent = relationship('Chapters', back_populates='files')
    __table_args__ = (
        ForeignKeyConstraint(
            ['CodeLang', 'Booknum', 'Chapter'],
            ['Chapters.CodeLang', 'Chapters.Booknum', 'Chapters.Chapter'],
            ondelete="CASCADE"
        ),
    )


class Markers(Base):
    __tablename__ = 'Markers'
    code_lang = Column('CodeLang', String, primary_key=True)
    booknum = Column('Booknum', Integer, primary_key=True)
    chapter = Column('Chapter', Integer, primary_key=True)
    versenum = Column('VerseNumber', Integer, primary_key=True)
    start_time = Column('StartTime', Float)
    duration = Column('Duration', Float)
    end_transition_duration = Column('EndTransitionDuration', Float)
    parent = relationship('Chapters', back_populates='markers')
    __table_args__ = (
        ForeignKeyConstraint(
            ['CodeLang', 'Booknum', 'Chapter'],
            ['Chapters.CodeLang', 'Chapters.Booknum', 'Chapters.Chapter'],
            ondelete="CASCADE"
        ),
    )


class SentVerses(Base):
    __tablename__ = 'SentVerses'
    code_lang = Column('CodeLang', String, primary_key=True)
    booknum = Column('Booknum', Integer, primary_key=True)
    chapter = Column('Chapter', Integer, primary_key=True)
    versenums = Column('VerseNumbers', String, primary_key=True)
    quality = Column('Quality', String, primary_key=True)
    file_id = Column('FileID', String)
    added_datetime = Column('AddedDatetime', String)
    parent = relationship('Chapters', back_populates='sent_verses')
    __table_args__ = (
        ForeignKeyConstraint(
            ['CodeLang', 'Booknum', 'Chapter'],
            ['Chapters.CodeLang', 'Chapters.Booknum', 'Chapters.Chapter'],
            ondelete="CASCADE"
        ),
    )


class Users(Base):
    __tablename__ = 'Users'
    user_id = Column('UserID', Integer, primary_key=True)
    full_name = Column('FullName', String)
    code_lang = Column('CodeLang', String, ForeignKey('SignLanguages.CodeLang'))
    quality = Column('Quality', String)
    added_datetime = Column('AddedDatetime', String)


class Foo:
    path = None
    checksum = None
    existing_verses = Boolean
    get_fileid = None
    get_versename = '2 Timoteo 3:1-5, 7. NO VA. SE DEDUCE DE JWBible.citation'
    discard_verses = 'QUIZA NO PORQUE ES INTERNO'
    save = 'commit'
    add_verse = 'sent verse: fileid, addedDatetime etc'


if __name__ == '__main__':
    engine = create_engine(f'sqlite:///{datetime.now().isoformat(timespec="seconds")}.db', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    session.add(SignLanguages(code_lang='SCH', locale='csg'))
    session.flush()

    session.add(Booknames(booknum=1, code_lang='SCH', bookname='Génesis'))
    session.add(Booknames(booknum=40, code_lang='SCH', bookname='Mateo'))
    session.add(Booknames(booknum=43, code_lang='SCH', bookname='Juan'))
    session.flush()

    session.add(Chapters(code_lang='SCH', booknum=1, chapter=4))
    session.add(Chapters(code_lang='SCH', booknum=40, chapter=14))
    session.add(Files(code_lang='SCH', booknum=1, chapter=4, quality='720p', checksum='sdkjfhs', url='https://GENESIS'))
    session.add(Files(code_lang='SCH', booknum=40, chapter=14, quality='720p', checksum='dgdfgsfghgf', url='https://MATEO'))
    session.commit()

    session.add(Markers(code_lang='SCH', booknum=40, chapter=14, versenum=10, start_time=10.5))

    # session.delete(session.query(Chapters).filter(Chapters.booknum == 40)[0])
    session.query(Chapters).filter(Chapters.booknum == 1).delete()
    session.commit()
