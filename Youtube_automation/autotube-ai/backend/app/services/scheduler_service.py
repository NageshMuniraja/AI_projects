"""Scheduler Service — defines Celery Beat schedules for automated operations."""

from celery.schedules import crontab

# Schedule definitions for Celery Beat
BEAT_SCHEDULE = {
    # === DAILY at 6 AM UTC ===
    "daily-trend-research": {
        "task": "app.workers.analytics_tasks.daily_trend_research_task",
        "schedule": crontab(hour=6, minute=0),
        "options": {"queue": "default"},
    },
    "daily-pull-analytics": {
        "task": "app.workers.analytics_tasks.pull_all_analytics_task",
        "schedule": crontab(hour=6, minute=30),
        "options": {"queue": "default"},
    },

    # === WEEKLY: Monday 3 AM UTC ===
    "weekly-content-calendar": {
        "task": "app.workers.analytics_tasks.weekly_content_calendar_task",
        "schedule": crontab(hour=3, minute=0, day_of_week=1),
        "options": {"queue": "default"},
    },
    "weekly-cleanup": {
        "task": "app.workers.analytics_tasks.weekly_cleanup_task",
        "schedule": crontab(hour=4, minute=0, day_of_week=1),
        "options": {"queue": "default"},
    },
}
