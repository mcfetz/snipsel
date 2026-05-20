from __future__ import annotations
from datetime import date, datetime, timedelta
from typing import Optional

from flask import Blueprint, request
from snipsel_api.auth_session import (
    current_user,
    enforce_json,
    json_response,
    require_auth,
)
from snipsel_api.extensions import db
from snipsel_api.models import Habit, HabitCompletion
from snipsel_api import sse_bus

habits_bp = Blueprint("habits", __name__)


def _habit_json(habit: Habit, user_id: str, today: date | None = None) -> dict:
    if today is None:
        today = date.today()

    today_completed = (
        db.session.execute(
            db.select(HabitCompletion).where(
                HabitCompletion.habit_id == habit.id,
                HabitCompletion.user_id == user_id,
                HabitCompletion.completed_date == today,
            )
        ).scalar_one_or_none()
        is not None
    )

    # Compute streaks
    completions = (
        db.session.execute(
            db.select(HabitCompletion.completed_date)
            .where(
                HabitCompletion.habit_id == habit.id,
                HabitCompletion.user_id == user_id,
            )
            .order_by(HabitCompletion.completed_date.desc())
        )
        .scalars()
        .all()
    )

    current_streak = 0
    longest_streak = 0
    streak = 0
    prev_date: Optional[date] = None

    for d in completions:
        if prev_date is None:
            streak = 1
        elif (prev_date - d).days == 1:
            streak += 1
        else:
            longest_streak = max(longest_streak, streak)
            streak = 1
        longest_streak = max(longest_streak, streak)
        prev_date = d

    # Check if current streak is active (ends today or yesterday)
    if completions and (today - completions[0]).days <= 1:
        current_streak = streak

    return {
        "id": habit.id,
        "name": habit.name,
        "icon": habit.icon,
        "color": habit.color,
        "reminder_time": habit.reminder_time,
        "reminder_rrule": habit.reminder_rrule,
        "sort_position": habit.sort_position,
        "is_archived": habit.is_archived,
        "created_at": habit.created_at.isoformat() + "Z",
        "modified_at": habit.modified_at.isoformat() + "Z",
        "today_completed": today_completed,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
    }


@habits_bp.get("")
@require_auth
def list_habits():
    user = current_user()
    include_archived = request.args.get("include_archived") == "1"
    date_str = request.args.get("date")
    target_date = date.fromisoformat(date_str) if date_str else date.today()

    q = db.select(Habit).where(
        Habit.owner_user_id == user.id,
        Habit.deleted_at.is_(None),
    )
    if not include_archived:
        q = q.where(Habit.is_archived == False)

    q = q.order_by(Habit.sort_position.asc(), Habit.created_at.asc())
    habits = db.session.execute(q).scalars().all()

    return json_response(
        {"habits": [_habit_json(h, user.id, target_date) for h in habits]}
    )


@habits_bp.post("")
@require_auth
@enforce_json
def create_habit():
    user = current_user()
    data = request.json or {}

    name = (data.get("name") or "").strip()
    if not name:
        return json_response({"error": "Name is required"}, 400)

    # Get max sort_position
    max_pos = (
        db.session.execute(
            db.select(db.func.max(Habit.sort_position)).where(
                Habit.owner_user_id == user.id, Habit.deleted_at.is_(None)
            )
        ).scalar()
        or 0
    )

    habit = Habit(
        owner_user_id=user.id,
        name=name,
        icon=data.get("icon", "✅"),
        color=data.get("color"),
        reminder_time=data.get("reminder_time"),
        reminder_rrule=data.get("reminder_rrule"),
        sort_position=max_pos + 1,
    )
    db.session.add(habit)
    db.session.commit()

    sse_bus.publish(
        [user.id],
        {"type": "habit_list_changed"},
        origin_client_id=request.headers.get("X-Client-Id"),
    )

    return json_response({"habit": _habit_json(habit, user.id)}, 201)


