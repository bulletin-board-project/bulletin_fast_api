""" Main File """
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from starlette.middleware.cors import CORSMiddleware
from app.core.database import get_db, create_tables, test_connection
from app.core.config import settings
from app import models  # pylint: disable=unused-import

# Import routes
from app.core.exception_handlers import add_exception_handlers
from app.routes import auth, users
from app.schemas.response import StandardResponse


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan context manager"""
    # Startup
    print(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION}")

    # Test database connection
    if test_connection():
        if settings.ENVIRONMENT == "development":
            create_tables()
    else:
        print("❌ Cannot connect to database.")

    yield  # App runs here


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs" if settings.DOCS else None,
    lifespan=lifespan,
)

# Cors middleware
print("🔧 Setting up CORS middleware")
print(f"Allowed origins: {settings.BACKEND_CORS_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,  # .env
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Register exception handlers
add_exception_handlers(app)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)


@app.get("/")
def read_root():
    """
    Welcome Route
    """
    return StandardResponse(
        success=True,
        message=f"Welcome to {settings.PROJECT_NAME}",
        data={
            "project": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT
        }
    )


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with database test"""
    try:
        # Test database query
        db.execute(text("SELECT 1"))
        return StandardResponse(
            success=True,
            message="Service is healthy",
            data={
                "database": "connected",
                "project": settings.PROJECT_NAME,
                "environment": settings.ENVIRONMENT
            }
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        return StandardResponse(
            success=False,
            message="Service is unhealthy",
            data={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )


print(__name__)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )
