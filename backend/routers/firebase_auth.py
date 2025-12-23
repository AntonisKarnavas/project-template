"""
Firebase Authentication Router

Token-only authentication pattern.
All authentication is handled by Firebase on the client side.
The backend verifies tokens on each request - no server-side sessions.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database.core import get_db
from database.models import User
from pydantic_models.schemas import UserResponse
from security.auth import get_current_user, verify_and_get_user

router = APIRouter(prefix="/auth", tags=["auth"])


class FirebaseTokenRequest(BaseModel):
    """Request model for Firebase authentication"""

    idToken: str


@router.post("/firebase/login")
async def firebase_login(
    token_request: FirebaseTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify Firebase ID token and ensure user exists in database.

    This endpoint:
    1. Verifies the Firebase ID token
    2. Gets or creates the user in the database (JIT provisioning)
    3. Returns user info

    No session is created - the client should include the Firebase ID token
    in the Authorization header for all subsequent requests.
    """
    user = await verify_and_get_user(db, token_request.idToken)

    return {
        "message": "Login successful",
        "email": user.email,
        "user_id": user.id,
        "firebase_uid": user.firebase_uid,
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_user),
):
    """
    Get current authenticated user info.

    Requires Authorization: Bearer <firebase_id_token> header.
    """
    return user


@router.post("/logout")
async def logout():
    """
    Logout endpoint for client-side cleanup acknowledgment.

    With token-only auth, logout is handled client-side by:
    1. Calling Firebase signOut()
    2. Clearing local state

    This endpoint exists for API completeness and logging purposes.
    """
    return {"message": "Logged out"}
