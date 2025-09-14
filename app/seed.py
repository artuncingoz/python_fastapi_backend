# app/seed.py
import os
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db import models
from app.auth.hashing import hash_password

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")

def ensure_admin(db: Session, email: str, password: str) -> models.User:
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        # If it exists but is not ADMIN, upgrade its role
        if user.role != models.UserRole.ADMIN.value:
            user.role = models.UserRole.ADMIN.value
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    user = models.User(
        email=email,
        password_hash=hash_password(password),
        role=models.UserRole.ADMIN.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def run():
    db: Session = SessionLocal()
    try:
        admin = ensure_admin(db, ADMIN_EMAIL, ADMIN_PASSWORD)
        print(f"Seed: ensured admin {admin.email}.")
    finally:
        db.close()

if __name__ == "__main__":
    run()
