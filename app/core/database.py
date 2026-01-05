"""
Docstring for app.core.database
"""
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.models.base import Base

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,     # Check connection before use
    pool_recycle=3600,      # Recycle connections every hour
    pool_size=10,           # Connection pool size
    max_overflow=20,        # Max overflow connections
    echo=settings.ENVIRONMENT == "development",  # SQL logging in dev
    echo_pool=settings.ENVIRONMENT == "development",  # Pool logging
    connect_args={
        "charset": "utf8mb4",
        "connect_timeout": 10,  # Connection timeout
    }
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Better for FastAPI
)


# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get database session.
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """Create all tables in the database"""
    try:

        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")

        # Show created tables
        tables = list(Base.metadata.tables.keys())
        print(f"📊 Tables created: {len(tables)}")
        for table in tables:
            print(f"  - {table}")

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise


def test_connection():
    """Test database connection"""

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                print("✅ Database connection successful!")
                return True
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Database connection failed: {e}")
        return False
