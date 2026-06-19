from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.sql import text

from bot.database.schema import Base, Bible, Language, Edition, Book, Chapter, VideoMarker, File, User, File2User
from bot.database.views import views


PATH_DB = Path(__file__).parent.parent.parent / 'database.db'

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=OFF")
    cursor.close()


def start_database(db: Path | str = PATH_DB):
    engine = create_engine(rf'sqlite:///{db}', echo=False)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    with engine.connect() as con:
        for view in views:
            con.execute(text(view))
    session_factory = sessionmaker(bind=engine)
    return session_factory()


session = start_database()


def rollback_session():
    """Recover from a broken session state (e.g. after IntegrityError)."""
    try:
        session.rollback()
    except Exception:
        pass
