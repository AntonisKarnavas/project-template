import time
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
from core.logging_context import set_request_id, set_user_id


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs incoming requests and outgoing responses in JSON format.
    Also tracks and logs the request duration.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Prepare initial log data
        # request_id and user_id are automatically added by log_formatter
        context_logger = logger.bind(
            method=request.method,
            url=str(request.url),
            client=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            referer=request.headers.get("referer"),
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Determine log level based on status code
            if response.status_code >= 500:
                log_func = context_logger.error
            elif response.status_code >= 400:
                log_func = context_logger.warning
            else:
                log_func = context_logger.info

            # Add X-Process-Time header
            response.headers["X-Process-Time"] = str(process_time)

            # Ensure context is set for logging (propagate up from inner middlewares via state)
            if hasattr(request.state, "request_id"):
                set_request_id(request.state.request_id)
            if hasattr(request.state, "user_id"):
                set_user_id(request.state.user_id)

            # Log with structured data
            log_func(
                "Request processed",
                status_code=response.status_code,
                duration=round(process_time, 4),
                response_size=response.headers.get("content-length"),
            )

            return response

        except Exception as e:
            process_time = time.time() - start_time

            # Ensure context is set for logging
            if hasattr(request.state, "request_id"):
                set_request_id(request.state.request_id)
            if hasattr(request.state, "user_id"):
                set_user_id(request.state.user_id)

            context_logger.error(
                "Request failed",
                status_code=500,
                duration=round(process_time, 4),
                error=str(e),
            )
            raise e
