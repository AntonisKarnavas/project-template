import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
import logging
import json
import bleach
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from config import settings
from pydantic_models.validation import ENDPOINT_SCHEMAS
from pydantic import ValidationError

# Structured Logging Setup
logger = logging.getLogger("api.security")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(settings.LOG_LEVEL)


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate and sanitize request query parameters, headers, and body.
    Uses Pydantic for schema validation and Bleach for HTML sanitization.
    """

    async def dispatch(self, request: Request, call_next):
        if not settings.VALIDATION_ENABLED:
            return await call_next(request)

        # Skip excluded paths
        if any(
            request.url.path.startswith(path)
            for path in settings.VALIDATION_EXCLUDED_PATHS
        ):
            return await call_next(request)

        request_id = getattr(request.state, "request_id", "unknown")

        # 1. Sanitize and Validate Query Parameters
        try:
            # Get all items including duplicates
            query_items = list(request.query_params.multi_items())
            sanitized_items = self._sanitize_query_items(query_items)

            # Reconstruct query params for validation (using a dict for Pydantic)
            sanitized_dict = {}
            for k, v in sanitized_items:
                sanitized_dict[k] = v

            self._validate_query_params(request, sanitized_dict)

            # Update request scope with sanitized query string
            # This ensures downstream endpoints see the sanitized values
            request.scope["query_string"] = urlencode(sanitized_items).encode("utf-8")
            # Clear cached query_params so they are re-parsed from scope
            if hasattr(request, "_query_params"):
                del request._query_params

        except ValidationError as e:
            self._log_violation(request, "query_validation_error", str(e))
            return Response("Invalid request parameters", status_code=400)
        except Exception as e:
            self._log_violation(request, "query_sanitization_error", str(e))
            return Response("Invalid request parameters", status_code=400)

        # 2. Validate Request Body (for POST/PUT/PATCH)
        if request.method in ["POST", "PUT", "PATCH"]:
            # Only validate JSON content types
            content_type = request.headers.get("content-type", "")
            if "application/json" in content_type:
                try:
                    # We need to read the body, sanitize it, and then replace it for the next middleware/route
                    body_bytes = await request.body()
                    if body_bytes:
                        try:
                            body_json = json.loads(body_bytes)
                        except json.JSONDecodeError:
                            # Not valid JSON
                            self._log_violation(
                                request, "body_parsing_error", "Invalid JSON body"
                            )
                            return Response("Invalid request body", status_code=400)

                        self._validate_json_depth(body_json)
                        sanitized_body = self._sanitize_json_body(body_json)

                        # Re-inject sanitized body
                        sanitized_body_bytes = json.dumps(sanitized_body).encode(
                            "utf-8"
                        )

                        async def receive() -> Message:
                            return {
                                "type": "http.request",
                                "body": sanitized_body_bytes,
                            }

                        request._receive = receive
                        # Also update the cached body since we already read it
                        request._body = sanitized_body_bytes

                except ValueError as e:  # Depth limit or other validation error
                    self._log_violation(request, "body_validation_error", str(e))
                    return Response("Invalid request body", status_code=400)
                except Exception as e:
                    self._log_violation(request, "body_processing_error", str(e))
                    return Response("Invalid request body", status_code=400)

        return await call_next(request)

    def _sanitize_query_items(self, items: list) -> list:
        """Sanitize query parameter items (key, value tuples) using Bleach."""
        sanitized = []
        for key, value in items:
            if isinstance(value, str):
                clean_value = bleach.clean(
                    value,
                    tags=settings.ALLOWED_TAGS,
                    attributes=settings.ALLOWED_ATTRIBUTES,
                    strip=True,
                )
                sanitized.append((key, clean_value))
            else:
                sanitized.append((key, value))
        return sanitized

    def _validate_query_params(self, request: Request, params: Dict[str, Any]):
        """Validate query parameters against Pydantic models."""
        path = request.url.path
        schema = ENDPOINT_SCHEMAS.get(path)

        if schema:
            schema(**params)
        elif settings.VALIDATION_STRICT_MODE and params:
            # Log warning for undefined schema in strict mode
            self._log_violation(
                request,
                "strict_mode_violation",
                f"No validation schema defined for {path} but parameters present",
            )

    def _validate_json_depth(self, data: Any, current_depth: int = 0):
        """Recursively check JSON depth to prevent DoS."""
        if current_depth > settings.MAX_JSON_DEPTH:
            raise ValueError("JSON depth limit exceeded")

        if isinstance(data, dict):
            for value in data.values():
                self._validate_json_depth(value, current_depth + 1)
        elif isinstance(data, list):
            for item in data:
                self._validate_json_depth(item, current_depth + 1)

    def _sanitize_json_body(self, data: Any) -> Any:
        """Recursively sanitize strings in JSON body."""
        if isinstance(data, dict):
            return {k: self._sanitize_json_body(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_json_body(item) for item in data]
        elif isinstance(data, str):
            return bleach.clean(
                data,
                tags=settings.ALLOWED_TAGS,
                attributes=settings.ALLOWED_ATTRIBUTES,
                strip=True,
            )
        return data

    def _log_violation(self, request: Request, violation_type: str, details: str):
        """Log validation violation with structured data."""
        log_data = {
            "event": "security_violation",
            "violation_type": violation_type,
            "request_id": getattr(request.state, "request_id", "unknown"),
            "method": request.method,
            "path": request.url.path,
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "details": details,
        }
        logger.warning(json.dumps(log_data))
