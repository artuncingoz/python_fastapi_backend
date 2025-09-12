from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from redis import Redis
from datetime import datetime, timezone

from app.schemas.user import UserCreate, UserOut, TokenOut
from app.db import models
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import create_access_token, decode_token
from app.auth.dependencies import bearer_scheme, get_db, get_current_user
from app.deps import get_redis

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserOut, status_code=201)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    
    exists = db.query(models.User).filter(models.User.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = models.User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=models.UserRole.AGENT.value,  # default role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=TokenOut)
def login(payload: UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token, jti, ttl = create_access_token(sub=str(user.id), ver=user.token_version)
    return TokenOut(access_token=token)

@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    r: Redis = Depends(get_redis),
):
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        raise HTTPException(status_code=400, detail="Malformed token")

    now = int(datetime.now(timezone.utc).timestamp())
    ttl = max(exp - now, 0)
    if ttl > 0:
        r.setex(f"revoked:{jti}", ttl, "1")

    return {"detail": "Logged out"}

@router.get("/me", response_model=UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user