@habits_bp.get("/<habit_id>")
@require_auth
def get_habit(habit_id: str):
    user = current_user()
    habit = db.session.execute(
        db.select(Habit).where(
            Habit.id == habit_id,
            Habit.owner_user_id == user.id,
            Habit.deleted_at.is_(None),
        )
    ).scalar_one_or_none()

    if not habit:
        return json_response({"error": "Habit not found"}, 404)

    return json_response({"habit": _habit_json(habit, user.id)})


@habits_bp.patch("/<habit_id>")
@require_auth
@enforce_json
def update_habit(habit_id: str):
    user = current_user()
    habit = db.session.execute(
        db.select(Habit).where(
            Habit.id == habit_id,
            Habit.owner_user_id == user.id,
            Habit.deleted_at.is_(None),
        )
    ).scalar_one_or_none()

    if not habit:
        return json_response({"error": "Habit not found"}, 404)

    data = request.json or {}

    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            return json_response({"error": "Name cannot be empty"}, 400)
        habit.name = name
    if "icon" in data:
        habit.icon = data["icon"]
    if "color" in data:
        habit.color = data["color"]
    if "reminder_time" in data:
        habit.reminder_time = data["reminder_time"]
    if "reminder_rrule" in data:
        habit.reminder_rrule = data["reminder_rrule"]
    if "sort_position" in data:
        habit.sort_position = int(data["sort_position"])
    if "is_archived" in data:
        habit.is_archived = bool(data["is_archived"])

    db.session.commit()

    sse_bus.publish(
        [user.id],
        {"type": "habit_list_changed"},
        origin_client_id=request.headers.get("X-Client-Id"),
    )

    return json_response({"habit": _habit_json(habit, user.id)})


@habits_bp.delete("/<habit_id>")
@require_auth
def delete_habit(habit_id: str):
    user = current_user()
    habit = db.session.execute(
        db.select(Habit).where(
            Habit.id == habit_id,
            Habit.owner_user_id == user.id,
            Habit.deleted_at.is_(None),
        )
    ).scalar_one_or_none()

    if not habit:
        return json_response({"error": "Habit not found"}, 404)

    habit.deleted_at = datetime.utcnow()
    db.session.commit()

    sse_bus.publish(
        [user.id],
        {"type": "habit_list_changed"},
        origin_client_id=request.headers.get("X-Client-Id"),
    )

    return json_response({"ok": True})


@habits_bp.post("/<habit_id>/complete")
@require_auth
@enforce_json
def complete_habit(habit_id: str):
    user = current_user()
    habit = db.session.execute(
        db.select(Habit).where(
            Habit.id == habit_id,
            Habit.owner_user_id == user.id,
            Habit.deleted_at.is_(None),
        )
    ).scalar_one_or_none()

    if not habit:
        return json_response({"error": "Habit not found"}, 404)

    data = request.json or {}
    date_str = data.get("date")
    completed_date = date.fromisoformat(date_str) if date_str else date.today()

    existing = db.session.execute(
        db.select(HabitCompletion).where(
            HabitCompletion.habit_id == habit_id,
            HabitCompletion.user_id == user.id,
            HabitCompletion.completed_date == completed_date,
        )
    ).scalar_one_or_none()

    if existing:
        return json_response(
            {
                "completion": {
                    "id": existing.id,
                    "habit_id": existing.habit_id,
                    "completed_date": existing.completed_date.isoformat(),
                }
            }
        )

    completion = HabitCompletion(
        habit_id=habit_id,
        user_id=user.id,
        completed_date=completed_date,
    )
    db.session.add(completion)
    db.session.commit()

    sse_bus.publish(
        [user.id],
        {"type": "habit_completion_changed", "habit_id": habit_id},
        origin_client_id=request.headers.get("X-Client-Id"),
    )

    return json_response(
        {
            "completion": {
                "id": completion.id,
                "habit_id": completion.habit_id,
                "completed_date": completion.completed_date.isoformat(),
            }
        },
        201,
    )


