
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.engine import Engine

from bot.database.schema import Base
from bot.database.views import views


PATH_DB = 'newlanguages.db'
# PATH_DB = 'test_database.db'

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def start_database() -> scoped_session:
    engine = create_engine(rf'sqlite:///{PATH_DB}', echo=False)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    with engine.connect() as con:
        for view in views:
            con.execute(view)
    return scoped_session(sessionmaker(bind=engine))()


SESSION = start_database()
