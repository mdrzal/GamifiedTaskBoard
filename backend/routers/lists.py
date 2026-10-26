"""Task lists."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func, select

from db import get_db, require
from models import ListIn
from tables import Task, TaskList

router = APIRouter(prefix="/api/lists", tags=["lists"])


def _clean_name(body):
    name = body.name.strip()
    if not name:
        raise HTTPException(422, "A list needs a name")
    return name


@router.get("")
def get_lists(db=Depends(get_db)):
    rows = db.execute(
        select(
            TaskList.id,
            TaskList.name,
            func.count(Task.id).label("total"),
            func.coalesce(func.sum(case((Task.status == "done", 1), else_=0)), 0).label("done"),
        )
        .outerjoin(Task, Task.list_id == TaskList.id)
        .group_by(TaskList.id)
        .order_by(TaskList.id)
    )
    return [dict(r._mapping) for r in rows]


@router.post("", status_code=201)
def create_list(body: ListIn, db=Depends(get_db)):
    task_list = TaskList(name=_clean_name(body))
    db.add(task_list)
    db.flush()  # assigns the id
    return {"id": task_list.id, "name": task_list.name, "total": 0, "done": 0}


@router.patch("/{list_id}")
def rename_list(list_id: int, body: ListIn, db=Depends(get_db)):
    task_list = require(db, TaskList, list_id)
    task_list.name = _clean_name(body)
    return {"id": list_id, "name": task_list.name}


@router.delete("/{list_id}", status_code=204)
def delete_list(list_id: int, db=Depends(get_db)):
    db.delete(require(db, TaskList, list_id))  # the database deletes its tasks and schedules with it
