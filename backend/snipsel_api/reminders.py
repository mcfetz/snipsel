from __future__ import annotations
from datetime import date, datetime
from snipsel_api.extensions import db
from snipsel_api import models


def _reminder_message(content_markdown: str | None) -> str:
    """Build a notification message from task content.

    Uses only the first line and appends '...' if the task has more lines
    or if the first line exceeds 80 characters.
    """
    if not content_markdown:
        return "Snipsel reminder"
    lines = content_markdown.splitlines()
    first_line = lines[0].strip()
    has_more_lines = len(lines) > 1
    if len(first_line) > 80:
        return first_line[:80] + "..."
    if has_more_lines:
        return first_line + "..."
    return first_line


def process_reminders(user_id: str | None = None) -> int:
    """Check for due reminders and create notifications.
    If user_id is None, processes reminders for all users.
    Returns count of new notifications created.
    """
    now = datetime.utcnow()

    q = db.select(models.Snipsel).where(
        models.Snipsel.reminder_at.isnot(None),
        models.Snipsel.reminder_at <= now,
        models.Snipsel.deleted_at.is_(None),
        models.Snipsel.task_done == False,
    )

    if user_id:
        q = q.where(models.Snipsel.owner_user_id == user_id)

    due_snipsels = db.session.execute(q).scalars().all()

    count = 0
    for s in due_snipsels:
        # Prevent duplicates: Check if ANY notification for this snipsel already exists.
        # We don't check for is_read=False because we only want to notify once per reminder.
        # Recurrence creates NEW snipsels, so they will get their own notifications.
        existing = (
            db.session.execute(
                db.select(models.Notification).where(
                    models.Notification.snipsel_id == s.id
                )
            )
            .scalars()
            .first()
        )

        if not existing:
            # Create notification
            n = models.Notification(
                user_id=s.owner_user_id,
                message=_reminder_message(s.content_markdown),
                snipsel_id=s.id,
            )
            db.session.add(n)
            count += 1

    if count > 0:
        db.session.commit()
    return count


def process_habit_reminders(user_id: str | None = None) -> int:
    """Check for due habit reminders and create notifications.
    If user_id is None, processes reminders for all users.
    Returns count of new notifications created.
    """
    now = datetime.utcnow()
    current_time_str = now.strftime("%H:%M")
    today = date.today()

    q = db.select(models.Habit).where(
        models.Habit.reminder_time.isnot(None),
        models.Habit.deleted_at.is_(None),
        models.Habit.is_archived == False,
    )

    if user_id:
        q = q.where(models.Habit.owner_user_id == user_id)

    habits = db.session.execute(q).scalars().all()

    count = 0
    for habit in habits:
        # Match reminder time within a 5-minute window
        habit_time = habit.reminder_time
        if not habit_time:
            continue

        # Simple time comparison: check if current time is within 5 min of reminder time
        try:
            h_hour, h_min = int(habit_time[:2]), int(habit_time[3:])
            n_hour, n_min = now.hour, now.minute
            habit_minutes = h_hour * 60 + h_min
            now_minutes = n_hour * 60 + n_min
            diff = abs(now_minutes - habit_minutes)
            if diff > 5 and diff < 1435:  # not within 5 minutes
                continue
        except (ValueError, IndexError):
            continue

        # Check if already completed today
        completed_today = db.session.execute(
            db.select(models.HabitCompletion).where(
                models.HabitCompletion.habit_id == habit.id,
                models.HabitCompletion.user_id == habit.owner_user_id,
                models.HabitCompletion.completed_date == today,
            )
        ).scalar_one_or_none()

        if completed_today:
            continue

        # Prevent duplicate notifications for the same habit on the same day
        existing = (
            db.session.execute(
                db.select(models.Notification).where(
                    models.Notification.user_id == habit.owner_user_id,
                    models.Notification.message == habit.name,
                    models.Notification.created_at
                    >= now.replace(hour=0, minute=0, second=0, microsecond=0),
                )
            )
            .scalars()
            .first()
        )

        if not existing:
            n = models.Notification(
                user_id=habit.owner_user_id,
                message=habit.name,
            )
            db.session.add(n)
            count += 1

    if count > 0:
        db.session.commit()
    return count
