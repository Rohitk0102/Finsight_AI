"""
Tests for Celery task configuration.
"""
import pytest
import os


# ─────────────────────────────────────────────────────────────────────────────
# CRITICAL Fix #3: Celery beat_schedule must use valid schedule types
#
# Root cause: beat_schedule entries used raw dicts {"hour": X, "minute": Y}
# which Celery does not recognize as schedule types. Tasks never run.
# Fix: replace with crontab(hour=X, minute=Y) from celery.schedules.
# ─────────────────────────────────────────────────────────────────────────────

CELERY_APP_PATH = os.path.join(
    os.path.dirname(__file__), "..", "app", "tasks", "celery_app.py"
)


def _read_source(path: str) -> str:
    with open(os.path.abspath(path)) as f:
        return f.read()


def test_beat_schedule_does_not_use_raw_dict_as_schedule():
    """
    Using {"hour": X, "minute": Y} as a Celery beat schedule value is invalid.
    Valid types are: crontab, timedelta, or a number (seconds).
    This test fails if any raw dict is still used as a schedule value.
    """
    source = _read_source(CELERY_APP_PATH)
    # Detect the buggy pattern: "schedule": {  (dict literal as schedule)
    # Valid schedule= values would be crontab(...) or a number
    assert '"schedule": {' not in source and "'schedule': {" not in source, (
        "beat_schedule contains a raw dict as 'schedule' value. "
        "Use crontab(hour=X, minute=Y) from celery.schedules instead."
    )


def test_beat_schedule_imports_crontab():
    """
    crontab must be imported for the beat schedule to work correctly.
    """
    source = _read_source(CELERY_APP_PATH)
    assert "crontab" in source, (
        "celery_app.py must import and use crontab from celery.schedules "
        "for the beat schedule entries."
    )


def test_beat_schedule_has_three_tasks():
    """
    There should be exactly 3 scheduled tasks:
    sync-market-data, retrain-models, sync-holdings.
    """
    source = _read_source(CELERY_APP_PATH)
    assert '"sync-market-data"' in source
    assert '"retrain-models"' in source
    assert '"sync-holdings"' in source
