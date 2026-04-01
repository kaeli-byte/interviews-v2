"""Auth router."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException

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
    """Logout acknowledgement for client-managed Supabase auth."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    return {"message": "Sign out from the frontend Supabase session to complete logout"}


@router.get("/me", response_model=auth_schemas.UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info."""
    return {"id": current_user["id"], "email": current_user["email"]}
