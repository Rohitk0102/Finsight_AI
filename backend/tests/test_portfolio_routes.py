"""
Tests for portfolio route logic.
"""
import pytest
import ast
import os


# ─────────────────────────────────────────────────────────────────────────────
# CRITICAL Fix #2: Holdings upsert on_conflict must match DB constraint
#
# DB constraint: unique (broker_account_id, ticker)  — no user_id column
# Bug: portfolio.py:146 used on_conflict="user_id,broker_account_id,ticker"
#      portfolio.py:201 used on_conflict="user_id,broker_account_id,ticker"
# Fix: change to on_conflict="broker_account_id,ticker" to match the constraint.
# Reference: data_sync.py:74 already uses the correct value.
# ─────────────────────────────────────────────────────────────────────────────

PORTFOLIO_ROUTE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "app", "api", "routes", "portfolio.py"
)
DATA_SYNC_PATH = os.path.join(
    os.path.dirname(__file__), "..", "app", "tasks", "data_sync.py"
)

CORRECT_CONFLICT_KEY = "broker_account_id,ticker"
WRONG_CONFLICT_KEY = "user_id,broker_account_id,ticker"


def _read_source(path: str) -> str:
    with open(os.path.abspath(path)) as f:
        return f.read()


def test_portfolio_sync_upsert_uses_correct_conflict_key():
    """
    portfolio.py's sync_broker endpoint must use on_conflict='broker_account_id,ticker'
    to match the DB unique constraint. Using 'user_id,broker_account_id,ticker'
    causes PostgREST to error on every holding sync.
    """
    source = _read_source(PORTFOLIO_ROUTE_PATH)
    assert WRONG_CONFLICT_KEY not in source, (
        f"portfolio.py still contains wrong on_conflict key: '{WRONG_CONFLICT_KEY}'. "
        f"Must be '{CORRECT_CONFLICT_KEY}' to match the DB unique constraint "
        f"unique(broker_account_id, ticker)."
    )
    assert CORRECT_CONFLICT_KEY in source, (
        f"portfolio.py must contain on_conflict='{CORRECT_CONFLICT_KEY}'"
    )


def test_groww_import_upsert_uses_correct_conflict_key():
    """
    The Groww CSV import endpoint also had the wrong on_conflict key.
    Both upsert calls in portfolio.py must use the same correct constraint.
    """
    source = _read_source(PORTFOLIO_ROUTE_PATH)
    # Count how many times the correct key appears (should be >=2: sync + groww import)
    correct_count = source.count(f'on_conflict="{CORRECT_CONFLICT_KEY}"')
    wrong_count = source.count(f'on_conflict="{WRONG_CONFLICT_KEY}"')

    assert wrong_count == 0, (
        f"Found {wrong_count} occurrence(s) of wrong conflict key '{WRONG_CONFLICT_KEY}'. "
        f"All must use '{CORRECT_CONFLICT_KEY}'."
    )
    assert correct_count >= 2, (
        f"Expected at least 2 upserts with '{CORRECT_CONFLICT_KEY}' "
        f"(sync_broker + groww_import), found {correct_count}."
    )


def test_data_sync_conflict_key_unchanged():
    """
    data_sync.py already uses the correct key. Verify it's still correct
    so we have a reference to compare against.
    """
    source = _read_source(DATA_SYNC_PATH)
    assert f'on_conflict="{CORRECT_CONFLICT_KEY}"' in source, (
        f"data_sync.py's reference conflict key has changed — "
        f"expected '{CORRECT_CONFLICT_KEY}' still present."
    )
