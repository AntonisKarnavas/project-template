import pytest
import asyncio
import os
import logging
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from database.models import Base
from main import app
from database.core import get_db
from security.redis import get_redis
from redis.asyncio import Redis as AsyncRedis

# Configure logging
logger = logging.getLogger(__name__)

# Determine Test Mode: "FAKE" (default) or "REAL"
# Determine Test Mode: "FAKE" (default) or "REAL"
# We access os.getenv just to be safe if settings is not fully loaded, 
# but preferably use settings if available. However, settings loads .env so it should match.
# Let's use the settings object to consistency.
from config import settings
TEST_MODE = settings.TEST_DATABASE_MODE.upper()

# --- Mock Implementations (for FAKE mode) ---

class MockRedis:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def setex(self, key, time, value):
        self.store[key] = value

    async def delete(self, key):
        if key in self.store:
            del self.store[key]

    async def set(self, key, value):
        self.store[key] = value

    async def close(self):
        pass

# --- DB Engine Fixture ---

@pytest.fixture(scope="function")
async def engine_fixture():
    if TEST_MODE == "REAL":
        # REAL MODE: Use Postgres
        database_url = os.getenv("TEST_DATABASE_URL")
        if not database_url:
            database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db")
            formatted_url = database_url.replace("postgresql://", "postgresql+asyncpg://") if "asyncpg" not in database_url else database_url
            logger.info(f"REAL MODE: Using Database {formatted_url}")
        
        # Function-scoped engine for isolation? 
        # Actually, creating an engine per test is expensive for Postgres. 
        # But for resolving the scope mismatch quickly, this is safest.
        # Alternatively, we could keep session scope but configure pytest-asyncio correctly.
        # Let's stick to function scope for now to get green tests.
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
        # Function scope = new memory DB per test. Very clean.
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
    session_factory = async_sessionmaker(
        autocommit=False, autoflush=False, expire_on_commit=False, bind=engine_fixture
    )

    async with session_factory() as session:
        yield session
        # No explicit cleanup needed for SQLite memory function-scope (engine dispose kills it).
        # For Real DB function-scope, we droppped/created in engine fixture? 
        # Be careful: engine_fixture yields engine, then waits. 
        # db_session yields session, then closes.
        # engine_fixture teardown (drop_all) happens AFTER db_session teardown.
        # So we don't strictly need to delete rows here if engine fixture drops all.
        pass


# --- Redis Fixture ---

@pytest.fixture(scope="function")
async def redis_client():
    if TEST_MODE == "REAL":
        redis_url = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")
        logger.info(f"REAL MODE: Using Redis at {redis_url}")
        client = AsyncRedis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        yield client
        await client.flushdb()
        await client.close()
    else:
        logger.info("FAKE MODE: Using MockRedis")
        yield MockRedis()



@pytest.fixture(scope="function")
async def redis_fixture(redis_client):
    # Yield the client
    yield redis_client
    # Cleanup after each test
    if TEST_MODE == "REAL":
        await redis_client.flushdb()
    else:
        # Reset mock store
        redis_client.store = {}


# --- Test Client Fixture ---

@pytest.fixture(scope="function")
async def client(db_session, redis_fixture):
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        yield redis_fixture

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
