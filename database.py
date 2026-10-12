import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker

engine = create_engine("sqlite:///database/database.db")

Session = scoped_session(sessionmaker(autoflush=False, bind=engine))


@event.listens_for(engine, "connect")
def on_connect(dbapi_connection: sqlite3.Connection, _):
    autocommit = dbapi_connection.autocommit
    dbapi_connection.autocommit = True

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()

    dbapi_connection.autocommit = autocommit


class Base(DeclarativeBase):
    pass
