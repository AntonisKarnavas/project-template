from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
import asyncio
import logging
import json
import re
import time
from typing import Optional, Dict
from config import settings

# Structured Logging Setup
logger = logging.getLogger("api.size_limit")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(settings.LOG_LEVEL)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that checks the Content-Length header of incoming requests.
    If the size exceeds the configured limit, it returns a 413 Request Entity Too Large response.
    Includes structured logging, configurable limits, and metrics.
    """

    def __init__(self, app):
        super().__init__(app)
        # In-memory metrics
        self.metrics = {
            "rejected_total": 0,
            "rejected_per_endpoint": {},
        }
        self.metrics_lock = None

    async def dispatch(self, request: Request, call_next):
        if self.metrics_lock is None:
            self.metrics_lock = asyncio.Lock()

        request_id = getattr(request.state, "request_id", "unknown")
        limit = self.get_limit_for_request(request.url.path, request.method)

        content_length_header = request.headers.get("content-length")

        if content_length_header:
            try:
                content_length = int(content_length_header)
                if content_length > limit:
                    await self.log_rejection(request, request_id, content_length, limit)
                    await self.update_metrics(request.url.path)

                    response = Response("Request entity too large", status_code=413)
                    response.headers["X-Request-ID"] = request_id
                    response.headers["X-Max-Content-Length"] = str(limit)
                    return response

            except ValueError:
                logger.warning(
                    json.dumps(
                        {
                            "event": "invalid_content_length",
                            "request_id": request_id,
                            "method": request.method,
                            "path": request.url.path,
                            "header_value": content_length_header,
                            "message": "Invalid Content-Length header value received",
                        }
                    )
                )
                # We interpret invalid content-length as suspicious but let it pass
                # (or could block depending on strictness. Here we pass per graceful handling req).
                pass

        return await call_next(request)

    def get_limit_for_request(self, path: str, method: str) -> int:
        """
        Determine size limit based on configuration rules.
        """
        for rule in settings.SIZE_LIMIT_RULES:
            # Check method match (if specified)
            if rule.method and rule.method.upper() != method.upper():
                continue

            # Check path match (regex or prefix)
            if re.match(rule.path_pattern, path):
                return rule.limit

        return settings.MAX_UPLOAD_SIZE

    async def log_rejection(
        self, request: Request, request_id: str, content_length: int, limit: int
    ):
        """
        Log rejection event with structured data.
        """
        log_data = {
            "event": "request_rejected_size_limit",
            "timestamp": time.time(),
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "content_length": content_length,
            "limit": limit,
        }
        logger.warning(json.dumps(log_data))

    async def update_metrics(self, path: str):
        """
        Update in-memory metrics in a thread-safe way.
        """
        async with self.metrics_lock:
            self.metrics["rejected_total"] += 1

            # Update per-endpoint
            current_endpoint_count = self.metrics["rejected_per_endpoint"].get(path, 0)
            self.metrics["rejected_per_endpoint"][path] = current_endpoint_count + 1
