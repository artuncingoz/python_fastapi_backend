# app/api/v1/routes_notes.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from redis import Redis
from rq import Queue
from app.worker_jobs import summarize_note_job



from app.schemas.note import NoteCreate, NoteOut, NoteStatus
from app.schemas.admin import UserWithNotesOut
from app.schemas.user import UserInfoOut
from app.db import models
from app.auth.dependencies import get_db, get_current_user, require_admin
from app.deps import get_redis
from app.config import settings

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteOut)
def create_note(
    payload: NoteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    r: Redis = Depends(get_redis),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    # Idempotency: reuse existing for same user+key
    if idempotency_key:
        existing = (
            db.query(models.Note)
            .filter(
                models.Note.user_id == current_user.id,
                models.Note.idempotency_key == idempotency_key,
            )
            .first()
        )
        if existing:
            return existing

    note = models.Note(
        user_id=current_user.id,
        raw_text=payload.raw_text,
        status=models.NoteStatus.queued.value,
        idempotency_key=idempotency_key,
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    # Enqueue background job
    q = Queue("notes_summarize", connection=r)       
    q.enqueue(summarize_note_job, note.id, job_timeout=600)
    return note


# ---------- LIST (current user only, regardless of role) ----------
@router.get("", response_model=List[NoteOut])
def list_my_notes(
    status: Optional[NoteStatus] = Query(default=None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = db.query(models.Note).filter(models.Note.user_id == current_user.id)
    if status is not None:
        q = q.filter(models.Note.status == status.value)
    return q.order_by(models.Note.id.desc()).limit(limit).offset(offset).all()


# ---------- ADMIN: grouped by user ----------
@router.get("/grouped-by-user", response_model=List[UserWithNotesOut])
def list_grouped_by_user_admin(
    status: Optional[NoteStatus] = Query(default=None, description="Optional status filter"),
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    # Load all users
    users = db.query(models.User).order_by(models.User.id.asc()).all()
    if not users:
        return []

    # Load notes (optionally filtered), then group in memory
    qn = db.query(models.Note)
    if status is not None:
        qn = qn.filter(models.Note.status == status.value)
    notes = qn.order_by(models.Note.id.desc()).all()

    from collections import defaultdict
    by_user: dict[int, list[models.Note]] = defaultdict(list)
    for n in notes:
        by_user[n.user_id].append(n)

    # Build response
    out: List[UserWithNotesOut] = []
    for u in users:
        uinfo = UserInfoOut.model_validate(u)
        u_notes = [NoteOut.model_validate(n) for n in by_user.get(u.id, [])]
        out.append(UserWithNotesOut(user=uinfo, notes=u_notes))
    return out


# ---------- ADMIN: all notes (flat list, optional) ----------
@router.get("/all", response_model=List[NoteOut])
def list_all_notes_admin(
    status: Optional[NoteStatus] = Query(default=None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: models.User = Depends(require_admin),
):
    q = db.query(models.Note)
    if status is not None:
        q = q.filter(models.Note.status == status.value)
    return q.order_by(models.Note.id.desc()).limit(limit).offset(offset).all()


# ---------- GET BY ID ----------
@router.get("/{note_id:int}", response_model=NoteOut)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    note = db.get(models.Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    # tenancy: AGENT can only access own
    if current_user.role != models.UserRole.ADMIN.value and note.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return note
