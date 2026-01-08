"""Global exception handlers"""
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.response import StandardResponse


def add_exception_handlers(app: FastAPI):
    """Add global exception handlers for consistent error responses"""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions"""
        detail = exc.detail
        if isinstance(detail, dict):
            # Already formatted as consistent response
            return JSONResponse(
                status_code=exc.status_code,
                content=detail
            )
        else:
            # Convert to consistent response
            response = StandardResponse(
                success=False,
                message=str(detail),
                error_code=f"HTTP_{exc.status_code}",
                details={
                    "status_code": exc.status_code,
                    "path": request.url.path
                }
            )
            return JSONResponse(
                status_code=exc.status_code,
                content=jsonable_encoder(response)
            )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors"""
        print(f"request: {request.url.path} - exception: {exc}")
        response = StandardResponse(
            success=False,
            message="Validation error",
            error_code="VALIDATION_ERROR",
            details={"errors": exc.errors()}
        )
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder(response)
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions"""
        print(f"request: {request.url.path} - exception: {exc}")
        response = StandardResponse(
            success=False,
            message="Internal server error",
            error_code="INTERNAL_SERVER_ERROR",
            details={"error": str(exc)}
        )
        return JSONResponse(
            status_code=500,
            content=jsonable_encoder(response)
        )
