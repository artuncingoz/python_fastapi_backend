# app/schemas/admin.py
from pydantic import BaseModel
from typing import List
from app.schemas.user import UserInfoOut
from app.schemas.note import NoteOut

class UserWithNotesOut(BaseModel):
    user: UserInfoOut
    notes: List[NoteOut]
