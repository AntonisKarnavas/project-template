from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str
    expires_in: int
    scope: Optional[str] = None


class TokenData(BaseModel):
    user_id: Optional[str] = None
    sub: Optional[str] = None
    scope: Optional[str] = None


class UserBase(BaseModel):
    email: EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SocialLoginRequest(BaseModel):
    token: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str
