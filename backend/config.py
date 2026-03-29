"""Configuration management."""
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings."""

    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MODEL: str = os.getenv("MODEL", "gemini-3.1-flash-live-preview")

    # JWT
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/interview_app")

    # Uploads
    UPLOADS_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # CORS
    CORS_ORIGINS: list = ["*"]

    # Frontend (for redirects)
    FRONTEND_DEV_URL: str = "http://localhost:3000"
    FRONTEND_BUILD_PATH: str = "frontend/.next/server/app"

    # Demo mode
    MOCK_USER_ID: str = "demo_user"

    def __init__(self):
        try:
            self.UPLOADS_DIR.mkdir(exist_ok=True)
        except OSError:
            # Read-only filesystem (e.g., Vercel) - skip directory creation
            pass

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return os.getenv("ENV", "development") == "production"

    @property
    def frontend_dist_exists(self) -> bool:
        """Check if Next.js build exists."""
        return Path(self.FRONTEND_BUILD_PATH).exists()


settings = Settings()