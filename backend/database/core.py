from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator
from pydantic_settings import BaseSettings, SettingsConfigDict
from contextlib import asynccontextmanager


class Settings(BaseSettings):
    """
    Database configuration settings.
    Reads from environment variables or .env file.
    """

    # Postgres Connection Credentials
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    # SQLAlchemy Engine Tuning
    # pool_size: The number of connections to keep open inside the connection pool.
    DB_POOL_SIZE: int = 5
    # max_overflow: The number of connections to allow in overflow, that is,
    # connections that can be opened above and beyond the pool_size setting.
    DB_MAX_OVERFLOW: int = 10
    # pool_recycle: This setting causes the pool to recycle connections after the given
    # number of seconds has passed. It defaults to -1, or no timeout.
    DB_POOL_RECYCLE: int = 3600

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def DATABASE_URL(self) -> str:
        """Constructs the SQLAlchemy async database URL."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()

# Create the Async Engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # Set to False in production
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_recycle=settings.DB_POOL_RECYCLE,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


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
