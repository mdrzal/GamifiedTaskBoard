"""Tasks, and the notes and checklist items that belong to them."""
from collections import defaultdict

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select

import game
import task_types
from db import get_db, require
from models import ItemIn, ItemPatch, NoteIn, TaskIn, TaskPatch
from tables import ChecklistItem, Note, Task, TaskList

router = APIRouter(prefix="/api", tags=["tasks"])


def clean_tags(tags):
    """Trim, drop empties and duplicates (case-insensitive), and strip the comma separator."""
    seen, out = set(), []
    for tag in (t.replace(",", " ").strip() for t in tags):
        if tag and tag.lower() not in seen:
            seen.add(tag.lower())
            out.append(tag)
    return out


def _by_task(db, model, task_ids):
    """Rows of notes / checklist items as dicts, grouped by task id."""
    grouped = defaultdict(list)
    for row in db.execute(select(model.__table__).where(model.task_id.in_(task_ids)).order_by(model.id)):
        grouped[row.task_id].append(dict(row._mapping))
    return grouped


def load_tasks(db, task_ids=None, list_id=None):
    """Tasks in the shape the API returns: tags decoded, notes and checklist attached. Plain rows rather than
    ORM objects, and three queries in all (not one per task): a big board loads several times faster."""
    if list_id is not None:
        ids = select(Task.id).where(Task.list_id == list_id)
        query = select(Task.__table__).where(Task.list_id == list_id).order_by(Task.id.desc())
    else:
        ids = task_ids
        query = select(Task.__table__).where(Task.id.in_(task_ids))
    tasks = [dict(row._mapping) for row in db.execute(query)]
    notes = _by_task(db, Note, ids)
    items = _by_task(db, ChecklistItem, ids)
    for task in tasks:
        task["tags"] = [tag for tag in task["tags"].split(",") if tag]
        task["notes"] = notes[task["id"]]
        task["items"] = items[task["id"]]
    return tasks


# ---- tasks ----

@router.get("/lists/{list_id}/tasks")
def get_tasks(list_id: int, db=Depends(get_db)):
    require(db, TaskList, list_id)
    # JSONResponse skips FastAPI's recursive re-encoding of an already JSON-ready structure: much faster
    # for a big board
    return JSONResponse(load_tasks(db, list_id=list_id))


@router.post("/lists/{list_id}/tasks", status_code=201)
def create_task(list_id: int, body: TaskIn, db=Depends(get_db)):
    require(db, TaskList, list_id)
    type_key = task_types.require_key(db, body.type) if body.type else task_types.first_key(db)
    task = Task(list_id=list_id, title=body.title.strip(), type=type_key)
    db.add(task)
    db.flush()  # assigns the id
    return load_tasks(db, task_ids=[task.id])[0]


@router.patch("/tasks/{task_id}")
def update_task(task_id: int, body: TaskPatch, db=Depends(get_db)):
    task = require(db, Task, task_id)
    fields = body.model_dump(exclude_none=True)
    if "type" in fields:
        task_types.require_key(db, fields["type"])
    if fields.get("env") == "prd" and "status" not in fields:
        fields["status"] = "done"  # a task that reached production is finished
    if "tags" in fields:
        fields["tags"] = ",".join(clean_tags(fields["tags"]))
    if fields:
        for name, value in fields.items():  # only TaskPatch's fields, all of them Task columns
            setattr(task, name, value)
        game.sync_task_events(db, task, fields)
    return load_tasks(db, task_ids=[task_id])[0]


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db=Depends(get_db)):
    db.delete(require(db, Task, task_id))


# ---- notes ----

@router.post("/tasks/{task_id}/notes", status_code=201)
def add_note(task_id: int, body: NoteIn, db=Depends(get_db)):
    require(db, Task, task_id)
    note = Note(task_id=task_id, body=body.body.strip())
    db.add(note)
    game.sync_challenges(db)  # a note can complete a "leave notes" challenge
    return note.as_dict()


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int, db=Depends(get_db)):
    db.delete(require(db, Note, note_id))
    game.sync_challenges(db)  # removing a note can undo a "leave notes" challenge


# ---- checklist ----

@router.post("/tasks/{task_id}/items", status_code=201)
def add_item(task_id: int, body: ItemIn, db=Depends(get_db)):
    require(db, Task, task_id)
    item = ChecklistItem(task_id=task_id, text=body.text.strip())
    db.add(item)
    db.flush()  # assigns the id
    return item.as_dict()


@router.patch("/items/{item_id}")
def update_item(item_id: int, body: ItemPatch, db=Depends(get_db)):
    item = require(db, ChecklistItem, item_id)
    for name, value in body.model_dump(exclude_none=True).items():  # only text / done
        setattr(item, name, value)
    return item.as_dict()


@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, db=Depends(get_db)):
    db.delete(require(db, ChecklistItem, item_id))
