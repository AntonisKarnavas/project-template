import pytest
from sqlalchemy import select
from database.models import User
from security.auth import create_code_challenge
import secrets
from datetime import datetime, timedelta

import logging

logger = logging.getLogger(__name__)


async def dump_db(session, model, label):
    result = await session.execute(select(model))
    rows = result.scalars().all()
    logger.info(f"--- DB DUMP: {label} ---")
    for row in rows:
        # Filter out internal SQLAlchemy state
        data = {k: v for k, v in row.__dict__.items() if not k.startswith("_")}
        logger.info(f"{data}")
    logger.info("------------------------")


@pytest.mark.asyncio
async def test_register_user(client, db_session):
    response = await client.post(
        "/auth/register", json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

    # Verify DB
    stmt = select(User).where(User.email == "test@example.com")
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    assert user is not None

    await dump_db(db_session, User, "Users after Register")


@pytest.mark.asyncio
async def test_login_cookie_flow(client, db_session):
    # Register first
    await client.post(
        "/auth/register", json={"email": "login@example.com", "password": "password123"}
    )

    # Login
    response = await client.post(
        "/auth/login", json={"email": "login@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    assert "session_id" in response.cookies

    # Logout
    response = await client.post("/auth/logout")
    assert response.status_code == 200
    assert "session_id" not in response.cookies or response.cookies["session_id"] == ""

    await dump_db(db_session, User, "Users in Login Flow")




@pytest.mark.asyncio
async def test_auth_me_endpoint(client, db_session):
    # Register
    await client.post(
        "/auth/register", json={"email": "me@example.com", "password": "password123"}
    )

    # Login
    response = await client.post(
        "/auth/login", json={"email": "me@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    cookies = response.cookies

    # Check Auth Status (Persistence)
    response = await client.get("/auth/me", cookies=cookies)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"

    # Logout
    response = await client.post("/auth/logout", cookies=cookies)
    assert response.status_code == 200

    # Check Auth Status after Logout
    response = await client.get("/auth/me", cookies=response.cookies)
    assert response.status_code == 401
