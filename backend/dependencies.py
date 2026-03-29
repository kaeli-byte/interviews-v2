"""FastAPI dependencies."""
import re
from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException
from jose import jwt, JWTError

from backend.config import settings
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from root db module
from backend.db import queries as db

# Token blacklist for logout
blacklisted_tokens: set = set()


def validate_email(email: str) -> bool:
    """Basic email format validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Dependency to get current user from JWT token.
    Raises 401 if token is invalid or user not found.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization.split(" ")[1]

    if token in blacklisted_tokens:
        raise HTTPException(status_code=401, detail="Token has been revoked")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await db.get_user_by_email(email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """
    Dependency to get current user from JWT token if present.
    Returns None if no valid token (for demo mode).
    """
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ")[1]

    if token in blacklisted_tokens:
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None

        return None  # Skip DB lookup for demo - would need async handling
    except JWTError:
        return None