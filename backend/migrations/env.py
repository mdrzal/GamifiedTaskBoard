"""Alembic environment: runs migrations against the app's database (config.DB_PATH)."""
import sys
from logging.config import fileConfig
from pathlib import Path

import sqlalchemy as sa
from alembic import context

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # the backend modules, when run by the alembic CLI

from tables import Base  # noqa: E402

config = context.config


def compare_type(_context, _inspected, _column, inspected_type, metadata_type):
    if isinstance(metadata_type, sa.Boolean) and isinstance(inspected_type, sa.Integer):
        return False  # the models' booleans are stored as 0/1 INTEGER columns: not a change
    return None  # Alembic's usual comparison


def run(connection):
    # render_as_batch: SQLite can't ALTER most things in place, so Alembic rebuilds the table instead
    context.configure(
        connection=connection, target_metadata=Base.metadata, render_as_batch=True, compare_type=compare_type
    )
    with context.begin_transaction():
        context.run_migrations()


connection = config.attributes.get("connection")
if connection is not None:  # started by the app (db.init_db), which keeps its own logging
    run(connection)
else:  # started by the alembic CLI
    if config.config_file_name:
        fileConfig(config.config_file_name)
    from db import engine

    with engine.begin() as connection:
        run(connection)
