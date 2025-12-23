import argparse
import asyncio

import asyncpg
from sqlalchemy import MetaData

from database.core import check_connection, engine, settings
from database.models import Base


async def create_database_if_not_exists():
    """
    Creates the database if it doesn't exist.
    Connects to the default 'postgres' database to execute the CREATE DATABASE command.
    """
    sys_conn = await asyncpg.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        host=settings.POSTGRES_SERVER,
        port=settings.POSTGRES_PORT,
        database="postgres",
    )

    try:
        # Check if database exists
        exists = await sys_conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", settings.POSTGRES_DB)
        if not exists:
            print(f"Database '{settings.POSTGRES_DB}' does not exist. Creating...")
            # CREATE DATABASE cannot run inside a transaction block
            await sys_conn.execute(f'CREATE DATABASE "{settings.POSTGRES_DB}"')
            print(f"Database '{settings.POSTGRES_DB}' created successfully.")
        else:
            print(f"Database '{settings.POSTGRES_DB}' already exists.")
    except Exception as e:
        print(f"Error creating database: {e}")
    finally:
        await sys_conn.close()


async def setup_db():
    """
    Creates the database (if missing) and all tables defined in the models.
    """
    await create_database_if_not_exists()
    print("Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")


async def drop_db():
    """
    Drops all tables in the database.
    Does NOT drop the database itself.
    """
    print("Dropping tables...")
    async with engine.begin() as conn:
        # Reflect existing tables to ensure we drop everything, including zombie tables
        meta = MetaData()
        await conn.run_sync(meta.reflect)
        await conn.run_sync(meta.drop_all)
    print("Tables dropped.")


async def reset_db():
    """
    Resets the database by dropping and recreating all tables.
    """
    await drop_db()
    await setup_db()


async def main():
    parser = argparse.ArgumentParser(description="Database management script")
    parser.add_argument("--setup", action="store_true", help="Create database and tables")
    parser.add_argument("--drop", action="store_true", help="Drop database tables")
    parser.add_argument("--reset", action="store_true", help="Reset database (drop and create tables)")
    parser.add_argument("--check", action="store_true", help="Check database connection")

    args = parser.parse_args()

    if args.check:
        await check_connection()
    elif args.reset:
        await reset_db()
    elif args.drop:
        await drop_db()
    elif args.setup:
        await setup_db()
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
