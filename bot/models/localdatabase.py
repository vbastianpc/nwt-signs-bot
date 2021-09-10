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
from sqlalchemy import Column, Integer, Float, String, ForeignKey, delete, create_engine
from sqlalchemy.orm import session, sessionmaker, backref, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import Float
from datetime import datetime

engine = create_engine(f'sqlite:///{datetime.now().isoformat(timespec="seconds")}.db', echo=True)
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
    # parent
    __tablename__ = 'Chapters'
    code_lang = Column('CodeLang', String, ForeignKey('Booknames.CodeLang'), primary_key=True)
    booknum = Column('Booknum', Integer, ForeignKey('Booknames.Booknum'), primary_key=True)
    chapter = Column('Chapter', Integer, primary_key=True)
    files = relationship(
        "Files",
        cascade="all,delete",
        # backref='Chapters',
        passive_deletes=True,
        primaryjoin="and_(Chapters.code_lang==Files.code_lang, Chapters.booknum==Files.booknum, Chapters.chapter==Files.chapter)",
        # foreign_keys="[Files.code_lang, Files.booknum, Files.chapter]",
    )

class Files(Base):
    # child
    __tablename__ = 'Files'
    code_lang = Column('CodeLang', String, ForeignKey('Chapters.CodeLang', ondelete="CASCADE"), primary_key=True)
    booknum = Column('Booknum', Integer, ForeignKey('Chapters.Booknum', ondelete="CASCADE"), primary_key=True)
    chapter = Column('Chapter', Integer, ForeignKey('Chapters.Chapter', ondelete="CASCADE"), primary_key=True)
    quality = Column('Quality', String, primary_key=True)
    url = Column('URL', String)
    checksum = Column('Checksum', String)
    filesize = Column('Filesize', Integer)
    modified_datetime = Column('ModifiedDatetime', String)
    # parent = relationship("Chapters", backref=backref('Files', cascade="all,delete"))
    # parent = relationship(
    #     "Chapters",
    #     # backref=backref('Files', cascade="all,delete"),
    #     foreign_keys="[Chapters.code_lang, Chapters.booknum, Chapters.chapter]",
    # )


class Markers(Base):
    __tablename__ = 'Markers'
    code_lang = Column('CodeLang', String, ForeignKey('Chapters.CodeLang'), primary_key=True)
    booknum = Column('Booknum', Integer, ForeignKey('Chapters.Booknum'), primary_key=True)
    chapter = Column('Chapter', Integer, ForeignKey('Chapters.Chapter'), primary_key=True)
    versenum = Column('VerseNumber', Integer, primary_key=True)
    start_time = Column('StartTime', Float)
    duration = Column('Duration', Float)
    end_transition_duration = Column('EndTransitionDuration', Float)


class SentVerses(Base):
    __tablename__ = 'SentVerses'
    code_lang = Column('CodeLang', String, ForeignKey('Chapters.CodeLang'), primary_key=True)
    booknum = Column('Booknum', Integer, ForeignKey('Chapters.Booknum'), primary_key=True)
    chapter = Column('Chapter', Integer, ForeignKey('Chapters.Chapter'), primary_key=True)
    versenums = Column('VerseNumbers', String, primary_key=True)
    quality = Column('Quality', String, primary_key=True)
    file_id = Column('FileID', String)
    added_datetime = Column('AddedDatetime', String)


class Users(Base):
    __tablename__ = 'Users'
    user_id = Column('UserID', Integer, primary_key=True)
    full_name = Column('FullName', String)
    code_lang = Column('CodeLang', String, ForeignKey('SignLanguages.CodeLang'))
    quality = Column('Quality', String)
    added_datetime = Column('AddedDatetime', String)


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    print('Dummy')
    session = Session()

    session.add(SignLanguages(code_lang='SCH', locale='csg'))
    session.add(Booknames(booknum=1, code_lang='SCH', bookname='Génesis'))
    session.add(Chapters(code_lang='SCH', booknum=1, chapter=3))
    session.add(Chapters(code_lang='SCH', booknum=1, chapter=4))
    session.add(Chapters(code_lang='SCH', booknum=7, chapter=4))
    session.add(Files(code_lang='SCH', booknum=1, chapter=4, quality='720p', checksum='sdkjfhs', url='https://fg'))
    session.commit()
    print('Finalizado')
    # session.execute(
    #     delete(Chapters).where(Chapters.booknum == 1)
    # )
    session.query(Chapters).filter(Chapters.booknum == 1).delete()
    session.commit()
    # print('borrado')