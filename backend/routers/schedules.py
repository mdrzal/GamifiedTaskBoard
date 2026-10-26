"""Scheduled tasks: create, edit, pause, delete, and run one right now."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

import scheduler
import task_types
from db import get_db, require
from models import ScheduleIn, SchedulePatch
from routers.tasks import load_tasks
from tables import Schedule, TaskList

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


def _out(db, schedule, today):
    task_list = db.get(TaskList, schedule.list_id)
    return {
        **schedule.as_dict(),
        "weekdays": scheduler.weekday_list(schedule.weekdays),
        "next_run": scheduler.next_run(schedule, today),
        "list_name": task_list.name if task_list else "",
    }


def _validate(db, data):
    """Check a complete schedule (cross-field rules) and normalise it for storage."""
    require(db, TaskList, data["list_id"])
    data["type"] = task_types.require_key(db, data["type"]) if data.get("type") else task_types.first_key(db)
    days = sorted(set(data["weekdays"]))
    if any(d < 0 or d > 6 for d in days):
        raise HTTPException(422, "Weekdays must be 0 (Monday) to 6 (Sunday)")
    if data["repeat"] == "weekly" and not days:
        raise HTTPException(422, "Pick at least one weekday")
    if data["repeat"] == "once" and not data["on_date"]:
        raise HTTPException(422, "Pick the date for a one-off task")
    data["name"] = data["name"].strip()
    data["weekdays"] = ",".join(str(d) for d in days)
    return data


@router.get("")
def list_schedules(db=Depends(get_db)):
    today = scheduler.today_for(db)
    return [_out(db, s, today) for s in db.scalars(select(Schedule).order_by(Schedule.id))]


@router.post("", status_code=201)
def create_schedule(body: ScheduleIn, db=Depends(get_db)):
    schedule = Schedule(**_validate(db, body.model_dump()))
    db.add(schedule)
    scheduler.run_due(db)  # if today is one of its days, the task appears right away
    return _out(db, schedule, scheduler.today_for(db))


@router.patch("/{schedule_id}")
def update_schedule(schedule_id: int, body: SchedulePatch, db=Depends(get_db)):
    schedule = require(db, Schedule, schedule_id)
    current = {name: getattr(schedule, name) for name in ScheduleIn.model_fields}
    current["weekdays"] = scheduler.weekday_list(current["weekdays"])
    data = _validate(db, {**current, **body.model_dump(exclude_none=True)})
    for name, value in data.items():  # only ScheduleIn's fields, all of them Schedule columns
        setattr(schedule, name, value)
    scheduler.run_due(db)
    return _out(db, schedule, scheduler.today_for(db))


@router.delete("/{schedule_id}", status_code=204)
def delete_schedule(schedule_id: int, db=Depends(get_db)):
    db.delete(require(db, Schedule, schedule_id))  # tasks it already created stay


@router.post("/{schedule_id}/run", status_code=201)
def run_now(schedule_id: int, db=Depends(get_db)):
    """Create the task now, whatever today is (and count it as today's run)."""
    schedule = require(db, Schedule, schedule_id)
    task_id = scheduler.create_task(db, schedule, scheduler.today_for(db))
    return load_tasks(db, task_ids=[task_id])[0]
