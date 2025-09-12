# app/api/v1/routes_users.py
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.user import UserInfoOut
from app.db import models
from app.auth.dependencies import get_db, require_admin

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=List[UserInfoOut])
def list_users(
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    return db.query(models.User).order_by(models.User.id.asc()).all()
