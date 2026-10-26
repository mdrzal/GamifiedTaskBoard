"""XP, daily levels, streaks, achievements and random daily challenges.

Everything is derived from an `events` table: one row per reward (resolving a task, pushing it to an
environment, finishing a daily challenge). A task earns each kind of reward once, and undoing the
progress (moving it out of Done, or back to an earlier environment) deletes the reward again, so XP
can neither be farmed by moving cards around nor kept after the work is undone. Events for deleted
tasks stay, so removing a finished task never costs you its XP.

A "game day" starts at 01:00 local time, not midnight: working past midnight still counts for the
same day. Level and XP reset each game day; streaks, totals and milestones carry on.
"""
import json
import random
from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.sqlite import insert

from tables import KV, Challenge, Event, Note, Task, TaskType

DAY_START_HOUR = 1
DONE_POINTS = 10
PRIORITY_BONUS = {"": 0, "low": 0, "medium": 2, "high": 5, "critical": 10}
ENV_ORDER = ["dev", "qa", "prd"]  # a task moves through these in this order
ENV_POINTS = {"dev": 3, "qa": 5, "prd": 15}
LEVEL_STEP = 25  # today's XP needed for level n is LEVEL_STEP * (n - 1) ** 2
DAILY_CHALLENGES = 3
RECENT_WINS = 8

SILLY_NAMES = [
    "Sir Procrastinate-a-Lot", "Captain Checkbox", "Baron von Backlog", "Duke of Deadlines",
    "Lord Latte Sipper", "Sergeant Snooze", "Admiral Autocomplete", "Professor Pixel Pants",
    "Count Commit", "Grand Poobah of Pull Requests", "Dr. Debug McBugface", "Nacho Average Dev",
    "The Rubber Duck Whisperer", "Keyboard Warrior Princess", "Master of Merge Conflicts",
    "Supreme Overlord of Unread Emails", "Chief Coffee Officer", "Ctrl+Z Champion", "Sir Scrolls-a-Lot",
    "Lady Lint-a-Lot", "Bug Squisher 9000", "Captain Copy-Paste", "Stack Overflow Sensei",
    "Reverend of the Refactor", "Generalissimo Git", "Majestic Mouse Clicker", "Wizard of Whoops",
    "Lieutenant Lorem Ipsum", "Emperor of Edge Cases", "Tab Hoarder Supreme", "Baroness of Boilerplate",
    "The Notorious N.P.M.", "Sir Sudo Make-Me-a-Sandwich", "Princess Pull-Request", "Colonel Cache Miss",
    "Maestro of the Meeting", "Knight of the Null Pointer", "Jedi Master of Jira", "Queen of Quick Fixes",
    "Doctor Dependency Hell", "Gandalf the Greybeard Coder", "The Yak Shaver", "Archduke of Alt-Tab",
    "Commander Cron Job", "Duchess of Dark Mode", "Sir Loops-a-Lot", "The Semicolon Slayer",
    "Fiona the Fire-Drill Fighter", "Mr. Whiskers' Intern", "Admiral Ackbar's Sprint Planner",
]


# ---------- time ----------

def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def set_tz(db, minutes):
    row = db.get(KV, "tz")
    if row and int(row.value) == minutes:
        return  # unchanged: skip the write, which would force a disk sync on every stats call
    upsert = insert(KV).values(key="tz", value=str(minutes))
    db.execute(upsert.on_conflict_do_update(index_elements=[KV.key], set_={"value": upsert.excluded.value}))


def get_tz(db):
    row = db.get(KV, "tz")
    return int(row.value) if row else 0


def _local(ts, offset):
    return datetime.fromisoformat(ts) - offset


def game_day(local_dt):
    """The game day a local wall-clock time belongs to (the day only turns over at DAY_START_HOUR)."""
    return (local_dt - timedelta(hours=DAY_START_HOUR)).date()


# ---------- levels ----------

def level_name(day, level):
    """Silly names, shuffled differently each game day so the same level is a new joke tomorrow."""
    order = SILLY_NAMES[:]
    random.Random(day.isoformat()).shuffle(order)
    return order[(level - 1) % len(order)]


