import logging
import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Determine Test Mode: "FAKE" (default) or "REAL"
from config import settings
from database.core import get_db
from database.models import Base
from main import app

# Configure logging
logger = logging.getLogger(__name__)

TEST_MODE = settings.TEST_DATABASE_MODE.upper()


# --- DB Engine Fixture ---


@pytest.fixture(scope="function")
async def engine_fixture():
    if TEST_MODE == "REAL":
        # REAL MODE: Use Postgres
        database_url = os.getenv("TEST_DATABASE_URL")
        if not database_url:
            database_url = os.getenv(
                "DATABASE_URL",
            )
            formatted_url = database_url.replace("postgresql://", "postgresql+asyncpg://") if "asyncpg" not in database_url else database_url
            logger.info(f"REAL MODE: Using Database {formatted_url}")

        engine = create_async_engine(formatted_url, echo=False)

        # Verify connection & Reset
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            pytest.fail(f"Could not connect to Real DB at {formatted_url}: {e}")

        yield engine

        # Cleanup
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    else:
        # FAKE MODE: Use SQLite In-Memory
        logger.info("FAKE MODE: Using SQLite In-Memory Database")
        TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
        engine = create_async_engine(
            TEST_DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield engine
        await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(engine_fixture):
    # Bind session to the engine
    session_factory = async_sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine_fixture)

    async with session_factory() as session:
        yield session
        pass


# --- Test Client Fixture ---


@pytest.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as ac:
        yield ac

    app.dependency_overrides.clear()
