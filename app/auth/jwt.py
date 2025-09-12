from datetime import datetime, timedelta, timezone
from jose import jwt
import uuid
from app.config import settings

def create_access_token(*, sub: str, ver: int) -> tuple[str, str, int]:
    """
    Create a signed JWT access token.
    Returns: (token, jti, ttl_seconds)
    - sub: user id as string
    - ver: user's current token_version from DB
    """
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.access_token_expire_minutes)
    jti = uuid.uuid4().hex

    payload = {
        "iss": settings.token_iss,
        "aud": settings.token_aud,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "sub": sub,
        "ver": ver,
        "jti": jti,
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)
    ttl = int((exp - now).total_seconds())
    return token, jti, ttl

def decode_token(token: str) -> dict:
    """Decode + validate a JWT (issuer, audience, exp, signature)."""
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_alg],
        audience=settings.token_aud,
        issuer=settings.token_iss,
        options={"verify_aud": True, "verify_signature": True, "verify_iss": True},
    )
