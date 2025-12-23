# Backend

A robust FastAPI backend with Firebase Authentication, async PostgreSQL, and production-ready middleware stack.

## Table of Contents

- [Project Structure](#project-structure)
- [Setup](#setup)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Alembic Migrations](#alembic-migrations)
- [Running the Application](#running-the-application)
- [Middlewares](#middlewares)
- [Testing](#testing)
- [Docker](#docker)

---

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── config.py               # Application settings and configuration
├── requirements.txt        # Python dependencies
├── Makefile                # Common development commands
├── alembic.ini             # Alembic configuration
├── pytest.ini              # Pytest configuration
├── docker-compose.yml      # Docker services (PostgreSQL)
├── .env.template           # Environment variables template
│
├── core/                   # Core utilities and shared logic
│   ├── errors.py           # Custom exception handlers
│   ├── firebase.py         # Firebase Admin SDK initialization
│   ├── logging.py          # Structured logging configuration
│   └── logging_context.py  # Request-scoped logging context
│
├── database/               # Database layer
│   ├── __init__.py
│   ├── core.py             # Async SQLAlchemy engine & session
│   ├── models.py           # SQLAlchemy ORM models
│   └── setup.py            # Database management script (create/drop/reset)
│
├── middlewares/            # HTTP middleware stack
│   ├── logging.py          # Request/response logging
│   ├── request_id.py       # Unique request ID generation
│   ├── security_headers.py # Security headers (HSTS, CSP, etc.)
│   ├── size_limit.py       # Request body size limiting
│   ├── timeout.py          # Request timeout enforcement
│   └── validation.py       # Input validation & sanitization
│
├── migrations/             # Alembic migrations
│   ├── env.py              # Alembic environment (async config)
│   ├── script.py.mako      # Migration script template
│   └── versions/           # Migration version files
│
├── pydantic_models/        # Pydantic schemas
│   ├── schemas.py          # Request/response models
│   └── validation.py       # Endpoint-specific validation schemas
│
├── routers/                # API route handlers
│   ├── firebase_auth.py    # Firebase authentication endpoints
│   └── health.py           # Health check endpoints
│
├── security/               # Security utilities
│   ├── auth.py             # Firebase token verification & user handling
│   └── docs.py             # OpenAPI documentation configuration
│
├── services/               # Business logic services
│   └── logic.py            # Application business logic
│
├── tests/                  # Test suite
│   └── conftest.py         # Pytest fixtures
│
├── grafana/                # Grafana dashboards & config
└── scripts/                # Utility scripts (empty, for future use)
```

---

## Setup

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (for PostgreSQL)
- Firebase project with service account

### Installation

1. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   # Or using Makefile:
   make install
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

4. **Add Firebase credentials**:
   - Download your Firebase service account JSON from:
     Firebase Console → Project Settings → Service Accounts → Generate New Private Key
   - Save as `firebase-service-account.json` in the backend directory
   - Update `FIREBASE_SERVICE_ACCOUNT_PATH` in `.env` if using a different path

---

## Environment Variables

Copy `.env.template` to `.env` and configure:

| Variable                        | Description                            | Default                                     |
| ------------------------------- | -------------------------------------- | ------------------------------------------- |
| `FIREBASE_SERVICE_ACCOUNT_PATH` | Path to Firebase service account JSON  | `./firebase-service-account.json`           |
| `SECRET_KEY`                    | Application secret key                 | `your-secret-key-change-this-in-production` |
| `SECURITY_FORCE_HTTPS`          | Force HTTPS redirects                  | `False`                                     |
| `REDIS_URL`                     | Redis connection URL                   | `redis://localhost:6379/0`                  |
| `ALLOWED_ORIGINS`               | CORS allowed origins (comma-separated) | `http://localhost:3000,...`                 |
| `ENVIRONMENT`                   | Environment mode (`dev`, `prod`)       | `dev`                                       |

Database configuration is set in `config.py` with defaults for local PostgreSQL.

---

## Database Setup

### Using Docker (Recommended)

Start PostgreSQL with Docker Compose:

```bash
docker-compose up -d
```

This starts a PostgreSQL instance on port `5432` with default credentials.

### Database Management Script

The `database/setup.py` script provides commands for database management:

```bash
# Create database and tables
python -m database.setup --setup

# Check database connection
python -m database.setup --check

# Drop all tables (data loss!)
python -m database.setup --drop

# Reset database (drop + recreate tables)
python -m database.setup --reset
```

---

## Alembic Migrations

This project uses [Alembic](https://alembic.sqlalchemy.org/) for database migrations with async support.

### Key Files

| File                        | Purpose                                        |
| --------------------------- | ---------------------------------------------- |
| `alembic.ini`               | Main Alembic configuration                     |
| `migrations/env.py`         | Environment configuration for async SQLAlchemy |
| `migrations/script.py.mako` | Template for generating new migration scripts  |
| `migrations/versions/`      | Directory containing all migration scripts     |

### Common Commands

```bash
# Check current database revision
alembic current

# Show migration history
alembic history

# Create a new migration (autogenerate from models)
alembic revision --autogenerate -m "describe your changes"

# Apply all pending migrations
alembic upgrade head

# Apply migrations one at a time
alembic upgrade +1

# Revert the last migration
alembic downgrade -1

# Revert all migrations
alembic downgrade base
```

### Starting Fresh

To delete all migrations and start clean:

```bash
# 1. Remove all migration versions
rm -rf migrations/versions/*

# 2. Generate a fresh initial migration
alembic revision --autogenerate -m "initial migration"

# 3. Apply the migration
alembic upgrade head
```

> **Note**: If your database already has tables, you may need to drop them first
> or mark the migration as applied: `alembic stamp head`

---

## Running the Application

### Development

```bash
# Using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8030

# Using Makefile
make run
```

The API will be available at `http://localhost:8030`.

### API Documentation

- **Swagger UI**: `http://localhost:8030/docs`
- **ReDoc**: `http://localhost:8030/redoc`

---

## Middlewares

The middleware stack processes requests in order (top to bottom):

### 1. RequestIDMiddleware (`middlewares/request_id.py`)

Generates a unique request ID for every incoming request.

- Reads `X-Request-ID` header if provided, otherwise generates a UUID
- Stores ID in `request.state.request_id` and context variables
- Adds `X-Request-ID` header to responses

### 2. RequestLoggingMiddleware (`middlewares/logging.py`)

Logs all requests and responses in structured JSON format.

- Records request method, URL, client IP, user agent
- Tracks request duration and response status code
- Adds `X-Process-Time` header to responses
- Uses appropriate log levels based on status codes (error for 5xx, warning for 4xx)

### 3. SecurityHeadersMiddleware (`middlewares/security_headers.py`)

Adds security headers to protect against common web attacks.

- **X-Content-Type-Options**: `nosniff` (prevent MIME sniffing)
- **X-Frame-Options**: Configurable (prevent clickjacking)
- **X-XSS-Protection**: `1; mode=block` (XSS protection for older browsers)
- **Strict-Transport-Security**: Conditional HSTS
- **Content-Security-Policy**: Configurable CSP
- **Permissions-Policy**: Feature restrictions
- **Referrer-Policy**: `strict-origin-when-cross-origin`

Supports per-endpoint overrides via `config.py`.

### 4. RequestSizeLimitMiddleware (`middlewares/size_limit.py`)

Prevents oversized request payloads.

- Returns `413 Request Entity Too Large` if Content-Length exceeds limit
- Configurable per-endpoint limits via `SIZE_LIMIT_RULES` in config
- Tracks rejection metrics in memory

### 5. TimeoutMiddleware (`middlewares/timeout.py`)

Enforces request processing timeouts.

- Returns `504 Gateway Timeout` if request processing exceeds limit
- Configurable per-endpoint timeouts via `TIMEOUT_RULES` in config
- Handles client disconnections gracefully

### 6. RequestValidationMiddleware (`middlewares/validation.py`)

Validates and sanitizes request inputs.

- Sanitizes query parameters and JSON body using [Bleach](https://bleach.readthedocs.io/)
- Validates against Pydantic schemas defined in `pydantic_models/validation.py`
- Enforces JSON depth limits to prevent DoS attacks
- Can be disabled via `VALIDATION_ENABLED` setting

---

## Testing

### Running Tests

```bash
# Run all tests with pytest
pytest

# Using Makefile
make test

# Run with verbose output
pytest -vv

# Run specific test file
pytest tests/test_auth.py

# Run tests matching a pattern
pytest -k "test_login"
```

### Test Configuration

The `pytest.ini` configures:

- Async mode: `auto` (automatically handles async tests)
- Verbose output: `-vv`
- Logging: CLI logs at INFO level

### Writing Tests

Test fixtures are defined in `tests/conftest.py`:

- `app` - Test FastAPI application
- `client` - Async HTTP test client
- `db_session` - Test database session

---

## Docker

### Starting Services

```bash
# Start PostgreSQL
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Using Makefile

```bash
make install   # Install dependencies + pre-commit hooks
make run       # Start development server
make test      # Run test suite
make lint      # Check code with ruff
make format    # Format code with ruff
make clean     # Remove __pycache__ and .pyc files
```

---

## Code Quality

### Linting & Formatting

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check for issues
ruff check .
# Or: make lint

# Format code
ruff format .
# Or: make format
```

### Pre-commit Hooks

Pre-commit hooks are configured in `.pre-commit-config.yaml`. Install with:

```bash
pre-commit install
```
