"""Authentication utilities and service."""
import re
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import jwt

from backend.config import settings
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# In-memory user storage (for MVP)
users_db: dict = {}


async def get_user_by_email(email: str) -> dict:
    """Get user by email from in-memory storage."""
    return users_db.get(email)


async def create_user(email: str, password_hash: str) -> dict:
    """Create a new user in memory."""
    import uuid
    user_id = uuid.uuid4().hex
    user = {
        "id": user_id,
        "email": email,
        "password_hash": password_hash
    }
    users_db[email] = user
    return user


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def validate_email(email: str) -> bool:
    """Basic email format validation."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


async def signup(email: str, password: str) -> dict:
    """Create a new user account."""
    if not validate_email(email):
        raise ValueError("Invalid email format")

    # Check if user exists
    existing = await get_user_by_email(email)
    if existing:
        raise ValueError("Email already registered")

    password_hash = hash_password(password)
    user = await create_user(email, password_hash)

    token = create_access_token({"sub": email})
    return {
        "user": {"id": user["id"], "email": user["email"]},
        "access_token": token,
        "token_type": "bearer",
    }


async def login(email: str, password: str) -> dict:
    """Authenticate a user."""
    user = await get_user_by_email(email)
    if not user:
        raise ValueError("Invalid credentials")

    if not verify_password(password, user["password_hash"]):
        raise ValueError("Invalid credentials")

    token = create_access_token({"sub": email})
    return {
        "user": {"id": user["id"], "email": user["email"]},
        "access_token": token,
        "token_type": "bearer",
    }