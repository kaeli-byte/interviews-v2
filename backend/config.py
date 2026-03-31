"""Configuration management."""
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables.
# Prefer backend/.env for local FastAPI runtime, then allow root-level env overrides.
ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_ENV_PATH = ROOT_DIR / "backend" / ".env"
ROOT_ENV_PATH = ROOT_DIR / ".env.local"

load_dotenv(BACKEND_ENV_PATH, override=False)
load_dotenv(ROOT_ENV_PATH, override=False)


def _parse_cors_origins(raw_origins: Optional[str]) -> list[str]:
    """Parse a comma-separated CORS origin list from the environment."""
    if not raw_origins:
        return ["*"]
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return origins or ["*"]


class Settings:
    """Application settings."""

    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MODEL_LIVE: str = os.getenv("MODEL_LIVE", os.getenv("MODEL", "gemini-3.1-flash-live-preview"))
    MODEL_EXTRACT: str = os.getenv("MODEL_EXTRACT", "gemini-2.5-flash")

    @property
    def MODEL(self) -> str:
        """Backward-compatible alias for the live model."""
        return self.MODEL_LIVE

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", os.getenv("NEXT_PUBLIC_SUPABASE_URL", ""))
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", ""))
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    SUPABASE_STORAGE_BUCKET: str = os.getenv("SUPABASE_STORAGE_BUCKET", "interview-assets")

    # JWT
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database
    DATABASE_URL: str = os.getenv(
        "DIRECT_URL",
        os.getenv("SUPABASE_DB_URL", os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/interview_app")),
    )

    # Uploads
    UPLOADS_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # CORS
    CORS_ORIGINS: list[str] = _parse_cors_origins(os.getenv("CORS_ALLOWED_ORIGINS"))

    # Frontend (for redirects)
    FRONTEND_DEV_URL: str = os.getenv("FRONTEND_DEV_URL", os.getenv("NEXT_PUBLIC_SITE_URL", ""))
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

    @property
    def has_local_supabase_jwt_verification(self) -> bool:
        """Check whether Supabase JWTs can be verified locally."""
        return bool(self.SUPABASE_JWT_SECRET)

    @property
    def uses_placeholder_app_jwt_secret(self) -> bool:
        """Check whether the app JWT secret is still using the default placeholder."""
        return self.SECRET_KEY == "your-secret-key-here"


settings = Settings()
