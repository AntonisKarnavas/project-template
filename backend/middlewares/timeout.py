from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
import asyncio
import logging
import json
import re
import time
from typing import Optional, Dict
from config import settings, TimeoutRule

# Structured Logging Setup
logger = logging.getLogger("api.timeout")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(settings.LOG_LEVEL)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce a timeout on request processing with structured logging,
    per-endpoint configuration, and metrics tracking.
    """

    def __init__(self, app):
        super().__init__(app)
        # In-memory metrics
        self.metrics = {
            "total_timeouts": 0,
            "timeouts_per_endpoint": {},
            "timeouts_per_method": {},
        }
        self.metrics_lock = None

    async def dispatch(self, request: Request, call_next):
        request_id = getattr(request.state, "request_id", "unknown")
        timeout_value = self.get_timeout_for_request(request.url.path, request.method)

        start_time = time.time()

        try:
            return await asyncio.wait_for(call_next(request), timeout=timeout_value)

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            await self.log_timeout(request, request_id, duration, timeout_value)
            await self.update_metrics(request.url.path, request.method)

            # Return error response with X-Request-ID
            response = Response("Request timed out", status_code=504)
            response.headers["X-Request-ID"] = request_id
            return response

        except asyncio.CancelledError:
            # Client disconnected
            logger.info(
                json.dumps(
                    {
                        "event": "request_cancelled",
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "message": "Request cancelled by client",
                    }
                )
            )
            raise  # Re-raise to let server handle disconnection

        except Exception as e:
            # Log other asyncio exceptions if any
            logger.error(
                json.dumps(
                    {
                        "event": "asyncio_exception",
                        "request_id": request_id,
                        "error": str(e),
                        "type": type(e).__name__,
                    }
                )
            )
            raise e

        finally:
            # Cleanup logic if needed (e.g. closing resources attached to request state)
            # Most cleanup is handled by dependencies, but this block ensures
            # we can add custom cleanup if necessary.
            pass

    def get_timeout_for_request(self, path: str, method: str) -> int:
        """
        Determine timeout value based on configuration rules.
        """
        for rule in settings.TIMEOUT_RULES:
            # Check method match (if specified)
            if rule.method and rule.method.upper() != method.upper():
                continue

            # Check path match (regex or prefix)
            # Assuming simple prefix match for now, or regex if it looks like one
            if re.match(rule.path_pattern, path):
                return rule.timeout

        return settings.REQUEST_TIMEOUT

    async def log_timeout(
        self, request: Request, request_id: str, duration: float, timeout_limit: int
    ):
        """
        Log timeout event with structured data.
        """
        log_data = {
            "event": "request_timeout",
            "timestamp": time.time(),
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "duration": duration,
            "timeout_limit": timeout_limit,
        }
        logger.warning(json.dumps(log_data))

    async def update_metrics(self, path: str, method: str):
        """
        Update in-memory metrics in a thread-safe way.
        """
        if self.metrics_lock is None:
            self.metrics_lock = asyncio.Lock()

        async with self.metrics_lock:
            self.metrics["total_timeouts"] += 1

            # Update per-endpoint
            current_endpoint_count = self.metrics["timeouts_per_endpoint"].get(path, 0)
            self.metrics["timeouts_per_endpoint"][path] = current_endpoint_count + 1

            # Update per-method
            current_method_count = self.metrics["timeouts_per_method"].get(method, 0)
            self.metrics["timeouts_per_method"][method] = current_method_count + 1
