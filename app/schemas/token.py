"""
Token schemas
"""
from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """Token response schema with refresh token"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Token refresh request schema"""
    refresh_token: str


class TokenData(BaseModel):
    """Decoded token data"""
    sub: str  # user_id
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[int] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    type: Optional[str] = None
