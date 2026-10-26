"""Scheduled tasks: rules that create a task on specific days, e.g. "time report spreadsheet" every Friday.

Days are game days (they turn over at 01:00 local time, like levels and daily challenges). A rule creates
at most one task per game day. If the app was off on a due day it does not backfill recurring rules, but a
one-off rule whose date has passed is created the next time the app runs.
"""
import calendar
from datetime import timedelta

from sqlalchemy import select

import db as database
import game
import task_types
from tables import Schedule, Task

PLACEHOLDERS = "{date} {weekday} {month} {year} {week}"


def render(text, day):
    """Fill {date} {weekday} {month} {year} {week} so a title can say what it is for."""
    values = {
        "{date}": day.isoformat(),
        "{weekday}": day.strftime("%A"),
        "{month}": day.strftime("%B"),
        "{year}": str(day.year),
        "{week}": str(day.isocalendar()[1]),
    }
    for key, value in values.items():
        text = text.replace(key, value)
    return text


def weekday_list(text):
    return [int(w) for w in text.split(",") if w != ""]


def is_due(schedule, day):
    """Should this rule create a task on game day `day`?"""
    if not schedule.enabled or schedule.last_run == day.isoformat():
        return False
    repeat = schedule.repeat
    if repeat == "once":
        return bool(schedule.on_date) and schedule.last_run == "" and schedule.on_date <= day.isoformat()
    if repeat == "daily":
        return True
    if repeat == "weekly":
        return day.weekday() in weekday_list(schedule.weekdays)
    if repeat == "monthly":
        return day.day == min(schedule.day_of_month, calendar.monthrange(day.year, day.month)[1])
    return False


def next_run(schedule, today, horizon=800):
    """The next game day a task will be created (today counts until the rule has run today)."""
    if not schedule.enabled:
        return None
    if schedule.repeat == "once":
        if schedule.last_run or not schedule.on_date:
            return None
        return max(schedule.on_date, today.isoformat())  # a missed date runs on the next opportunity
    for offset in range(horizon):
        day = today + timedelta(days=offset)
        if is_due(schedule, day):
            return day.isoformat()
    return None


def create_task(db, schedule, day):
    """Create the task for `day` and remember it, so the rule can't fire twice on the same day."""
    type_key = schedule.type if schedule.type in task_types.keys(db) else task_types.first_key(db)
    task = Task(
        list_id=schedule.list_id, title=render(schedule.title, day), type=type_key, priority=schedule.priority,
        description=render(schedule.description, day), due_date=day.isoformat(), schedule_id=schedule.id,
    )
    db.add(task)
    schedule.last_run = day.isoformat()
    db.flush()  # assigns the task its id
    return task.id


def today_for(db, now=None):
    now = now or game._utcnow()
    return game.game_day(now - timedelta(minutes=game.get_tz(db)))


def run_due(db, now=None):
    """Create the tasks that are due today. Safe to call as often as you like."""
    day = today_for(db, now)
    created = []
    for schedule in db.scalars(select(Schedule).where(Schedule.enabled)).all():
        if is_due(schedule, day):
            created.append(create_task(db, schedule, day))
    return created


def tick():
    """One pass of the background loop, in its own session."""
    with database.Session.begin() as db:
        return run_due(db)
