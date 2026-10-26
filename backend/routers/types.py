"""Task types: list, create, edit, reorder, delete."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update

import game
from db import get_db
from tables import Task, TaskType
from task_types import HEX, keys, require_key, slugify

router = APIRouter(prefix="/api/types", tags=["types"])


class TypeIn(BaseModel):
    name: str = Field(min_length=1, max_length=30)
    color: str = Field(pattern=HEX)


class TypePatch(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=30)
    color: Optional[str] = Field(None, pattern=HEX)


class Reorder(BaseModel):
    keys: list[str]


def _rows(db):
    count = select(func.count(Task.id)).where(Task.type == TaskType.key).scalar_subquery()
    rows = db.execute(
        select(TaskType.key, TaskType.name, TaskType.color, TaskType.position, count.label("count"))
        .order_by(TaskType.position, TaskType.key)
    )
    return [dict(r._mapping) for r in rows]


def _one(db, key):
    return next(r for r in _rows(db) if r["key"] == key)


def _name_taken(db, name, except_key=None):
    same_name = func.lower(TaskType.name) == func.lower(name)
    return db.scalar(select(TaskType.key).where(same_name, TaskType.key != (except_key or ""))) is not None


@router.get("")
def list_types(db=Depends(get_db)):
    return _rows(db)


@router.post("", status_code=201)
def create_type(body: TypeIn, db=Depends(get_db)):
    name = body.name.strip()
    if not name or _name_taken(db, name):
        raise HTTPException(409, f"A task type named '{name}' already exists")
    key = slugify(name, set(keys(db)))
    position = db.scalar(select(func.coalesce(func.max(TaskType.position), -1) + 1))
    db.add(TaskType(key=key, name=name, color=body.color.lower(), position=position))
    return _one(db, key)


# registered before the "/{key}" routes so "reorder" is never read as a key
@router.post("/reorder")
def reorder_types(body: Reorder, db=Depends(get_db)):
    if sorted(body.keys) != sorted(keys(db)):
        raise HTTPException(422, "Reorder must list every task type exactly once")
    for position, key in enumerate(body.keys):
        db.get(TaskType, key).position = position
    return _rows(db)


@router.patch("/{key}")
def update_type(key: str, body: TypePatch, db=Depends(get_db)):
    task_type = db.get(TaskType, require_key(db, key))
    fields = body.model_dump(exclude_none=True)
    if "name" in fields:
        fields["name"] = fields["name"].strip()
        if not fields["name"] or _name_taken(db, fields["name"], key):
            raise HTTPException(409, f"A task type named '{fields['name']}' already exists")
    if "color" in fields:
        fields["color"] = fields["color"].lower()
    for name, value in fields.items():  # only name / color
        setattr(task_type, name, value)
    if "name" in fields:  # keep the wording of existing daily challenges in step with the new name
        game.rename_type_challenges(db, key, fields["name"])
    return _one(db, key)


@router.delete("/{key}", status_code=204)
def delete_type(key: str, move_to: Optional[str] = None, db=Depends(get_db)):
    require_key(db, key)
    if len(keys(db)) == 1:
        raise HTTPException(400, "You need at least one task type")
    used = db.scalar(select(func.count()).select_from(Task).where(Task.type == key))
    if used:
        if not move_to or move_to == key or move_to not in keys(db):
            raise HTTPException(409, f"{used} task(s) use this type; choose another type to move them to")
        db.execute(update(Task).where(Task.type == key).values(type=move_to))
    game.drop_type_challenges(db, key)  # a challenge for a type that no longer exists can't be finished
    db.delete(db.get(TaskType, key))
