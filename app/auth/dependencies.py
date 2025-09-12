from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
bearer_scheme = HTTPBearer(auto_error=True)

from sqlalchemy.orm import Session
from redis import Redis

from app.db.session import SessionLocal
from app.db import models
from app.auth.jwt import decode_token
from app.deps import get_redis


def get_db():
    """Provide a SQLAlchemy session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _raise_401(detail: str = "Unauthorized"):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    r: Redis = Depends(get_redis),
) -> models.User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except Exception:
        _raise_401("Invalid or expired token")

    jti = payload.get("jti")
    sub = payload.get("sub")
    ver = payload.get("ver")
    if not jti or sub is None or ver is None:
        _raise_401("Malformed token")

    # Safely check blacklist
    try:
        if r.exists(f"revoked:{jti}"):
            _raise_401("Token revoked")
    except RedisError:
        # If Redis is briefly unavailable, treat it as not revoked
        pass

    user = db.get(models.User, int(sub))
    if not user:
        _raise_401("User not found")

    if user.token_version != int(ver):
        _raise_401("Token outdated")

    return user

def require_admin(user: models.User = Depends(get_current_user)) -> models.User:
    if user.role != models.UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin required")
    return user
