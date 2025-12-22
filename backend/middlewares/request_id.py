from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from core.logging_context import set_request_id, generate_request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates a unique Request ID for every incoming request.
    The ID is added to the request state, context variables, and response headers.
    """

    async def dispatch(self, request: Request, call_next):
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", generate_request_id())

        # Store in both request.state AND context variables
        request.state.request_id = request_id
        set_request_id(request_id)  # ← This makes it available everywhere

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
