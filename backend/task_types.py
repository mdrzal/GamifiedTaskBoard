"""Task-type data helpers. `key` is the stable id stored on tasks; name, colour and order are editable.
The HTTP routes are in routers/types.py."""
import re

from fastapi import HTTPException
from sqlalchemy import func, select

from tables import TaskType

HEX = r"^#[0-9a-fA-F]{6}$"

DEFAULT_TYPES = [
    ("task", "Task", "#9aa5ce"),
    ("meeting", "Meeting", "#2de2a6"),
    ("personal", "Personal", "#ff8fa3"),
    ("feature", "Feature", "#b967ff"),
    ("bug", "Bug", "#ff2a6d"),
    ("chore", "Chore", "#fcee0a"),
    ("refactor", "Refactor", "#05d9e8"),
    ("docs", "Docs", "#4d7cff"),
    ("research", "Research", "#ff9f1c"),
    ("other", "Other", "#c0c4d6"),
]


def seed(db):
    """Fill an empty table with the defaults (first start, or an upgrade from the fixed type list)."""
    if db.scalar(select(func.count()).select_from(TaskType)) == 0:
        db.add_all(
            TaskType(key=k, name=n, color=c, position=i) for i, (k, n, c) in enumerate(DEFAULT_TYPES)
        )


def keys(db):
    return db.scalars(select(TaskType.key).order_by(TaskType.position, TaskType.key)).all()


def first_key(db):
    found = keys(db)
    if not found:
        raise HTTPException(409, "No task types exist; create one in Settings first")
    return found[0]


def require_key(db, key):
    if key not in keys(db):
        raise HTTPException(422, f"Unknown task type '{key}'")
    return key


def slugify(name, taken):
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "type"
    key, n = base, 2
    while key in taken:
        key = f"{base}-{n}"
        n += 1
    return key
