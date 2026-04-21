"""
Regression tests for CORS preflight on API routes.
"""
from fastapi.testclient import TestClient

from app.main import app


def test_cors_preflight_allows_localhost_https_origin():
    client = TestClient(app)

    response = client.options(
        "/api/v1/news",
        headers={
            "Origin": "https://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code in (200, 204)
    assert response.headers.get("access-control-allow-origin") == "https://localhost:3000"
    assert "GET" in response.headers.get("access-control-allow-methods", "")
