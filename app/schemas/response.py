"""Response schemas for consistent API responses"""
from typing import Any, Optional, Generic, TypeVar
from datetime import UTC, datetime
from pydantic import BaseModel, Field

T = TypeVar("T")


class StandardResponse(BaseModel):
    """Standard API response"""
    success: bool = Field(...,
                          description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    data: Optional[Any] = None
    error_code: Optional[str] = None


class PaginatedResponse(StandardResponse, Generic[T]):
    """Paginated response"""
    current_page: int
    per_page: int
    total: int
    total_pages: int
    data: list[T]


class ErrorResponse(BaseModel):
    """Error response for consistent error formatting"""
    success: bool = False
    message: str
    error_code: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    details: Optional[dict] = None
