"""Database engine and sessions, startup migrations and a small lookup helper."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import task_types
from config import DB_PATH

HERE = Path(__file__).parent

# FastAPI runs a dependency's setup and teardown on different threads
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
Session = sessionmaker(engine)


@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_connection, _record):
    """SQLite only enforces foreign keys (and so cascading deletes) when asked to, per connection."""
    dbapi_connection.execute("PRAGMA foreign_keys = ON")


def get_db():
    """FastAPI dependency: one session per request, committed when the request succeeds."""
    with Session() as db:
        yield db
        db.commit()


def require(db, model, key):
    """Fetch a row by primary key or raise a 404."""
    row = db.get(model, key)
    if row is None:
        raise HTTPException(404, f"{model.__tablename__[:-1]} not found")
    return row


def init_db():
    """Create missing tables and bring databases made by older versions up to date."""
    config = Config(str(HERE / "alembic.ini"))
    config.set_main_option("script_location", str(HERE / "migrations"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    with Session.begin() as db:
        task_types.seed(db)
