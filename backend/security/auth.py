from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic_models.schemas import TokenData
from config import settings
from security.redis import get_redis
import redis.asyncio as redis
import secrets
import hashlib
import base64

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def generate_random_string(length=48):
    return secrets.token_urlsafe(length)


def create_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def verify_pkce(verifier: str, challenge: str) -> bool:
    if not verifier or not challenge:
        return False
    # Only S256 supported
    expected = create_code_challenge(verifier)
    return expected == challenge


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # Add JTI (Unique Identifier) for blacklist capability
    if "jti" not in to_encode:
        to_encode["jti"] = secrets.token_hex(16)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_token_from_header_or_cookie(
    request: Request, token: Optional[str] = Depends(oauth2_scheme)
) -> str:
    if token:
        return token

    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        if cookie_token.startswith("Bearer "):
            return cookie_token.split(" ")[1]
        return cookie_token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    token: str = Depends(get_token_from_header_or_cookie),
    redis_conn: redis.Redis = Depends(get_redis),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")

        if user_id is None:
            raise credentials_exception

        # Check Blacklist
        if jti:
            is_revoked = await redis_conn.get(f"blacklist:{jti}")
            if is_revoked:
                raise credentials_exception

        token_data = TokenData(
            user_id=str(user_id), sub=str(user_id), scope=payload.get("scope")
        )
    except JWTError:
        raise credentials_exception

    return token_data