def level_info(xp, day):
    level = int((xp / LEVEL_STEP) ** 0.5) + 1
    return {
        "level": level,
        "level_name": level_name(day, level),
        "level_floor": LEVEL_STEP * (level - 1) ** 2,
        "level_next": LEVEL_STEP * level**2,
    }


# ---------- events ----------

def _stamp(now):
    return (now or _utcnow()).strftime("%Y-%m-%d %H:%M:%S")


def _add_event(db, now, **values):
    """Record a reward, unless this task (or challenge) already has one of this kind."""
    db.execute(insert(Event).values(**values, created_at=_stamp(now)).on_conflict_do_nothing())


def award(db, task, kind, points, now=None):
    _add_event(
        db, now, kind=kind, task_id=task.id, title=task.title, points=points, task_type=task.type,
        priority=task.priority,
    )


def revoke(db, task_id, kind):
    db.execute(delete(Event).where(Event.task_id == task_id, Event.kind == kind))


def sync_task_events(db, task, fields, now=None, rng=None):
    """Called after a task was updated with `fields`; `task` is the Task as it is now."""
    if "status" in fields:
        if fields["status"] == "done":
            award(db, task, "done", DONE_POINTS + PRIORITY_BONUS.get(task.priority, 0), now)
        else:
            revoke(db, task.id, "done")
    if "env" in fields:
        env = fields["env"]
        reached = ENV_ORDER.index(env) if env in ENV_ORDER else -1
        for i, e in enumerate(ENV_ORDER):
            if i > reached:  # moving back (or out of) an environment takes its XP away
                revoke(db, task.id, f"env_{e}")
        if env in ENV_POINTS:
            award(db, task, f"env_{env}", ENV_POINTS[env], now)
    sync_challenges(db, now, rng)


# ---------- daily challenges ----------

def _clock(e, offset):
    return _local(e.created_at, offset)


def _day_window(day, offset):
    """The UTC [start, end) timestamps of a game day, in the format SQLite stores in created_at."""
    start = datetime(day.year, day.month, day.day, DAY_START_HOUR) + offset
    fmt = "%Y-%m-%d %H:%M:%S"
    return start.strftime(fmt), (start + timedelta(days=1)).strftime(fmt)


def _day_context(db, day, offset):
    lo, hi = _day_window(day, offset)
    events = db.execute(
        select(Event.kind, Event.points, Event.priority, Event.task_type, Event.created_at).where(
            Event.created_at >= lo, Event.created_at < hi
        )
    ).all()
    notes = db.scalar(select(func.count()).select_from(Note).where(Note.created_at >= lo, Note.created_at < hi))
    return {
        "events": events,
        "done": [e for e in events if e.kind == "done"],
        "kinds": Counter(e.kind for e in events),
        "task_xp": sum(e.points for e in events if e.kind != "challenge"),
        "notes": notes,
        "offset": offset,
    }


def _hour(e, ctx):
    return _clock(e, ctx["offset"]).hour


def _n_text(n, singular, plural=None):
    return singular if n == 1 else (plural or singular + "s")


# Each challenge: (generate(ctx, rng) -> (text, target, reward, params) or None, progress(ctx, params) -> int)
def _gen_resolve(ctx, rng):
    n = rng.choice([2, 3, 4])
    return f"Resolve {n} tasks", n, 8 + 4 * n, {}


def _gen_xp(ctx, rng):
    n = rng.choice([30, 45, 60])
    return f"Earn {n} XP from tasks", n, n // 3, {}


def _gen_dev(ctx, rng):
    n = rng.choice([1, 2])
    return f"Push {n} {_n_text(n, 'task')} to DEV", n, 6 * n, {}


def _gen_qa(ctx, rng):
    n = rng.choice([1, 2])
    return f"Get {n} {_n_text(n, 'task')} through QA", n, 8 * n, {}


def _gen_notes(ctx, rng):
    n = rng.choice([1, 2, 3])
    return f"Leave {n} progress {_n_text(n, 'note')}", n, 5 * n + 3, {}


def _gen_type(ctx, rng):
    options = ctx.get("open_types") or []
    if not options:
        return None
    key, name = rng.choice(options)
    return f"Finish a {name} task", 1, 12, {"type": key}


def _gen_early(ctx, rng):
    return ("Resolve a task before noon", 1, 15, {}) if ctx.get("hours_in", 0) < 10 else None


