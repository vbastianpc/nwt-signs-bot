from sqlalchemy.orm import session, sessionmaker
from sqlalchemy import create_engine


from schemedb import ( # pylint: disable=import-error
    SignLanguages, Booknames, Chapters, Files, Markers,
    SentVerses, Users, PATH_DB, Base
)
from jwpubmedia import BiblePassage # pylint: disable=import-error


engine = create_engine(f'sqlite:///{PATH_DB}', echo=True)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

class LocalDatabase:
    def __init__(self, passage: BiblePassage):
        self.session = Session()
        self.passage = passage

    @property
    def checksum(self):
        pass



class Foo:
    path = None
    checksum = None
    existing_verses = bool
    get_fileid = None
    get_versename = '2 Timoteo 3:1-5, 7. NO VA. SE DEDUCE DE JWBible.citation'
    discard_verses = 'QUIZA NO PORQUE ES INTERNO'
    save = 'commit'
    add_verse = 'sent verse: fileid, addedDatetime etc'


if __name__ == '__main__':
    pass