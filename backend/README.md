# Project Template

This is a robust FastAPI project template designed for scalability and maintainability.

## Features

- **FastAPI**: High performance, easy to learn, fast to code, ready for production.
- **PostgreSQL (Async)**: Using `SQLAlchemy` and `asyncpg`.
- **Migrations**: Using `Alembic`.
- **Redis**: For caching and background jobs (if applicable).
- **Authentication**: JWT based auth.
- **Observability**: Prometheus metrics, structured logging.
- **Testing**: `pytest` setup with async support.
- **Docker**: Containerized environment.

## Database Migrations

This project uses [Alembic](https://alembic.sqlalchemy.org/en/latest/) for database migrations.

### Creating a Migration

After modifying your SQLAlchemy models in `database/models.py`, generate a new migration script:

```bash
alembic revision --autogenerate -m "describe your changes here"
```

This will create a new file in `migrations/versions/`. Always verify the generated script to ensure it accurately reflects your changes.

### Applying Migrations

To apply pending migrations and update your database schema:

```bash
alembic upgrade head
```

### Common Commands

- `alembic current`: Check the current revision of the database.
- `alembic history`: Show changes in chronological order.
- `alembic downgrade -1`: Revert the last migration.

## Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional, for running dependencies easily)

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repo_url>
   cd project_template
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Copy the example environment file (if available) or create `.env`:
   ```bash
   # Create .env file based on your config.py defaults
   touch .env
   ```

## Running the Application

To run the application locally with hot-reloading:

```bash
uvicorn main:app --reload
```
Or using the Makefile (if available):
```bash
make run
```

The API will be available at `http://localhost:8030`.

## Running Tests

Run the test suite using `pytest`:

```bash
pytest
```
Or with Makefile:
```bash
make test
```

## Docker

To stand up the database and other services (Redis, etc.):

```bash
docker-compose up -d
```
