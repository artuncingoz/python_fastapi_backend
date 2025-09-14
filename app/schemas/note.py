from datetime import datetime
from enum import Enum
from pydantic import BaseModel, ConfigDict

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

    model_config = ConfigDict(from_attributes=True)
