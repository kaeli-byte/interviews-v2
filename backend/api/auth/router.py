"""Auth router."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import JSONResponse

from backend.api.auth import schemas as auth_schemas
from backend.api.auth import service as auth_service
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=auth_schemas.AuthResponse)
async def signup(data: auth_schemas.SignupRequest):
    """Register a new user."""
    try:
        result = await auth_service.signup(data.email, data.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=auth_schemas.AuthResponse)
async def login(data: auth_schemas.LoginRequest):
    """Authenticate a user."""
    try:
        result = await auth_service.login(data.email, data.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Logout a user (blacklist token)."""
    from backend.dependencies import blacklisted_tokens

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    token = authorization.split(" ")[1]
    blacklisted_tokens.add(token)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=auth_schemas.UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info."""
    return {"id": current_user["id"], "email": current_user["email"]}