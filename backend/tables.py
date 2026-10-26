"""The database tables as SQLAlchemy ORM models. Schema changes go in a new Alembic migration (migrations/).

Child rows (a list's tasks and schedules, a task's notes and checklist) are deleted by the database itself
(ON DELETE CASCADE, switched on in db.py), so deleting a parent never loads its children first."""
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    type_annotation_map = {str: Text}

    def as_dict(self):
        """Every column, keyed by name: the shape the API returns."""
        return {c.key: getattr(self, c.key) for c in self.__table__.columns}


def _text(default=""):
    return mapped_column(default=default, server_default=default)


def _created_at():
    return mapped_column(server_default=func.current_timestamp())  # "YYYY-MM-DD HH:MM:SS" in UTC


class TaskList(Base):
    __tablename__ = "lists"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (Index("idx_tasks_list", "list_id"), {"sqlite_autoincrement": True})

    id: Mapped[int] = mapped_column(primary_key=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("lists.id", ondelete="CASCADE"))
    title: Mapped[str]
    type: Mapped[str] = _text("feature")
    status: Mapped[str] = _text("todo")
    track_envs: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    env: Mapped[str] = _text()
    description: Mapped[str] = _text()
    priority: Mapped[str] = _text()
    due_date: Mapped[str] = _text()
    tags: Mapped[str] = _text()  # comma-separated
    link: Mapped[str] = _text()
    is_pr: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")  # task is a pull request
    schedule_id: Mapped[Optional[int]] = mapped_column(Integer)  # set on tasks created by a schedule
    created_at: Mapped[str] = _created_at()


class Note(Base):
    __tablename__ = "notes"
    __table_args__ = (
        Index("idx_notes_task", "task_id"),
        Index("idx_notes_created", "created_at"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    body: Mapped[str]
    created_at: Mapped[str] = _created_at()


class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    __table_args__ = (Index("idx_items_task", "task_id"), {"sqlite_autoincrement": True})

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    text: Mapped[str]
    done: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")


class Event(Base):
    """One reward. task_id is a task's id, or minus a challenge's id for a challenge bonus."""

    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("task_id", "kind"),
        Index("idx_events_created", "created_at"),
        Index("idx_events_kind", "kind"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str]
    task_id: Mapped[int]
    title: Mapped[str]
    points: Mapped[int]
    task_type: Mapped[str] = _text()
    priority: Mapped[str] = _text()
    created_at: Mapped[str] = _created_at()


class TaskType(Base):
    __tablename__ = "task_types"

    key: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    color: Mapped[str]
    position: Mapped[int]


class KV(Base):
    __tablename__ = "kv"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str]


class Challenge(Base):
    __tablename__ = "challenges"
    __table_args__ = (Index("idx_challenges_day", "day"), {"sqlite_autoincrement": True})

    id: Mapped[int] = mapped_column(primary_key=True)
    day: Mapped[str]
    key: Mapped[str]
    text: Mapped[str]
    target: Mapped[int]
    reward: Mapped[int]
    params: Mapped[str] = _text("{}")  # JSON


class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = _text()  # custom label for the schedule; empty = show the task title
    title: Mapped[str]
    description: Mapped[str] = _text()
    list_id: Mapped[int] = mapped_column(ForeignKey("lists.id", ondelete="CASCADE"))
    type: Mapped[str] = _text()
    priority: Mapped[str] = _text()
    repeat: Mapped[str]  # once | daily | weekly | monthly
    weekdays: Mapped[str] = _text()  # comma-separated, 0 = Monday ... 6 = Sunday
    day_of_month: Mapped[int] = mapped_column(default=1, server_default="1")
    on_date: Mapped[str] = _text()  # YYYY-MM-DD, for "once"
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    last_run: Mapped[str] = _text()  # the game day it last created a task
    created_at: Mapped[str] = _created_at()