def _gen_late(ctx, rng):
    return ("Resolve a task after 8 PM", 1, 15, {}) if ctx.get("hours_in", 0) < 18 else None


CHALLENGES = {
    "resolve_n": (_gen_resolve, lambda c, p: len(c["done"])),
    "earn_xp": (_gen_xp, lambda c, p: c["task_xp"]),
    "dev_n": (_gen_dev, lambda c, p: c["kinds"]["env_dev"]),
    "qa_n": (_gen_qa, lambda c, p: c["kinds"]["env_qa"]),
    "ship_prd": (lambda c, r: ("Ship a task to PRD", 1, 25, {}), lambda c, p: c["kinds"]["env_prd"]),
    "pipeline": (
        lambda c, r: ("Touch DEV, QA and PRD in one day", 3, 30, {}),
        lambda c, p: sum(1 for e in ENV_ORDER if c["kinds"][f"env_{e}"]),
    ),
    "high_prio": (
        lambda c, r: ("Resolve a high-priority task", 1, 20, {}),
        lambda c, p: sum(1 for e in c["done"] if e.priority in ("high", "critical")),
    ),
    "type_task": (_gen_type, lambda c, p: sum(1 for e in c["done"] if e.task_type == p.get("type"))),
    "notes_n": (_gen_notes, lambda c, p: c["notes"]),
    "early_bird": (
        _gen_early,
        lambda c, p: sum(1 for e in c["done"] if DAY_START_HOUR <= _hour(e, c) < 12),
    ),
    "night_owl": (
        _gen_late,
        lambda c, p: sum(1 for e in c["done"] if _hour(e, c) >= 20 or _hour(e, c) < DAY_START_HOUR),
    ),
}


def _type_challenge_ids(db, type_key):
    """Ids of the "Finish a <type> task" challenges that point at this type."""
    return [
        r.id for r in db.execute(select(Challenge.id, Challenge.params).where(Challenge.key == "type_task"))
        if json.loads(r.params).get("type") == type_key
    ]


def _challenge_events(ids):
    """Conditions matching the bonus events paid for these challenges."""
    return Event.kind == "challenge", Event.task_id.in_([-cid for cid in ids])


def rename_type_challenges(db, type_key, new_name):
    """A type was renamed: keep the wording of its existing challenges in step."""
    text = f"Finish a {new_name} task"
    ids = _type_challenge_ids(db, type_key)
    db.execute(update(Challenge).where(Challenge.id.in_(ids)).values(text=text))
    db.execute(update(Event).where(*_challenge_events(ids)).values(title=text))


def drop_type_challenges(db, type_key):
    """A type was deleted: its challenges (and any bonus already paid for them) go with it."""
    ids = _type_challenge_ids(db, type_key)
    db.execute(delete(Challenge).where(Challenge.id.in_(ids)))
    db.execute(delete(Event).where(*_challenge_events(ids)))


def _open_types(db):
    rows = db.execute(
        select(TaskType.key, TaskType.name).distinct().join(Task, Task.type == TaskType.key).where(Task.status != "done")
    )
    return [(r.key, r.name) for r in rows]


def _ensure_challenges(db, day, ctx, now, offset, rng):
    if db.scalar(select(func.count()).select_from(Challenge).where(Challenge.day == day.isoformat())):
        return
    clock = now - offset
    ctx = {**ctx, "open_types": _open_types(db), "hours_in": (clock.hour - DAY_START_HOUR) % 24}
    pool = list(CHALLENGES)
    rng.shuffle(pool)
    made = []
    for key in pool:
        spec = CHALLENGES[key][0](ctx, rng)
        if spec:
            made.append((key, *spec))
        if len(made) == DAILY_CHALLENGES:
            break
    db.add_all(
        Challenge(day=day.isoformat(), key=key, text=text, target=target, reward=reward, params=json.dumps(params))
        for key, text, target, reward, params in made
    )


