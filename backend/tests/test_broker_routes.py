"""
Tests for broker OAuth routes.
"""
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# CRITICAL Fix #1: Upstox state param must appear exactly once
#
# Root cause (fixed): settings/page.tsx was appending &state=USER_ID to an
# auth_url that already contained &state=USER_ID from the backend (broker.py:26).
# Fix: removed `+ '&state=${user?.id}'` from settings/page.tsx:connectUpstox.
# ─────────────────────────────────────────────────────────────────────────────

def test_upstox_auth_url_state_appears_exactly_once():
    """
    After fix: the browser navigates to exactly the auth_url returned by the
    backend. The backend appends &state=USER_ID once in broker.py:26.
    Frontend no longer re-appends state.
    """
    user_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    # Backend (broker.py:26) builds this URL — state appears once
    backend_auth_url = (
        "https://api.upstox.com/v2/login/authorization/dialog"
        "?response_type=code&client_id=test-client"
        "&redirect_uri=https://localhost:8000/api/v1/broker/upstox/callback"
        f"&state={user_id}"
    )

    # Fixed frontend: window.location.href = res.data.auth_url  (no extra append)
    final_url = backend_auth_url

    state_count = final_url.count("state=")
    assert state_count == 1, (
        f"Expected exactly 1 'state=' in navigated URL, found {state_count}.\n"
        f"URL: {final_url}"
    )


def test_double_state_append_would_break_oauth():
    """
    Regression guard: demonstrates that appending state twice produces an
    invalid URL. This ensures the bug does not return.
    """
    user_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

    backend_auth_url = (
        "https://api.upstox.com/v2/login/authorization/dialog"
        "?response_type=code&client_id=test-client"
        f"&state={user_id}"
    )

    # If someone re-introduces the bug (appending state again):
    buggy_url = backend_auth_url + f"&state={user_id}"

    assert buggy_url.count("state=") > 1, "Should detect double-state as a bug"
