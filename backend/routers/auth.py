from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.core import get_db
from database.models import User
from security.redis import get_redis
from services.auth_service import authenticate_user, create_user
from pydantic_models.schemas import (
    UserLogin,
    UserCreate,
    UserResponse,
    Token,
    SocialLoginRequest,
)
from services.auth_service import (
    authenticate_user,
    create_user,
    get_or_create_user_via_social,
    verify_google_token,
    verify_apple_token,
    verify_facebook_token,
)
from config import settings
from security.session_manager import SessionManager


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    return await create_user(db, user_in)


@router.post("/login")
async def login_cookie(
    response: Response,
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
    redis_conn=Depends(get_redis),
):
    """
    Login endpoint that sets a secure HttpOnly cookie (Redis Session).
    """
    user = await authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create Redis Session
    session_manager = SessionManager(redis_conn)
    session_id = await session_manager.create_session(user.id, user.email)

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=settings.SECURITY_FORCE_HTTPS,
        samesite="lax",
        max_age=86400 * 7,
    )

    return {"message": "Login successful", "email": user.email}


@router.post("/logout")
async def logout(response: Response, request: Request, redis_conn=Depends(get_redis)):
    session_id = request.cookies.get("session_id")
    if session_id:
        session_manager = SessionManager(redis_conn)
        await session_manager.delete_session(session_id)


    response.delete_cookie("session_id")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def check_auth_status(
    request: Request, db: AsyncSession = Depends(get_db), redis_conn=Depends(get_redis)
):
    """
    Check if the user is logged in via session cookie.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session_manager = SessionManager(redis_conn)
    session_data = await session_manager.get_session(session_id)
    
    if not session_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    user_id = session_data.get("user_id")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def process_social_login(
    response: Response,
    db: AsyncSession,
    redis_conn,
    provider: str,
    token: str,
):
    # Process based on provider
    try:
        user_info = {}
        if provider == "google":
            user_info = verify_google_token(token)
        elif provider == "apple":
            user_info = verify_apple_token(token)
        elif provider == "facebook":
            user_info = verify_facebook_token(token)
        else:
             raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
             
        sub = user_info["sub"]
        email = user_info.get("email")
        
        user = await get_or_create_user_via_social(db, provider, sub, email)
    except Exception as e:
        # Re-raise HTTP Exceptions, wrap others
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=400, detail=str(e))

    # Create Redis Session
    session_manager = SessionManager(redis_conn)
    session_id = await session_manager.create_session(user.id, user.email)

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=settings.SECURITY_FORCE_HTTPS,
        samesite="lax",
        max_age=86400 * 7,
    )

    return {"message": f"Login with {provider} successful", "email": user.email}


@router.post("/google")
async def login_google(
    response: Response,
    login_request: SocialLoginRequest,
    db: AsyncSession = Depends(get_db),
    redis_conn=Depends(get_redis),
):
    return await process_social_login(
        response, db, redis_conn, "google", login_request.token
    )


@router.post("/apple")
async def login_apple(
    response: Response,
    login_request: SocialLoginRequest,
    db: AsyncSession = Depends(get_db),
    redis_conn=Depends(get_redis),
):
    return await process_social_login(
        response, db, redis_conn, "apple", login_request.token
    )


@router.post("/facebook")
async def login_facebook(
    response: Response,
    login_request: SocialLoginRequest,
    db: AsyncSession = Depends(get_db),
    redis_conn=Depends(get_redis),
):
    return await process_social_login(
        response, db, redis_conn, "facebook", login_request.token
    )