def sync_challenges(db, now=None, rng=None):
    """Create today's challenges on first use after the day starts, then award or take back their bonus."""
    now = now or _utcnow()
    offset = timedelta(minutes=get_tz(db))
    day = game_day(now - offset)
    ctx = _day_context(db, day, offset)
    _ensure_challenges(db, day, ctx, now, offset, rng or random.Random())
    result = []
    for ch in db.scalars(select(Challenge).where(Challenge.day == day.isoformat()).order_by(Challenge.id)).all():
        progress = CHALLENGES[ch.key][1](ctx, json.loads(ch.params))
        done = progress >= ch.target
        if done:
            _add_event(db, now, kind="challenge", task_id=-ch.id, title=ch.text, points=ch.reward)
        else:
            db.execute(delete(Event).where(*_challenge_events([ch.id])))
        result.append(
            {"id": ch.id, "text": ch.text, "progress": min(progress, ch.target),
             "target": ch.target, "reward": ch.reward, "done": done}
        )
    return result


# ---------- stats ----------

def _run_ending(days, day):
    """Length of the run of consecutive days in `days` that ends on `day`."""
    n = 0
    while day in days:
        n += 1
        day -= timedelta(days=1)
    return n


def _best_streak(days):
    # a run's last day is a day whose next day is missing
    return max((_run_ending(days, d) for d in days if d + timedelta(days=1) not in days), default=0)


def compute_stats(db, tz_offset_minutes, now=None, rng=None):
    """`tz_offset_minutes` is JavaScript's getTimezoneOffset(): minutes UTC is ahead of local time.
    `now` (naive UTC) and `rng` can be given to make the result deterministic."""
    set_tz(db, tz_offset_minutes)
    now = now or _utcnow()
    offset = timedelta(minutes=tz_offset_minutes)
    today = game_day(now - offset)
    challenges = sync_challenges(db, now, rng)  # may add or remove challenge bonus events

    done_per_day = Counter(
        game_day(_local(ts, offset)) for ts in db.scalars(select(Event.created_at).where(Event.kind == "done"))
    )
    days = set(done_per_day)
    # a streak stays alive through today, so it only breaks once a whole game day passes with nothing done
    streak = _run_ending(days, today if today in days else today - timedelta(days=1))
    best_streak = _best_streak(days)

    lo, hi = _day_window(today, offset)
    xp = select(func.coalesce(func.sum(Event.points), 0))
    xp_today = db.scalar(xp.where(Event.created_at >= lo, Event.created_at < hi))
    total_xp = db.scalar(xp)
    total_done = sum(done_per_day.values())
    week_start = today - timedelta(days=6)

    envs_by_task = {}
    env_kinds = [f"env_{e}" for e in ENV_ORDER]
    for task_id, kind in db.execute(select(Event.task_id, Event.kind).where(Event.kind.in_(env_kinds))):
        envs_by_task.setdefault(task_id, set()).add(kind[4:])

    achievements = [
        ("first_blood", "First Blood", "Resolve your first task", total_done >= 1),
        ("hat_trick", "Hat Trick", "Resolve 3 tasks in one day", max(done_per_day.values(), default=0) >= 3),
        ("on_fire", "On Fire", "Reach a 3-day streak", best_streak >= 3),
        ("unstoppable", "Unstoppable", "Reach a 7-day streak", best_streak >= 7),
        ("ship_it", "Ship It", "Push a task to PRD", any("prd" in s for s in envs_by_task.values())),
        ("full_pipeline", "Full Pipeline", "Take one task through DEV, QA and PRD", any(s >= set(ENV_ORDER) for s in envs_by_task.values())),
        ("task_machine", "Task Machine", "Resolve 25 tasks", total_done >= 25),
    ]

    recent = db.execute(
        select(Event.kind, Event.title, Event.points, Event.created_at).order_by(Event.id.desc()).limit(RECENT_WINS)
    )

    return {
        "day": today.isoformat(),
        "day_starts_at": f"{DAY_START_HOUR:02d}:00",
        "xp": xp_today,
        "total_xp": total_xp,
        **level_info(xp_today, today),
        "streak": streak,
        "best_streak": best_streak,
        "resolved_today": done_per_day.get(today, 0),
        "resolved_week": sum(n for d, n in done_per_day.items() if d >= week_start),
        "total_done": total_done,
        "challenges": challenges,
        "recent": [dict(r._mapping) for r in recent],
        "achievements": [
            {"id": i, "name": name, "desc": desc, "unlocked": bool(ok)} for i, name, desc, ok in achievements
        ],
    }
