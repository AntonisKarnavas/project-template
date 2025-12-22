import pytest
from unittest.mock import MagicMock
from sqlalchemy import select
from database.models import User, OAuthAccount
import services.auth_service

@pytest.mark.asyncio
async def test_social_login_google_mock(client, db_session, monkeypatch):
    # Mock verify_google_token in routers.auth
    mock_verify = MagicMock(return_value={
        "sub": "google_123",
        "email": "test@google.com",
        "provider": "google"
    })
    monkeypatch.setattr("routers.auth.verify_google_token", mock_verify)
    
    token = "some_valid_google_token"
    
    response = await client.post(
        "/auth/google",
        json={"token": token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login with google successful"
    assert data["email"] == "test@google.com"
    assert "session_id" in response.cookies

    # Verify DB
    stmt = select(User).where(User.email == "test@google.com")
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    assert user is not None
    
    stmt_acc = select(OAuthAccount).where(OAuthAccount.user_id == user.id)
    result_acc = await db_session.execute(stmt_acc)
    account = result_acc.scalar_one_or_none()
    assert account is not None
    assert account.provider == "google"
    assert account.sub == "google_123"

@pytest.mark.asyncio
async def test_social_login_apple_mock(client, db_session, monkeypatch):
    mock_verify = MagicMock(return_value={
        "sub": "apple_123",
        "email": "test@apple.com",
        "provider": "apple"
    })
    monkeypatch.setattr("routers.auth.verify_apple_token", mock_verify)

    token = "some_apple_token"
    
    response = await client.post(
        "/auth/apple",
        json={"token": token}
    )
    assert response.status_code == 200
    assert "session_id" in response.cookies
    
    # Check if provider is correct
    stmt = select(OAuthAccount).where(OAuthAccount.provider == "apple")
    result = await db_session.execute(stmt)
    account = result.scalar_one_or_none()
    assert account is not None
    assert account.sub == "apple_123"


@pytest.mark.asyncio
async def test_social_login_facebook_mock(client, db_session, monkeypatch):
    mock_verify = MagicMock(return_value={
        "sub": "fb_123",
        "email": "test@fb.com",
        "provider": "facebook"
    })
    monkeypatch.setattr("routers.auth.verify_facebook_token", mock_verify)
    
    token = "some_fb_token"
    
    response = await client.post(
        "/auth/facebook",
        json={"token": token}
    )
    assert response.status_code == 200
    assert "session_id" in response.cookies
