"""
Docstring for app.core.config
"""
import json
import sys
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """
    Docstring for Settings
    """
    # Project
    PROJECT_NAME: str = "FastAPI Project"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_HOUR: int = 1

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173", "http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """
        Docstring for assemble_cors_origins
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            return json.loads(v)
        elif isinstance(v, list):
            return v
        else:
            raise ValueError(f"Invalid CORS origins format: {v}")

    # MySQL Database
    MYSQL_HOST: str
    MYSQL_PORT: str = "3306"
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str

    @property
    def DATABASE_URL(self) -> str:  # pylint: disable=invalid-name
        """Build MySQL connection URL"""
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"  # pylint: disable=line-too-long

    # Documentation
    DOCS: bool = True

    # Security validations
    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """
        validate_secret_key
        """
        if not v or v.strip() == "":
            raise ValueError("SECRET_KEY cannot be empty")

        # Warn about example keys
        example_keys = [
            "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
            "CHANGE_ME",
            "your_secret_key"
        ]

        for example in example_keys:
            if example in v:
                print("⚠️  WARNING: Using example SECRET_KEY - change in production!")
                break

        return v

    class Config:
        """
        Docstring for Config
        """
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def init_settings() -> Settings:
    """Initialize and validate settings"""
    try:
        _settings = Settings()

        print(f"✅ Configuration loaded: {_settings.PROJECT_NAME}")
        print(f"🌍 Environment: {_settings.ENVIRONMENT}")

        # Hide password in logs
        safe_url = _settings.DATABASE_URL.replace(
            f":{_settings.MYSQL_PASSWORD}@",
            ":******@"
        )
        print(f"🔗 Database: {safe_url}")

        return _settings

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Configuration error: {e}")
        print("\n💡 Please check your .env file. Required variables:")
        sys.exit(1)


# Initialize settings
settings = init_settings()
