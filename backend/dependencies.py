"""FastAPI dependencies."""
import json
from time import monotonic
from typing import Any, Dict, Optional

import httpx
from fastapi import Header, HTTPException
from jose import JWTError, jwt

from backend.config import settings
from backend.perf import timing_span


_AUTH_CACHE_TTL_SECONDS = 300.0
_auth_cache: dict[str, tuple[float, Dict[str, Any]]] = {}


def _cache_user(token: str, user: Dict[str, Any], now: float) -> Dict[str, Any]:
    _auth_cache[token] = (now, user)
    return user


def _verify_supabase_user_locally(token: str) -> Optional[Dict[str, Any]]:
    """Verify Supabase JWT locally when signing material is configured."""
    if not settings.SUPABASE_JWT_SECRET:
        return None

    issuer = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1" if settings.SUPABASE_URL else None

    # Decode header to check algorithm
    try:
        header_b64 = token.split('.')[0]
        # Add padding if needed
        padding = 4 - len(header_b64) % 4
        if padding != 4:
            header_b64 += '=' * padding
        import base64
        header_json = base64.urlsafe_b64decode(header_b64)
        header = json.loads(header_json)
        algorithm = header.get('alg', 'HS256')
    except Exception:
        algorithm = 'HS256'

    with timing_span("auth.local_jwt"):
        try:
            if algorithm == 'ES256':
                # ES256 requires a public key, not a symmetric secret
                # For Supabase, we need to fetch the JWKS or use the public key
                # Fall through to HTTP verification
                return None
            else:
                # HS256 - symmetric secret verification
                claims = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=["HS256"],
                    issuer=issuer,
                    options={"verify_aud": False},
                )
        except JWTError as exc:
            raise HTTPException(status_code=401, detail="Invalid Supabase token") from exc

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Supabase user not found")

    return {
        "id": user_id,
        "email": claims.get("email"),
        "app_metadata": claims.get("app_metadata"),
        "user_metadata": claims.get("user_metadata"),
        "role": claims.get("role"),
    }


async def _fetch_supabase_user(token: str) -> Dict[str, Any]:
    cached = _auth_cache.get(token)
    now = monotonic()
    if cached and now - cached[0] < _AUTH_CACHE_TTL_SECONDS:
        return cached[1]

    local_user = _verify_supabase_user_locally(token)
    if local_user is not None:
        return _cache_user(token, local_user, now)

    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise HTTPException(status_code=500, detail="Supabase auth is not configured")

    url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.SUPABASE_ANON_KEY,
    }

    with timing_span("auth.supabase.user"):
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Supabase token")

    user = response.json()
    if not user.get("id"):
        raise HTTPException(status_code=401, detail="Supabase user not found")
    return _cache_user(token, user, now)


async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Resolve the current Supabase-authenticated user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authorization header required")

    user = await _fetch_supabase_user(token)
    return {
        "id": user["id"],
        "email": user.get("email"),
        "raw_user": user,
        "token": token,
    }


async def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """Resolve the current user when a Supabase bearer token is present."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None

    try:
        user = await _fetch_supabase_user(token)
    except HTTPException:
        return None

    return {
        "id": user["id"],
        "email": user.get("email"),
        "raw_user": user,
        "token": token,
    }
