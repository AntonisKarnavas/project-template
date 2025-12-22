import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from middlewares.security_headers import SecurityHeadersMiddleware
from config import settings, SecurityOverrides
from unittest.mock import patch

# Setup simple app for testing
app = FastAPI()
app.add_middleware(SecurityHeadersMiddleware)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/embed")
async def embed():
    return {"content": "embedded"}


client = TestClient(app)


def test_default_security_headers():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert response.headers["Content-Security-Policy"] == "default-src 'self'"
    assert (
        response.headers["Permissions-Policy"]
        == "geolocation=(), microphone=(), camera=()"
    )
    # HSTS should not be present on HTTP by default (unless forced)
    assert "Strict-Transport-Security" not in response.headers


def test_hsts_on_https():
    # Simulate HTTPS request via headers (as TestClient uses http://testserver by default)
    # The middleware checks request.url.scheme or x-forwarded-proto

    # Method 1: Mocking request.url.scheme is hard with TestClient,
    # but we implemented x-forwarded-proto check
    response = client.get("/health", headers={"X-Forwarded-Proto": "https"})
    assert response.status_code == 200
    assert "Strict-Transport-Security" in response.headers
    assert "max-age=31536000" in response.headers["Strict-Transport-Security"]
    assert "includeSubDomains" in response.headers["Strict-Transport-Security"]


def test_hsts_force_https_setting():
    with patch.object(settings, "SECURITY_FORCE_HTTPS", True):
        response = client.get("/health")  # Plain HTTP
        assert "Strict-Transport-Security" in response.headers


def test_endpoint_overrides():
    # Mock settings with an override
    override = SecurityOverrides(
        path_pattern="^/embed",
        x_frame_options="SAMEORIGIN",
        content_security_policy="default-src 'self' https://example.com",
    )

    with patch.object(settings, "SECURITY_OVERRIDES", [override]):
        # Test override endpoint
        response = client.get("/embed")
        assert response.status_code == 200
        assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
        assert (
            response.headers["Content-Security-Policy"]
            == "default-src 'self' https://example.com"
        )

        # Test non-override endpoint
        response = client.get("/health")
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Content-Security-Policy"] == "default-src 'self'"


def test_config_changes():
    # Test changing default settings
    with patch.object(settings, "SECURITY_X_FRAME_OPTIONS", "SAMEORIGIN"):
        response = client.get("/health")
        assert response.headers["X-Frame-Options"] == "SAMEORIGIN"
