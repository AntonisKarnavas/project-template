from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError, ExpiredSignatureError
from config import settings
from core.logging_context import set_user_id
import logging
import time

logger = logging.getLogger("api.auth")

# List of paths that do not require authentication context to be logged/processed
PUBLIC_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc", "/metrics"}


class UserContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract user information from the Authorization header.

    Sets:
        request.state.authenticated (bool): True if valid token is present.
        request.state.user_id (str | None): The user ID (sub) from the token.
        request.state.user (dict | None): The full user context/payload.
    """

    async def dispatch(self, request: Request, call_next):
        # Initialize state
        request.state.authenticated = False
        request.state.user_id = None
        request.state.user = None

        auth_header = request.headers.get("Authorization")
        token = None

        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        elif "access_token" in request.cookies:
            # Fallback to cookie
            token = request.cookies.get("access_token")
            # Handle possible "Bearer " prefix in cookie value just in case
            if token and token.startswith("Bearer "):
                token = token.split(" ")[1]

        if token:
            try:
                payload = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
                )
                username: str = payload.get("sub")
                exp: int = payload.get("exp")

                if username:
                    request.state.authenticated = True
                    request.state.user_id = username
                    request.state.user = {"username": username}

                    # Store in context variables for logging
                    set_user_id(str(username))

                    # Check for token refresh hint (e.g., if expiring in < 5 minutes)
                    if exp:
                        now = time.time()
                        if exp - now < settings.REFRESH_HINT_WINDOW_SECONDS:
                            request.state.token_expiring_soon = True

            except ExpiredSignatureError:
                logger.warning(f"Expired token used. IP: {request.client.host}")
                return Response("Token expired", status_code=401)
            except JWTError as e:
                logger.warning(
                    f"Invalid token signature. IP: {request.client.host}, Error: {str(e)}"
                )
                return Response("Invalid token", status_code=401)
            except Exception as e:
                logger.error(f"Auth middleware error: {str(e)}")
                # Don't block for generic errors, let it fail downstream or just be unauthenticated
                pass
        
        # Check for Redis Session if not authenticated via JWT
        if not request.state.authenticated:
            session_id = request.cookies.get("session_id")
            if session_id:
                from security.redis import redis_client
                from security.session_manager import SessionManager

                try:
                    session_manager = SessionManager(redis_client)
                    session_data = await session_manager.get_session(session_id)
                    
                    if session_data:
                        user_id = session_data.get("user_id")
                        email = session_data.get("email")
                        if user_id:
                            request.state.authenticated = True
                            request.state.user_id = str(user_id)
                            request.state.user = {"id": user_id, "email": email}
                            set_user_id(str(user_id))
                            
                            # Optionally refresh session on activity? 
                            # For now we rely on the client hitting an endpoint that refreshes it 
                            # or just let it expire in 24h. 
                            # But standard session behavior usually slides the window.
                            # await session_manager.refresh_session(session_id) 
                except Exception as e:
                    logger.error(f"Session auth middleware error: {str(e)}")
                    pass

        response = await call_next(request)

        # Add refresh hint if needed and authenticated
        if request.state.authenticated and getattr(
            request.state, "token_expiring_soon", False
        ):
            response.headers["X-Token-Expiring-Soon"] = "true"

        return response
