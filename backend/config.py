from enum import Enum
from typing import List, Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    DEV = "dev"
    UAT = "uat"
    PROD = "prod"


class TimeoutRule(BaseModel):
    path_pattern: str
    method: Optional[str] = None  # None means all methods
    timeout: int


class SizeLimitRule(BaseModel):
    path_pattern: str
    method: Optional[str] = None
    limit: int


class SecurityOverrides(BaseModel):
    path_pattern: str
    # Optional overrides for specific headers
    x_frame_options: Optional[str] = None
    content_security_policy: Optional[str] = None
    permissions_policy: Optional[str] = None


class Settings(BaseSettings):
    # Security
    ALLOWED_HOSTS: List[str] = [
        "localhost",
        "127.0.0.1",
        "host.docker.internal",
        "testserver",
    ]
    ALLOWED_ORIGINS: List[str]
    ENVIRONMENT: Environment = Environment.DEV

    # Security Headers
    SECURITY_HSTS_MAX_AGE: int = 31536000
    SECURITY_HSTS_INCLUDE_SUBDOMAINS: bool = True
    SECURITY_HSTS_PRELOAD: bool = False
    SECURITY_FORCE_HTTPS: bool = False
    SECURITY_X_FRAME_OPTIONS: str = "DENY"
    SECURITY_CONTENT_SECURITY_POLICY: str = "default-src 'self'"
    SECURITY_PERMISSIONS_POLICY: str = "geolocation=(), microphone=(), camera=()"
    SECURITY_OVERRIDES: List[SecurityOverrides] = []

    # Firebase Configuration
    FIREBASE_SERVICE_ACCOUNT_PATH: Optional[str] = None

    # Database Configuration
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str

    # SQLAlchemy Engine Tuning
    DB_POOL_SIZE: int = 5  # Number of connections to keep open
    DB_MAX_OVERFLOW: int = 10  # Connections allowed above pool_size
    DB_POOL_RECYCLE: int = 3600  # Recycle connections after N seconds

    @property
    def DATABASE_URL(self) -> str:
        """Constructs the SQLAlchemy async database URL."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Performance
    MAX_UPLOAD_SIZE: int = 10_000_000  # 10MB
    REQUEST_TIMEOUT: int = 10  # seconds

    # Timeout Rules
    # Example: TIMEOUT_RULES = [TimeoutRule(path_pattern="^/heavy-computation", timeout=30)]
    TIMEOUT_RULES: List["TimeoutRule"] = []

    # Size Limit Rules
    # Example: SIZE_LIMIT_RULES = [SizeLimitRule(path_pattern="^/upload/large", limit=50_000_000)]
    SIZE_LIMIT_RULES: List["SizeLimitRule"] = []

    # Logging
    LOG_LEVEL: str = "INFO"

    # Validation & Sanitization
    VALIDATION_ENABLED: bool = True
    VALIDATION_STRICT_MODE: bool = True  # If True, rejects unknown parameters
    VALIDATION_EXCLUDED_PATHS: List[str] = ["/docs", "/redoc", "/openapi.json"]

    # Bleach Sanitization Settings
    ALLOWED_TAGS: List[str] = [
        "a",
        "abbr",
        "acronym",
        "b",
        "blockquote",
        "code",
        "em",
        "i",
        "li",
        "ol",
        "strong",
        "ul",
        "p",
        "br",
    ]
    ALLOWED_ATTRIBUTES: dict = {
        "a": ["href", "title"],
        "abbr": ["title"],
        "acronym": ["title"],
    }

    # JSON Validation
    MAX_JSON_DEPTH: int = 10  # Prevent DoS via deep nesting

    # Docs Security
    DOCS_USERNAME: str = "admin"
    DOCS_PASSWORD: str = "admin"

    # Test Configuration
    TEST_DATABASE_MODE: str = "FAKE"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# Default Security Overrides for Docs
# Allow Swagger UI resources (CDN scripts, styles, etc.)
docs_csp = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' https://fastapi.tiangolo.com data:;"
)

settings.SECURITY_OVERRIDES.extend(
    [
        SecurityOverrides(path_pattern=r"^/docs", content_security_policy=docs_csp),
        SecurityOverrides(path_pattern=r"^/redoc", content_security_policy=docs_csp),
        SecurityOverrides(path_pattern=r"^/openapi.json", content_security_policy=docs_csp),
    ]
)
