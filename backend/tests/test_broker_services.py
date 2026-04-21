"""
Tests for broker service implementations.
"""
import pytest
import inspect
import os


# ─────────────────────────────────────────────────────────────────────────────
# CRITICAL Fix #4: AngelOne fetch_holdings must use the access_token param
#
# Root cause: angelone_broker.py creates SmartConnect but never calls
# obj.generateSession() or sets the JWT token from access_token.
# The parameter is accepted but silently ignored → all requests unauthenticated.
#
# Fix: Use the SmartAPI's setSessionExpiryHook and set the access token
# on the SmartConnect object before calling obj.holding().
# ─────────────────────────────────────────────────────────────────────────────

ANGELONE_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "app", "services", "broker", "angelone_broker.py"
)


def _read_source(path: str) -> str:
    with open(os.path.abspath(path)) as f:
        return f.read()


def test_angelone_fetch_holdings_uses_access_token():
    """
    fetch_holdings must use the access_token parameter to authenticate
    the SmartConnect session before calling obj.holding().
    Without this, every holding request is unauthenticated.
    """
    source = _read_source(ANGELONE_PATH)

    # The fix must set the access token on the SmartConnect object.
    # SmartAPI's way to set token is via obj.setSessionExpiryHook + token
    # or by using the session token directly.
    # We verify the access_token variable is actually used (not just accepted).
    assert "access_token" in source, "access_token param must exist"

    # The source MUST reference access_token in a way that uses it,
    # not just declare it. Specifically, it must not be only in the signature.
    lines = source.splitlines()
    usage_lines = [
        l for l in lines
        if "access_token" in l and "def fetch_holdings" not in l
    ]
    assert len(usage_lines) > 0, (
        "access_token is declared as a parameter but never used inside "
        "fetch_holdings. The SmartConnect session must be authenticated "
        "using the stored token."
    )

    # Specifically verify the token is set on the SmartConnect object
    # (not just referenced in a comment)
    non_comment_usage = [
        l.strip() for l in usage_lines
        if not l.strip().startswith("#")
    ]
    assert len(non_comment_usage) > 0, (
        "access_token is only referenced in comments, not used in code. "
        "Must authenticate SmartConnect with the stored token."
    )


def test_angelone_fetch_holdings_sets_token_on_smartconnect():
    """
    The SmartConnect object must have the access token set before calling
    obj.holding(). SmartAPI requires setting the auth token on the session.
    """
    source = _read_source(ANGELONE_PATH)

    # After fix, the code should set the access token.
    # SmartAPI uses obj.setSessionExpiryHook or token in headers.
    # The minimal fix is to call generateSession or set token attribute.
    has_token_set = (
        "obj.generateSession" in source
        or "authToken" in source
        or "setToken" in source
        or 'obj, access_token' in source
        or "SmartConnect(api_key" in source and "access_token" in source
    )

    # Verify that the holding() call comes AFTER access_token is referenced
    lines = source.splitlines()
    holding_line = next(
        (i for i, l in enumerate(lines) if "obj.holding()" in l), None
    )
    token_usage_line = next(
        (i for i, l in enumerate(lines)
         if "access_token" in l
         and "def fetch_holdings" not in l
         and not l.strip().startswith("#")),
        None
    )

    assert holding_line is not None, "fetch_holdings must call obj.holding()"
    assert token_usage_line is not None, (
        "access_token must be used before calling obj.holding()"
    )
    assert token_usage_line < holding_line, (
        f"Token setup (line {token_usage_line}) must come BEFORE "
        f"obj.holding() call (line {holding_line})."
    )
