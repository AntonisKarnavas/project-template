from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings

# Create the Async Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Set to False in production
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions, useful for scripts and background tasks.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_connection():
    """
    Checks the database connection.
    """
    try:
        async with engine.connect() as conn:
            await conn.run_sync(lambda x: x.execute("SELECT 1"))
        print("Database connection successful.")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False
