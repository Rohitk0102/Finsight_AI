"""
Resilience tests for predict routes when external DB/network is degraded.
"""
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

from app.api.routes import predict as predict_routes


def _request() -> SimpleNamespace:
    return SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))


class _FakeQuery:
    def __init__(self, *, data=None, exc: Exception | None = None):
        self._data = data
        self._exc = exc

    def execute(self):
        if self._exc:
            raise self._exc
        return SimpleNamespace(data=self._data)


@pytest.mark.asyncio
async def test_execute_query_returns_503_on_connect_error():
    request = httpx.Request("GET", "https://invalid-host.local")
    query = _FakeQuery(exc=httpx.ConnectError("[Errno 8] nodename nor servname provided, or not known", request=request))

    with pytest.raises(HTTPException) as exc_info:
        await predict_routes._execute_query(query, operation="test_connectivity")

    assert exc_info.value.status_code == 503
    assert "Database service unavailable" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_sentiment_fails_open_to_zero(monkeypatch):
    async def failing_query(*_args, **_kwargs):
        raise RuntimeError("db temporarily unavailable")

    monkeypatch.setattr(predict_routes, "_execute_query", failing_query)

    score = await predict_routes._get_sentiment("INFY")
    assert score == 0.0


@pytest.mark.asyncio
async def test_analyze_portfolio_returns_empty_when_no_holdings(monkeypatch):
    async def no_rate_limit(*_args, **_kwargs):
        return None

    async def fake_execute(_query, *, operation: str, fail_open: bool = False):
        if operation == "portfolio_holdings_fetch":
            return SimpleNamespace(data=[])
        raise AssertionError("Profile query should not run when no holdings exist")

    monkeypatch.setattr(predict_routes, "_apply_rate_limit", no_rate_limit)
    monkeypatch.setattr(predict_routes, "_execute_query", fake_execute)

    result = await predict_routes.analyze_portfolio(
        current_user={"id": "user_123"},
        request=_request(),
    )

    assert result == {"message": "No holdings found", "analyses": []}


@pytest.mark.asyncio
async def test_analyze_portfolio_surfaces_db_unavailable(monkeypatch):
    async def no_rate_limit(*_args, **_kwargs):
        return None

    async def fake_execute(_query, *, operation: str, fail_open: bool = False):
        if operation == "portfolio_holdings_fetch":
            raise HTTPException(status_code=503, detail="Database service unavailable")
        return SimpleNamespace(data=[])

    monkeypatch.setattr(predict_routes, "_apply_rate_limit", no_rate_limit)
    monkeypatch.setattr(predict_routes, "_execute_query", fake_execute)

    with pytest.raises(HTTPException) as exc_info:
        await predict_routes.analyze_portfolio(
            current_user={"id": "user_123"},
            request=_request(),
        )

    assert exc_info.value.status_code == 503
