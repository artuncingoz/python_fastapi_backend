import os
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db import models
from app.auth.hashing import hash_password
from app.services.summarize import simple_summarize

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin123!")
AGENT_COUNT = int(os.getenv("AGENT_COUNT", "5"))

def ensure_user(db: Session, email: str, password: str, role: str) -> models.User:
    u = db.query(models.User).filter(models.User.email == email).first()
    if u:
        return u
    u = models.User(email=email, password_hash=hash_password(password), role=role)
    db.add(u); db.commit(); db.refresh(u)
    return u

def ensure_note(db: Session, user_id: int, raw_text: str, status: str = models.NoteStatus.done.value):
    summary = simple_summarize(raw_text) if status == models.NoteStatus.done.value else None
    n = models.Note(user_id=user_id, raw_text=raw_text, summary=summary, status=status)
    db.add(n)

def run():
    db = SessionLocal()
    try:
        # if anything exists, skip (idempotent seed)
        if db.query(models.User).count() > 0:
            print("Seed: users already exist, skipping.")
            return

        admin = ensure_user(db, ADMIN_EMAIL, ADMIN_PASSWORD, models.UserRole.ADMIN.value)

        agents = []
        for i in range(1, AGENT_COUNT + 1):
            email = f"agent{i}@example.com"
            agents.append(ensure_user(db, email, f"Agent{i}123!", models.UserRole.AGENT.value))

        # add a couple notes for admin (done)
        ensure_note(db, admin.id, "Admin note one " * 10, status=models.NoteStatus.done.value)
        ensure_note(db, admin.id, "Admin note two " * 20, status=models.NoteStatus.done.value)

        # add some notes for each agent (mix of statuses)
        for idx, a in enumerate(agents, start=1):
            ensure_note(db, a.id, f"Agent {idx} done note " * 10, status=models.NoteStatus.done.value)
            ensure_note(db, a.id, f"Agent {idx} queued note " * 15, status=models.NoteStatus.queued.value)

        db.commit()
        print(f"Seed: created admin {ADMIN_EMAIL} + {len(agents)} agents with sample notes.")
    finally:
        db.close()

if __name__ == "__main__":
    run()
