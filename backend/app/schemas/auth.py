"""Pydantic schemas for authentication and authorization."""

from pydantic import BaseModel, Field

from app.models.user import UserRole


class LoginRequest(BaseModel):
    """Credentials submitted for authentication."""

    username: str = Field(..., min_length=3, max_length=80)
    password: str = Field(..., min_length=4, max_length=128)


class TokenResponse(BaseModel):
    """JWT token returned on successful login."""

    access_token: str
    token_type: str = "bearer"


class CurrentUser(BaseModel):
    """Authenticated user identity extracted from a valid JWT."""

    username: str
    role: UserRole
