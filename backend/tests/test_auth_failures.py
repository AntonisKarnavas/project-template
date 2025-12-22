import pytest
from database.models import User, OAuthClient
from security.auth import get_password_hash


@pytest.mark.asyncio
async def test_login_failure_wrong_password(client, db_session):
    # Setup
    await client.post(
        "/auth/register", json={"email": "fail@example.com", "password": "password123"}
    )

    # Attempt login with wrong password
    response = await client.post(
        "/auth/login", json={"email": "fail@example.com", "password": "wrongpassword"}
    )

    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_failure_nonexistent_user(client):
    response = await client.post(
        "/auth/login", json={"email": "ghost@example.com", "password": "password123"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_client_credentials_failure_invalid_secret(client, db_session):
    # Setup Client
    client_id = "fail_client"
    client_secret = "secret"

    db_client = OAuthClient(
        client_id=client_id,
        client_secret_hash=get_password_hash(client_secret),
        name="Fail Client",
        redirect_uris=[],
        grant_types=["client_credentials"],
        is_confidential=True,
    )
    db_session.add(db_client)
    await db_session.commit()

    # Attempt with wrong secret
    response = await client.post(
        "/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": "wrongsecret",
        },
    )

    assert response.status_code == 401
    assert "Invalid client credentials" in response.json()["detail"]


@pytest.mark.asyncio
async def test_exchange_failure_invalid_code(client):
    response = await client.post(
        "/oauth/token",
        data={
            "grant_type": "authorization_code",
            "code": "invalid_code",
            "client_id": "any_client",
            "redirect_uri": "http://localhost/callback",
            "code_verifier": "verifier",
        },
    )
    # Dependent on implementation, likely 400 or 401
    assert response.status_code in [400, 401]
