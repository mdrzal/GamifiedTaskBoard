# TaskBoard

Project to manage tasks in a kanban board style. Gamify your work with XP, streaks and daily challenges.
Built with the help of Claude Code.

Simple task tracker: FastAPI + SQLite (via the SQLAlchemy ORM) backend, Vue 3 frontend, one Docker container.

- Multiple lists, a kanban board (To Do / In Progress / Done) with drag and drop.
- Task types you can edit in **Settings** (⚙): rename, recolour, reorder, add, delete.
- Optional per-task details: description, priority, due date, tags, link, "is a PR", checklist, notes,
  and DEV / QA / PRD environment tracking. Moving a task to PRD moves it to Done.
- Filters: type, priority, due date, environment, tag, PRs only, plus search.
- **This week** panel on the left: today's date, the current week with how many tasks are due each day
  (click a day to filter the board to it) and an overdue shortcut.
- **Scheduled tasks** (Settings): create a task automatically on chosen days, e.g. a weekly time report.
- Destructive actions (deleting a list, task, type or schedule) ask first, in an in-app dialog.
- Light and dark themes.

## Scheduled tasks

Settings → *Scheduled tasks*. A schedule creates a task in To Do on the days you pick, with that day as its
due date: **once** on a date, **daily**, **weekly** on chosen weekdays, or **monthly** on a day (31 uses the
last day of short months). Titles and descriptions can use `{date}` `{weekday}` `{month}` `{year}` `{week}`,
so "Time report – week {week}" becomes "Time report – week 43".

- Saving a schedule creates today's task straight away if today is one of its days. *Run now* creates one
  on demand; *Pause* stops it.
- The server checks every minute, so tasks appear on time even if no browser is open.
- A day starts at 01:00 (like game days). Missed days are not backfilled, except a one-off whose date passed.
- Tasks made by a schedule show a "↻ scheduled" badge and stay if you delete the schedule.

## Game

Finishing work earns XP: resolving a task (+10, more for high priority) and moving it into DEV, QA or PRD.
Undoing progress (moving a task out of Done, or back to an earlier environment) takes the XP back.

- The **game day** starts at 01:00, so working past midnight still counts for the same day.
- **Level resets each day** and every level gets a random silly name that changes day to day.
- Three **random daily challenges** are created on the first use after 01:00 and pay bonus XP.
- Streaks, totals and milestones carry on across days.
- Daily goal and sound are in Settings. Sound is off by default.

## Run with Docker

    docker compose up -d --build

Open http://localhost:8000.

On Windows, `.\run.ps1` does the same and opens the browser.

## Develop locally

    # backend (from backend/)
    pip install -r requirements.txt
    uvicorn main:app --reload

    # frontend (from frontend/), proxies /api to :8000
    npm install
    npm run dev
