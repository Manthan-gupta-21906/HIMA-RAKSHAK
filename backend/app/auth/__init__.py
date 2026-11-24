"""FastAPI dependencies for authentication and role-based authorization."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.core.security import decode_access_token
from app.models.user import UserRole
from app.schemas.auth import CurrentUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """Extract and validate the current user from a Bearer token."""
    try:
        payload = decode_access_token(token)
        username: str | None = payload.get("sub")
        role: str | None = payload.get("role")
        if username is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims.",
            )
        return CurrentUser(username=username, role=UserRole(role))
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        ) from exc


class RoleChecker:
    """Dependency that enforces a minimum set of allowed roles."""

    def __init__(self, allowed_roles: list[UserRole]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(self, user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role}' is not authorized for this resource.",
            )
        return user


require_admin = RoleChecker([UserRole.ADMIN])
require_operator = RoleChecker([UserRole.ADMIN, UserRole.DISTRICT_OPERATOR])
require_any_authenticated = RoleChecker(
    [UserRole.ADMIN, UserRole.DISTRICT_OPERATOR, UserRole.VIEWER]
)
