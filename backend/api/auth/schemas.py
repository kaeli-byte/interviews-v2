"""Auth Pydantic schemas."""
from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    user: dict
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str