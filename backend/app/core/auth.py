"""
PropelAuth integration — verify JWT tokens and get current user.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from propelauth_fastapi import init_auth, TokenVerificationMetadata
from app.core.config import get_settings

settings = get_settings()

# Initialize PropelAuth
_auth = init_auth(
    auth_url=settings.PROPELAUTH_AUTH_URL,
    api_key=settings.PROPELAUTH_API_KEY,
)

http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> dict:
    """Verify PropelAuth JWT and return user dict."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )
    try:
        user = _auth.validate_access_token_and_get_user(
            f"Bearer {credentials.credentials}"
        )
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> dict | None:
    """Like get_current_user but returns None instead of raising for unauthenticated."""
    if not credentials:
        return None
    try:
        return _auth.validate_access_token_and_get_user(
            f"Bearer {credentials.credentials}"
        )
    except Exception:
        return None


async def get_or_create_db_user(propelauth_user: dict, db) -> "User":
    """Get or create DB User record from PropelAuth user dict."""
    from app.models import User
    from sqlalchemy import select

    result = await db.execute(
        select(User).where(User.propelauth_user_id == propelauth_user.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            propelauth_user_id=propelauth_user.user_id,
            email=propelauth_user.email,
            plan="free",
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user
