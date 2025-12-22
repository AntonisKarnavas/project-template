import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler for 500 errors.
    """
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(f"Unhandled exception for request {request_id}: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "request_id": request_id,
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please contact support.",
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Preserve default HTTPException behavior but ensure structured JSON if needed.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "request_id": request_id, "code": "HTTP_ERROR"},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with structured response.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation Error",
            "details": exc.errors(),
            "request_id": request_id,
            "code": "VALIDATION_ERROR",
        },
    )


def create_exception_handlers(app: FastAPI):
    app.add_exception_handler(Exception, generic_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
