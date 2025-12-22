from contextvars import ContextVar
from typing import Optional
import uuid

# Context variables - automatically propagate across async calls
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


def get_request_id() -> Optional[str]:
    """Get the current request ID from context"""
    return request_id_var.get()


def set_request_id(request_id: str) -> None:
    """Set the request ID in context"""
    request_id_var.set(request_id)


def get_user_id() -> Optional[str]:
    """Get the current user ID from context"""
    return user_id_var.get()


def set_user_id(user_id: str) -> None:
    """Set the user ID in context"""
    user_id_var.set(user_id)


def generate_request_id() -> str:
    """Generate a new UUID for request ID"""
    return str(uuid.uuid4())


def clear_context() -> None:
    """Clear all context variables (useful for testing)"""
    request_id_var.set(None)
    user_id_var.set(None)
