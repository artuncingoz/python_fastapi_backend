from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.summarize import process_note

def summarize_note_job(note_id: int) -> None:
    db: Session = SessionLocal()
    try:
        process_note(db, note_id)
    finally:
        db.close()
