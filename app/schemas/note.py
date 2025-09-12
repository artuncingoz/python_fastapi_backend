from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class NoteStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    done = "done"
    failed = "failed"

class NoteCreate(BaseModel):
    raw_text: str

class NoteOut(BaseModel):
    id: int
    raw_text: str
    summary: str | None
    status: NoteStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
