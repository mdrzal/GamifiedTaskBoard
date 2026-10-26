"""Allowed values and request bodies shared by the routers."""
from typing import Literal, Optional

from pydantic import BaseModel, Field

Status = Literal["todo", "in_progress", "done"]
STATUSES = list(Status.__args__)
Env = Literal["dev", "qa", "prd", ""]  # "" = not in any environment
ENVS = [e for e in Env.__args__ if e]
Priority = Literal["", "low", "medium", "high", "critical"]  # "" = not set
PRIORITIES = [p for p in Priority.__args__ if p]
DATE_PATTERN = r"^(\d{4}-\d{2}-\d{2})?$"  # YYYY-MM-DD, or empty for no due date


class ListIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class TaskIn(BaseModel):
    title: str
    type: Optional[str] = None  # defaults to the first task type


class TaskPatch(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    status: Optional[Status] = None
    track_envs: Optional[bool] = None
    env: Optional[Env] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    due_date: Optional[str] = Field(None, pattern=DATE_PATTERN)
    tags: Optional[list[str]] = None
    link: Optional[str] = None
    is_pr: Optional[bool] = None


Repeat = Literal["once", "daily", "weekly", "monthly"]


class ScheduleIn(BaseModel):
    name: str = Field("", max_length=80)  # custom label; empty falls back to the task title
    title: str = Field(min_length=1, max_length=120)
    description: str = ""
    list_id: int
    type: Optional[str] = None  # defaults to the first task type
    priority: Priority = ""
    repeat: Repeat
    weekdays: list[int] = []  # 0 = Monday ... 6 = Sunday (weekly)
    day_of_month: int = Field(1, ge=1, le=31)  # monthly; a short month uses its last day
    on_date: str = Field("", pattern=DATE_PATTERN)  # once
    enabled: bool = True


class SchedulePatch(BaseModel):
    name: Optional[str] = Field(None, max_length=80)
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = None
    list_id: Optional[int] = None
    type: Optional[str] = None
    priority: Optional[Priority] = None
    repeat: Optional[Repeat] = None
    weekdays: Optional[list[int]] = None
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    on_date: Optional[str] = Field(None, pattern=DATE_PATTERN)
    enabled: Optional[bool] = None


class NoteIn(BaseModel):
    body: str


class ItemIn(BaseModel):
    text: str


class ItemPatch(BaseModel):
    text: Optional[str] = None
    done: Optional[bool] = None
