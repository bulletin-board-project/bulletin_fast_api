"""
User Pydantic schemas for request/response validation
"""
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_serializer, field_validator

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema"""
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(
        None, pattern=r'^(\+959|9|09|0)?[0-9]{0,10}$|^$')
    dob: Optional[date] = None
    address: Optional[str] = Field(None, max_length=255)
    profile_path: Optional[str] = None
    role: int = Field(default=UserRole.USER.value)


class UserCreate(UserBase):
    """Schema for user creation"""
    password: str = Field(..., min_length=8, max_length=72)
    confirm_password: str

    @field_validator('confirm_password')
    @classmethod
    def validate_confirm_password(cls, v: str, info):
        """
        Validate that passwords match
        """
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str):
        """
        Validate password strength
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError(
                'Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """Schema for user update"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    dob: Optional[date] = None
    address: Optional[str] = Field(None, max_length=255)
    profile_path: Optional[str] = None
    role: Optional[int] = Field(None, ge=0, le=3)  # 0-3 for enum values
    lock_flg: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    lock_flg: bool
    lock_count: int
    last_lock_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None
    create_user_id: Optional[int] = None
    updated_user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    # Custom serializers for datetime fields
    @field_serializer('created_at', 'updated_at', 'last_login_at', 'last_lock_at', 'deleted_at')
    def serialize_datetime(self, dt: Optional[datetime], _info) -> Optional[str]:
        """Convert datetime to ISO format string"""
        if dt is None:
            return None
        return dt.isoformat()

    @field_serializer('dob')
    def serialize_date(self, d: Optional[date], _info) -> Optional[str]:
        """Convert date to string"""
        if d is None:
            return None
        return d.isoformat()

    class Config:
        """ config """
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserChangePassword(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str

    @field_validator('confirm_password')
    @classmethod
    def validate_confirm_password(cls, v: str, info):
        """
        Validate that passwords match
        """
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v

