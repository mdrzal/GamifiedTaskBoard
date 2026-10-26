"""Baseline: the schema as it was before Alembic.

Databases from before Alembic have no version yet, and may come from any earlier release, so this step
only creates what is missing: every table, and the columns and indexes that later releases added.
On a fresh database it simply creates everything.

Revision ID: 0001
Revises:
Create Date: 2026-10-25
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

ENVS = ["dev", "qa", "prd"]


def _text(name, default=""):
    return sa.Column(name, sa.Text(), nullable=False, server_default=default)


def _flag(name, default):
    return sa.Column(name, sa.Integer(), nullable=False, server_default=str(default))


def _id():
    return sa.Column("id", sa.Integer(), primary_key=True)


def _created_at():
    return sa.Column("created_at", sa.Text(), nullable=False, server_default=sa.func.current_timestamp())


# Optional task details. Tables created before they existed get them added below.
DETAIL_COLUMNS = [
    lambda: _text("description"),
    lambda: _text("priority"),
    lambda: _text("due_date"),
    lambda: _text("tags"),
    lambda: _text("link"),
    lambda: _flag("is_pr", 0),
    lambda: sa.Column("schedule_id", sa.Integer()),
]

TABLES = {
    "lists": lambda: [_id(), _text("name", None)],
    "tasks": lambda: [
        _id(),
        sa.Column("list_id", sa.Integer(), sa.ForeignKey("lists.id", ondelete="CASCADE"), nullable=False),
        _text("title", None),
        _text("type", "feature"),
        _text("status", "todo"),
        _flag("track_envs", 0),
        _text("env"),
        *(make() for make in DETAIL_COLUMNS),
        _created_at(),
    ],
    "notes": lambda: [
        _id(),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        _text("body", None),
        _created_at(),
    ],
    "checklist_items": lambda: [
        _id(),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        _text("text", None),
        _flag("done", 0),
    ],
    "events": lambda: [
        _id(),
        _text("kind", None),
        sa.Column("task_id", sa.Integer(), nullable=False),
        _text("title", None),
        sa.Column("points", sa.Integer(), nullable=False),
        _text("task_type"),
        _text("priority"),
        _created_at(),
        sa.UniqueConstraint("task_id", "kind"),
    ],
    "task_types": lambda: [
        sa.Column("key", sa.Text(), primary_key=True),
        _text("name", None),
        _text("color", None),
        sa.Column("position", sa.Integer(), nullable=False),
    ],
    "kv": lambda: [sa.Column("key", sa.Text(), primary_key=True), _text("value", None)],
    "challenges": lambda: [
        _id(),
        _text("day", None),
        _text("key", None),
        _text("text", None),
        sa.Column("target", sa.Integer(), nullable=False),
        sa.Column("reward", sa.Integer(), nullable=False),
        _text("params", "{}"),
    ],
    "schedules": lambda: [
        _id(),
        _text("name"),
        _text("title", None),
        _text("description"),
        sa.Column("list_id", sa.Integer(), sa.ForeignKey("lists.id", ondelete="CASCADE"), nullable=False),
        _text("type"),
        _text("priority"),
        _text("repeat", None),
        _text("weekdays"),
        sa.Column("day_of_month", sa.Integer(), nullable=False, server_default="1"),
        _text("on_date"),
        _flag("enabled", 1),
        _text("last_run"),
        _created_at(),
    ],
}

# lookups the app does constantly (a board loads its tasks, notes and checklist by these)
INDEXES = [
    ("idx_tasks_list", "tasks", "list_id"),
    ("idx_notes_task", "notes", "task_id"),
    ("idx_notes_created", "notes", "created_at"),
    ("idx_items_task", "checklist_items", "task_id"),
    ("idx_events_created", "events", "created_at"),
    ("idx_events_kind", "events", "kind"),
    ("idx_challenges_day", "challenges", "day"),
]


def _inspect():
    return sa.inspect(op.get_bind())  # a fresh inspector each time: one caches what it has read


def upgrade():
    existing = set(_inspect().get_table_names())
    for name, columns in TABLES.items():
        if name not in existing:
            op.create_table(name, *columns(), sqlite_autoincrement=name not in ("task_types", "kv"))

    def columns(table):
        return {c["name"] for c in _inspect().get_columns(table)}

    tasks = columns("tasks")
    if "track_envs" not in tasks:  # created before environment tracking existed
        op.add_column("tasks", _flag("track_envs", 0))
        op.add_column("tasks", _text("env"))
    elif "env" not in tasks:  # an earlier multi-select version stored a comma list in `envs`
        op.add_column("tasks", _text("env"))
        _env_from_envs()

    tasks = columns("tasks")
    for make in DETAIL_COLUMNS:
        column = make()
        if column.name not in tasks:
            op.add_column("tasks", column)

    events = columns("events")
    for name in ("task_type", "priority"):  # events written before challenges tracked these
        if name not in events:
            op.add_column("events", _text(name))

    if "name" not in columns("schedules"):  # schedules made before they could be named
        op.add_column("schedules", _text("name"))

    for name, table, column in INDEXES:
        if name not in {i["name"] for i in _inspect().get_indexes(table)}:
            op.create_index(name, table, [column])


def _env_from_envs():
    """Keep the furthest environment of the old comma list."""
    tasks = sa.table("tasks", sa.column("id"), sa.column("envs"), sa.column("env"))
    bind = op.get_bind()
    for task_id, envs in bind.execute(sa.select(tasks.c.id, tasks.c.envs).where(tasks.c.envs != "")).all():
        furthest = max((e for e in envs.split(",") if e in ENVS), key=ENVS.index, default="")
        bind.execute(sa.update(tasks).where(tasks.c.id == task_id).values(env=furthest))


def downgrade():
    raise NotImplementedError("The baseline can't be undone; restore a backup of the database instead.")
