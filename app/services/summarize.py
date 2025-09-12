from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential
from app.db import models

def simple_summarize(text: str) -> str:
    """Very small heuristic: first 60 words (or shorter)."""
    words = text.strip().split()
    if len(words) <= 60:
        return " ".join(words)
    return " ".join(words[:60]) + "…"

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def process_note(db: Session, note_id: int) -> None:
    note = db.get(models.Note, note_id)
    if not note:
        return
    # mark processing
    note.status = models.NoteStatus.processing.value
    db.commit()
    db.refresh(note)

    try:
        note.summary = simple_summarize(note.raw_text)
        note.status = models.NoteStatus.done.value
    except Exception:
        note.status = models.NoteStatus.failed.value
        raise
    finally:
        db.commit()
