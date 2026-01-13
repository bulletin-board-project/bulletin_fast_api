"""Custom Business Exceptions"""

from typing import Any, Dict, Optional


class AppException(Exception):
    """Base application exception"""

    def __init__(
        self,
        message: str = "An error occurred",
        error_code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class BusinessException(AppException):
    """Business logic exception"""

    def __init__(
        self,
        message: str = "Business rule violation",
        error_code: str = "BUSINESS_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            details=details
        )


class ValidationException(AppException):
    """Validation exception"""

    def __init__(
        self,
        message: str = "Validation failed",
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=422,
            details=details
        )


class NotFoundException(AppException):
    """Resource not found exception"""

    def __init__(
        self,
        message: str = "Resource not found",
        error_code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=404,
            details=details
        )


class UnauthorizedException(AppException):
    """Unauthorized access exception"""

    def __init__(
        self,
        message: str = "Unauthorized access",
        error_code: str = "UNAUTHORIZED",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
            details=details
        )


class ForbiddenException(AppException):
    """Forbidden access exception"""

    def __init__(
        self,
        message: str = "Forbidden access",
        error_code: str = "FORBIDDEN",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=403,
            details=details
        )
