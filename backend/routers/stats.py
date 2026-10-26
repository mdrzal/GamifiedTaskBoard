"""Static choices for the UI, and the game stats."""
from fastapi import APIRouter, Depends

import game
from db import get_db
from models import ENVS, PRIORITIES, STATUSES

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/meta")
def meta():
    return {"statuses": STATUSES, "envs": ENVS, "priorities": PRIORITIES}


@router.get("/stats")
def get_stats(tz: int = 0, db=Depends(get_db)):
    """Gamification stats. `tz` is the browser's getTimezoneOffset(), so "today" means the user's day."""
    return game.compute_stats(db, tz)
