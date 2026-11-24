"""Authentication API routes — login and current-user inspection."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.base import Base
from app.db.session import create_db_engine, get_session_factory
from app.models.user import UserModel, UserRole
from app.schemas.auth import CurrentUser, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_engine = create_db_engine()
Base.metadata.create_all(bind=_engine)
_session_factory = get_session_factory(_engine)


def _get_db() -> Session:
    """Get a DB session for auth routes."""
    return _session_factory()


def _ensure_demo_users(db: Session) -> None:
    """Idempotently seed demo users (admin, operator, viewer) if none exist."""
    existing = db.query(UserModel).count()
    if existing > 0:
        return
    demo_users = [
        ("admin", "admin1234", "Demo Admin", UserRole.ADMIN),
        ("operator", "operator1234", "Demo Operator", UserRole.DISTRICT_OPERATOR),
        ("viewer", "viewer1234", "Demo Viewer", UserRole.VIEWER),
    ]
    for username, password, full_name, role in demo_users:
        db.add(
            UserModel(
                user_id=str(uuid4()),
                username=username,
                hashed_password=hash_password(password),
                full_name=full_name,
                role=role,
                is_demo_fixture=True,
            )
        )
    db.commit()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    """Authenticate with username and password, returning a JWT."""
    db = _get_db()
    try:
        _ensure_demo_users(db)
        user = db.query(UserModel).filter(UserModel.username == payload.username).first()
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled.",
            )
        token = create_access_token(subject=user.username, role=user.role)
        return TokenResponse(access_token=token)
    finally:
        db.close()


@router.get("/me", response_model=CurrentUser)
def get_me(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Return the authenticated user's identity and role."""
    return user
