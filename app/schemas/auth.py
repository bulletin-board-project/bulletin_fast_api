""" Auth Scheme """

from pydantic import BaseModel, EmailStr, Field, field_validator


class ForgotPasswordRequest(BaseModel):
    """
    Docstring for ForgotPasswordRequest
    """
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """
    Docstring for ResetPasswordRequest
    """
    token: str
    password:  str = Field(..., min_length=8, max_length=100)
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
