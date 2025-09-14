# app/worker_jobs.py
from sqlalchemy.orm import Session
from tenacity import retry, wait_exponential, stop_after_attempt

from app.db.session import SessionLocal
from app.db import models
from app.services.summarize import summarize_text  # <- use the new API


@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), reraise=True)
def _summarize_with_retry(text: str) -> str:
    return summarize_text(text)


def summarize_note_job(note_id: int) -> None:
    """Background job: summarize a note and store result. Idempotent + retries."""
    db: Session = SessionLocal()
    try:
        note = db.get(models.Note, note_id)
        if not note:
            return

        # Idempotency: if already summarized, no-op
        if note.status == "done" and note.summary:
            return

        # Mark processing
        note.status = "processing"
        db.commit()

        try:
            summary = _summarize_with_retry(note.raw_text or "")
            note.summary = summary
            note.status = "done"
        except Exception:
            note.status = "failed"
            raise
        finally:
            db.commit()
    finally:
        db.close()
