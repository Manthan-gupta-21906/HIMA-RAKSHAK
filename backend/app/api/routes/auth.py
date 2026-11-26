"""Authentication API routes — login and current-user inspection."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import get_settings
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


def seed_demo_users(db: Session) -> int:
    """Explicitly seed or sync demo users only in development/test environments."""
    if get_settings().app_env.lower() not in {"development", "test"}:
        return 0
    demo_users = [
        ("Admin", "Admin123", "Demo Admin", UserRole.ADMIN),
        ("operator", "operator1234", "Demo Operator", UserRole.DISTRICT_OPERATOR),
        ("viewer", "viewer1234", "Demo Viewer", UserRole.VIEWER),
    ]
    changed = 0
    # Rename legacy lowercase 'admin' demo fixture if present
    legacy_admin = (
        db.query(UserModel)
        .filter(UserModel.username == "admin", UserModel.is_demo_fixture.is_(True))
        .first()
    )
    if legacy_admin is not None:
        existing_upper = db.query(UserModel).filter(UserModel.username == "Admin").first()
        if existing_upper is None:
            legacy_admin.username = "Admin"
            legacy_admin.hashed_password = hash_password("Admin123")
            changed += 1
        else:
            db.delete(legacy_admin)
        db.flush()

    for username, password, full_name, role in demo_users:
        existing_user = db.query(UserModel).filter(UserModel.username == username).first()
        if existing_user is None:
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
            changed += 1
        elif existing_user.is_demo_fixture and not verify_password(
            password, existing_user.hashed_password
        ):
            existing_user.hashed_password = hash_password(password)
            changed += 1
    if changed > 0:
        db.commit()
    return changed


def _seed_dev_demo_users_on_startup() -> None:
    db = _get_db()
    try:
        seed_demo_users(db)
    finally:
        db.close()


_seed_dev_demo_users_on_startup()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    """Authenticate with username and password, returning a JWT."""
    db = _get_db()
    try:
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
