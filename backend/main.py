"""TaskBoard API. Run with: uvicorn main:app"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

import config
import db
import scheduler
from routers import lists, schedules, stats, tasks, types

log = logging.getLogger("taskboard")
TICK_SECONDS = 60

db.init_db()


async def _scheduler_loop():
    """Create due scheduled tasks while the server runs, even if no browser is open."""
    while True:
        try:
            await asyncio.to_thread(scheduler.tick)
        except Exception:  # keep ticking; one bad run must not stop the schedule
            log.exception("scheduler tick failed")
        await asyncio.sleep(TICK_SECONDS)


@asynccontextmanager
async def lifespan(_app):
    loop = asyncio.create_task(_scheduler_loop())
    try:
        yield
    finally:
        loop.cancel()


class CachedStatic(StaticFiles):
    """The built Vue app. Its /assets files have a content hash in their name, so browsers may keep them
    for a year; index.html must always be re-checked so a new build is picked up."""

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        if response.status_code in (200, 304):
            immutable = path.replace("\\", "/").startswith("assets/")  # Windows hands over backslashes
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable" if immutable else "no-cache"
        return response


app = FastAPI(title="TaskBoard", lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=500)  # JSON boards and the JS/CSS shrink to about a third
for module in (lists, tasks, types, schedules, stats):
    app.include_router(module.router)

# mounted last so the /api routes above win
if config.STATIC_DIR.is_dir():
    app.mount("/", CachedStatic(directory=config.STATIC_DIR, html=True), name="static")