@habits_bp.delete("/<habit_id>/complete")
@require_auth
def uncomplete_habit(habit_id: str):
    user = current_user()
    habit = db.session.execute(
        db.select(Habit).where(
            Habit.id == habit_id,
            Habit.owner_user_id == user.id,
            Habit.deleted_at.is_(None),
        )
    ).scalar_one_or_none()

    if not habit:
        return json_response({"error": "Habit not found"}, 404)

    date_str = request.args.get("date")
    completed_date = date.fromisoformat(date_str) if date_str else date.today()

    db.session.execute(
        db.delete(HabitCompletion).where(
            HabitCompletion.habit_id == habit_id,
            HabitCompletion.user_id == user.id,
            HabitCompletion.completed_date == completed_date,
        )
    )
    db.session.commit()

    sse_bus.publish(
        [user.id],
        {"type": "habit_completion_changed", "habit_id": habit_id},
        origin_client_id=request.headers.get("X-Client-Id"),
    )

    return json_response({"ok": True})


@habits_bp.get("/stats")
@require_auth
def habit_stats():
    user = current_user()
    from_str = request.args.get("from")
    to_str = request.args.get("to")

    if to_str:
        to_date = date.fromisoformat(to_str)
    else:
        to_date = date.today()

    if from_str:
        from_date = date.fromisoformat(from_str)
    else:
        from_date = to_date - timedelta(days=29)

    habits = (
        db.session.execute(
            db.select(Habit)
            .where(
                Habit.owner_user_id == user.id,
                Habit.deleted_at.is_(None),
            )
            .order_by(Habit.sort_position.asc())
        )
        .scalars()
        .all()
    )

    result = []
    for habit in habits:
        completions = (
            db.session.execute(
                db.select(HabitCompletion)
                .where(
                    HabitCompletion.habit_id == habit.id,
                    HabitCompletion.user_id == user.id,
                    HabitCompletion.completed_date >= from_date,
                    HabitCompletion.completed_date <= to_date,
                )
                .order_by(HabitCompletion.completed_date.desc())
            )
            .scalars()
            .all()
        )

        completion_dates = [c.completed_date.isoformat() for c in completions]
        total_days = (to_date - from_date).days + 1
        completed_days = len(completions)
        completion_rate = completed_days / total_days if total_days > 0 else 0

        # Streaks (all-time)
        all_completions = (
            db.session.execute(
                db.select(HabitCompletion.completed_date)
                .where(
                    HabitCompletion.habit_id == habit.id,
                    HabitCompletion.user_id == user.id,
                )
                .order_by(HabitCompletion.completed_date.desc())
            )
            .scalars()
            .all()
        )

        current_streak = 0
        longest_streak = 0
        streak = 0
        prev_date: Optional[date] = None
        for d in all_completions:
            if prev_date is None:
                streak = 1
            elif (prev_date - d).days == 1:
                streak += 1
            else:
                longest_streak = max(longest_streak, streak)
                streak = 1
            longest_streak = max(longest_streak, streak)
            prev_date = d

        today = date.today()
        if all_completions and (today - all_completions[0]).days <= 1:
            current_streak = streak

        result.append(
            {
                "id": habit.id,
                "name": habit.name,
                "icon": habit.icon,
                "color": habit.color,
                "total_days": total_days,
                "completed_days": completed_days,
                "completion_rate": round(completion_rate, 2),
                "current_streak": current_streak,
                "longest_streak": longest_streak,
                "completions": completion_dates,
            }
        )

    return json_response({"habits": result})


@habits_bp.patch("/reorder")
@require_auth
@enforce_json
def reorder_habits():
    user = current_user()
    data = request.json or {}
    items = data.get("items", [])

    if not items:
        return json_response({"error": "Missing items"}, 400)

    for item in items:
        habit_id = item.get("id")
        sort_position = item.get("sort_position")
        if habit_id is None or sort_position is None:
            continue

        db.session.execute(
            db.update(Habit)
            .where(Habit.id == habit_id, Habit.owner_user_id == user.id)
            .values(sort_position=sort_position)
        )

    db.session.commit()

    sse_bus.publish(
        [user.id],
        {"type": "habit_list_changed"},
        origin_client_id=request.headers.get("X-Client-Id"),
    )

    return json_response({"ok": True})
