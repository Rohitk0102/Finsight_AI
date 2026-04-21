"""
Tests for application configuration defaults.
"""
import pytest
import os
import sys


# ─────────────────────────────────────────────────────────────────────────────
# CRITICAL Fix #5: ALLOWED_ORIGINS default must include HTTP localhost
#
# Root cause: default was ["https://localhost:3000"] (HTTPS only).
# Local dev without Docker runs frontend on http://localhost:3000 (HTTP).
# CORS middleware blocks all dev requests with 403.
#
# Fix: include both http://localhost:3000 and https://localhost:3000 in default.
# ─────────────────────────────────────────────────────────────────────────────

CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "app", "core", "config.py"
)


def _read_source(path: str) -> str:
    with open(os.path.abspath(path)) as f:
        return f.read()


def test_allowed_origins_default_includes_http_localhost():
    """
    The default ALLOWED_ORIGINS must include http://localhost:3000 (HTTP)
    so local development without Docker works out of the box.
    """
    source = _read_source(CONFIG_PATH)
    assert '"http://localhost:3000"' in source or "'http://localhost:3000'" in source, (
        "ALLOWED_ORIGINS default must include 'http://localhost:3000' (HTTP). "
        "Local dev frontend runs on HTTP, not HTTPS. "
        "Without this, every frontend API call is CORS-rejected in local dev."
    )


def test_allowed_origins_default_also_includes_https_localhost():
    """
    The default ALLOWED_ORIGINS must retain https://localhost:3000 (HTTPS)
    for Docker-based local development where nginx provides SSL.
    """
    source = _read_source(CONFIG_PATH)
    assert '"https://localhost:3000"' in source or "'https://localhost:3000'" in source, (
        "ALLOWED_ORIGINS default must still include 'https://localhost:3000' (HTTPS) "
        "for Docker local dev with nginx SSL termination."
    )


def test_env_files_are_resolved_relative_to_backend_config():
    """
    Backend config should resolve env files from fixed paths rather than the
    current working directory, otherwise repo-root runs can accidentally load
    Docker Redis settings during local development.
    """
    from app.core import config

    assert os.path.isabs(config.BACKEND_ENV_FILE)
    assert os.path.isabs(config.PROJECT_ENV_FILE)
    assert config.BACKEND_ENV_FILE.endswith(os.path.join("backend", ".env"))
    assert config.PROJECT_ENV_FILE.endswith(".env")
    assert config.BACKEND_ENV_FILE != config.PROJECT_ENV_FILE
