""" Main File """
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db, create_tables, test_connection
from app.core.config import settings
from app import models  # pylint: disable=unused-import

# Import routes
from app.routes import auth


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

# Include routers
app.include_router(auth.router)
# app.include_router(users.router)


@app.get("/")
def read_root():
    """
    Welcome Route
    """
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with database test"""
    try:
        # Test database query
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "project": settings.PROJECT_NAME,
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:  # pylint: disable=broad-exception-caught
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


print(__name__)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )
