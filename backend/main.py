import uvicorn
from fastapi import FastAPI, Depends
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from routers import example_router, health, auth
from config import settings, Environment

# Middlewares
from core.logging import setup_logging
from security.docs import get_current_username
from middlewares.logging import RequestLoggingMiddleware
from middlewares.request_id import RequestIDMiddleware
from middlewares.auth import UserContextMiddleware
from middlewares.size_limit import RequestSizeLimitMiddleware
from middlewares.security_headers import SecurityHeadersMiddleware
from middlewares.validation import RequestValidationMiddleware
from prometheus_fastapi_instrumentator import Instrumentator, metrics
from middlewares.timeout import TimeoutMiddleware

from core.logging import setup_logging
from core.errors import create_exception_handlers

setup_logging()

app = FastAPI(title="Project Template", docs_url=None, redoc_url=None, openapi_url=None)

# Exception Handlers
create_exception_handlers(app)

# Middlewares (Order matters: LIFO for request, FIFO for response)

# 1. Trusted Host (Security) - Reject invalid hosts early
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# 2. CORS (Security)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. GZip Compression (Performance)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 4. Security Headers (Security)
app.add_middleware(SecurityHeadersMiddleware)

# 5. Request Size Limit (Security)
app.add_middleware(RequestSizeLimitMiddleware)

# 6. Timeout (Performance) - Ensure requests don't hang forever
app.add_middleware(TimeoutMiddleware)


# 8. Validation & Sanitization (Security/Processing)
app.add_middleware(RequestValidationMiddleware)

# 9. User Context (Auth)
app.add_middleware(UserContextMiddleware)

# 10. Request ID (Observability)
app.add_middleware(RequestIDMiddleware)

# 11. Logging (Observability) - Should be outer-most to catch everything (including timing)
app.add_middleware(RequestLoggingMiddleware)


# Routers
app.include_router(auth.router)

app.include_router(example_router.router)
app.include_router(health.router)


Instrumentator().instrument(app).expose(app)

# Custom Docs (Protected in UAT/PROD)
docs_deps = []
if settings.ENVIRONMENT in [Environment.UAT, Environment.PROD]:
    docs_deps = [Depends(get_current_username)]


@app.get("/docs", include_in_schema=False, dependencies=docs_deps)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )


@app.get("/redoc", include_in_schema=False, dependencies=docs_deps)
async def redoc_html():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )


@app.get("/openapi.json", include_in_schema=False, dependencies=docs_deps)
async def get_open_api_endpoint():
    return get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )


@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Project Template"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8030, reload=True, log_config=None)
