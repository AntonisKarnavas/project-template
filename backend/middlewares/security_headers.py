from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import json
import re
import time
from config import settings

# Structured Logging Setup
logger = logging.getLogger("api.security_headers")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(settings.LOG_LEVEL)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds various security headers to the response to protect against
    common attacks like XSS, Clickjacking, and MIME sniffing.

    Now supports:
    - Configurable settings via config.py
    - Per-endpoint overrides
    - Conditional HSTS
    - Structured logging
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Determine strict mode or overrides for current path
        path = request.url.path

        # Default security values
        x_frame = settings.SECURITY_X_FRAME_OPTIONS
        csp = settings.SECURITY_CONTENT_SECURITY_POLICY
        permissions = settings.SECURITY_PERMISSIONS_POLICY

        # Check for overrides
        matched_override = None
        for override in settings.SECURITY_OVERRIDES:
            if re.match(override.path_pattern, path):
                matched_override = override
                if override.x_frame_options:
                    x_frame = override.x_frame_options
                if override.content_security_policy:
                    csp = override.content_security_policy
                if override.permissions_policy:
                    permissions = override.permissions_policy
                break

        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent Clickjacking (Configurable)
        response.headers["X-Frame-Options"] = x_frame

        # Enable XSS protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Enforce HTTPS (HSTS) - Conditional
        # Apply if FORCE_HTTPS is True OR if request is HTTPS
        is_https = (
            request.url.scheme == "https"
            or request.headers.get("x-forwarded-proto") == "https"
        )

        if settings.SECURITY_FORCE_HTTPS or is_https:
            hsts_val = f"max-age={settings.SECURITY_HSTS_MAX_AGE}"
            if settings.SECURITY_HSTS_INCLUDE_SUBDOMAINS:
                hsts_val += "; includeSubDomains"
            if settings.SECURITY_HSTS_PRELOAD:
                hsts_val += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_val

        # Content Security Policy
        response.headers["Content-Security-Policy"] = csp

        # Permissions Policy
        response.headers["Permissions-Policy"] = permissions

        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Structured Log (Debug level to avoid noise, or Info if needed)
        # We'll log at DEBUG unless there was an override, then maybe INFO?
        # For now, let's keep it consistent.
        if settings.LOG_LEVEL == "DEBUG":
            log_data = {
                "event": "security_headers_applied",
                "path": path,
                "x_frame_options": x_frame,
                "hsts_applied": settings.SECURITY_FORCE_HTTPS or is_https,
                "override_matched": bool(matched_override),
            }
            logger.debug(json.dumps(log_data))

        return response
