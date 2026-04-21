"""
Shared pytest fixtures for Finsight AI backend tests.
Uses FastAPI TestClient with mocked external dependencies.
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def mock_settings(tmp_path_factory):
    """Patch settings so tests don't need real env vars."""
    from cryptography.fernet import Fernet
    valid_key = Fernet.generate_key().decode()
    settings_patch = {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_SERVICE_ROLE_KEY": "test-service-role-key",
        "CLERK_JWKS_URL": "https://test-clerk.example/.well-known/jwks.json",
        "BROKER_TOKEN_ENCRYPTION_KEY": valid_key,
        "REDIS_URL": "redis://localhost:6379/0",
        "ALLOWED_ORIGINS": ["http://localhost:3000", "https://localhost:3000"],
        "FINNHUB_API_KEY": "",
        "UPSTOX_CLIENT_ID": "test-client-id",
        "UPSTOX_CLIENT_SECRET": "test-client-secret",
        "UPSTOX_REDIRECT_URI": "https://localhost:8000/api/v1/broker/upstox/callback",
        "ZERODHA_API_KEY": "test-zerodha-key",
        "ZERODHA_API_SECRET": "test-zerodha-secret",
        "ANGEL_ONE_API_KEY": "test-angel-key",
    }
    return settings_patch


@pytest.fixture
def mock_current_user():
    """Simulated authenticated user payload from get_current_user."""
    return {
        "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "email": "test@example.com",
        "token": "clerk-jwt-token",
    }


@pytest.fixture
def mock_redis():
    """Mock Redis for tests to avoid requiring a running Redis instance."""
    with patch("app.core.redis.get_redis") as mock_get_redis:
        mock_redis_client = AsyncMock()
        mock_redis_client.get.return_value = None
        mock_redis_client.setex.return_value = True
        mock_redis_client.delete.return_value = True
        mock_redis_client.exists.return_value = False
        mock_redis_client.incr.return_value = 1
        mock_redis_client.expire.return_value = True
        mock_get_redis.return_value = mock_redis_client
        yield mock_redis_client


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for tests."""
    with patch("app.core.supabase.supabase") as mock_sb:
        yield mock_sb
