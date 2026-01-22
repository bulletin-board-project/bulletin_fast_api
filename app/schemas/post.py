"""Post Pydantic schemas"""
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator, validator

from app.models.post import Status


class PostBase(BaseModel):
    """Base Post Schema"""
    title: str = Field(..., min_length=2, max_length=255)
    description: str = Field(..., min_length=2, max_length=255)
    status: int = Field(default=Status.ACTIVE.value)


class PostCreate(PostBase):
    """Schema for post create"""


class PostUpdate(BaseModel):
    """Schema for Post Update"""
    title: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, min_length=2, max_length=255)
    status: Optional[int] = Field(None, ge=0, le=1)


class PostResponse(PostBase):
    """Schema for Post Response"""
    id: int
    create_user_id: Optional[int] = None
    updated_user_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

# Custom serializers for datetime fields
    @field_serializer('created_at', 'updated_at', 'deleted_at')
    def serialize_datetime(self, dt: Optional[datetime], _info) -> Optional[str]:
        """Convert datetime to ISO format string"""
        if dt is None:
            return None
        return dt.isoformat()

    model_config = ConfigDict(from_attributes=True)


class PostExportRequest(BaseModel):
    """ Post Export Request """
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(10, ge=1, le=10000,
                          description="Items per page (max 10000 for export)")
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[int] = None  # Changed from post_status to match your code
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"
    post_ids: Optional[List[int]] = Field(
        [], description="List of post IDs to export")

    @field_validator('post_ids')
    @classmethod
    def validate_post_ids(cls, v):
        """ Validate post_ids """
        if v is not None and len(v) == 0:
            return None
        return v

    class Config:
        """ config """
        from_attributes = True
