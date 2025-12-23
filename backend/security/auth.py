"""
Authentication Module

Handles Firebase token verification and user provisioning.
Uses firebase_uid as the primary lookup key for users.
"""
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from firebase_admin import auth as firebase_auth
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.firebase import verify_firebase_token
from database.core import get_db
from database.models import User

# Defined for Swagger UI to show the "Authorize" button
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/firebase/login", auto_error=False)


async def get_token_from_header(request: Request, token: Optional[str] = Depends(oauth2_scheme)) -> str:
    """Extract Bearer token from Authorization header."""
    if token:
        return token

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    token: str = Depends(get_token_from_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency to get current authenticated user.

    Uses firebase_uid as the primary lookup key.
    Creates new user if not found (JIT provisioning).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        decoded_token = verify_firebase_token(token)
        firebase_uid = decoded_token.get("uid")
        email = decoded_token.get("email")

        if not firebase_uid:
            raise credentials_exception

        # Look up user by firebase_uid
        stmt = select(User).where(User.firebase_uid == firebase_uid)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            return user

        # Create new user (JIT Provisioning)
        new_user = User(
            email=email,
            firebase_uid=firebase_uid,
        )
        db.add(new_user)
        try:
            await db.commit()
            await db.refresh(new_user)
            return new_user
        except IntegrityError:
            await db.rollback()
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                return user
            raise credentials_exception from None

    except Exception:
        raise credentials_exception from None


async def verify_and_get_user(db: AsyncSession, id_token: str) -> User:
    """
    Verify Firebase ID token and get or create user in database.

    This is used by the /auth/firebase/login endpoint to verify
    tokens sent in the request body (not Authorization header).

    Args:
        db: Database session
        id_token: Firebase ID token from client

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: If token is invalid or user creation fails
    """
    try:
        decoded_token = verify_firebase_token(id_token)
        firebase_uid = decoded_token["uid"]
        email = decoded_token.get("email")

        if not email:
            raise HTTPException(status_code=400, detail="Email not found in Firebase token")

        # Look up user by firebase_uid
        stmt = select(User).where(User.firebase_uid == firebase_uid)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            return user

        # Create new user
        new_user = User(
            email=email,
            firebase_uid=firebase_uid,
        )
        db.add(new_user)

        try:
            await db.commit()
            await db.refresh(new_user)
            return new_user
        except IntegrityError:
            await db.rollback()
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                return user
            raise HTTPException(status_code=400, detail="Failed to create user") from None

    except firebase_auth.InvalidIdTokenError as err:
        raise HTTPException(status_code=401, detail="Invalid Firebase ID token") from err
    except firebase_auth.ExpiredIdTokenError as err:
        raise HTTPException(status_code=401, detail="Firebase ID token has expired") from err
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}") from e


async def get_user_by_firebase_uid(db: AsyncSession, firebase_uid: str) -> Optional[User]:
    """Get user by Firebase UID from database."""
    stmt = select(User).where(User.firebase_uid == firebase_uid)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
