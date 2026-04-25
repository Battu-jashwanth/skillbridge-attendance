import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src import models, schemas, auth

router = APIRouter(prefix="/batches", tags=["batches"])


@router.post("", response_model=schemas.BatchResponse, status_code=201)
def create_batch(
    payload: schemas.BatchCreate,
    current_user: models.User = Depends(auth.require_roles("trainer", "institution")),
    db: Session = Depends(get_db),
):
    inst = db.query(models.Institution).filter(models.Institution.id == payload.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    batch = models.Batch(name=payload.name, institution_id=payload.institution_id)
    db.add(batch)
    db.flush()

    bt = models.BatchTrainer(batch_id=batch.id, trainer_id=current_user.id)
    db.add(bt)
    db.commit()
    db.refresh(batch)
    return batch


@router.post("/{batch_id}/invite", response_model=schemas.InviteResponse)
def create_invite(
    batch_id: int,
    current_user: models.User = Depends(auth.require_roles("trainer")),
    db: Session = Depends(get_db),
):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    is_trainer = db.query(models.BatchTrainer).filter(
        models.BatchTrainer.batch_id == batch_id,
        models.BatchTrainer.trainer_id == current_user.id,
    ).first()
    if not is_trainer:
        raise HTTPException(status_code=403, detail="You are not a trainer for this batch")

    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    invite = models.BatchInvite(
        batch_id=batch_id,
        token=token,
        created_by=current_user.id,
        expires_at=expires,
        used=False,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return {"token": invite.token, "expires_at": invite.expires_at, "batch_id": invite.batch_id}


@router.post("/join")
def join_batch(
    payload: schemas.JoinBatchRequest,
    current_user: models.User = Depends(auth.require_roles("student")),
    db: Session = Depends(get_db),
):
    invite = db.query(models.BatchInvite).filter(models.BatchInvite.token == payload.token).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite token not found")
    if invite.used:
        raise HTTPException(status_code=422, detail="Invite token already used")
    if invite.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Invite token has expired")

    existing = db.query(models.BatchStudent).filter(
        models.BatchStudent.batch_id == invite.batch_id,
        models.BatchStudent.student_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=422, detail="Already enrolled in this batch")

    bs = models.BatchStudent(batch_id=invite.batch_id, student_id=current_user.id)
    invite.used = True
    db.add(bs)
    db.commit()
    return {"message": "Successfully joined batch", "batch_id": invite.batch_id}


@router.get("/{batch_id}/summary", response_model=schemas.BatchSummaryResponse)
def batch_summary(
    batch_id: int,
    current_user: models.User = Depends(auth.require_roles("institution")),
    db: Session = Depends(get_db),
):
    batch = db.query(models.Batch).filter(models.Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    total_students = db.query(models.BatchStudent).filter(models.BatchStudent.batch_id == batch_id).count()
    sessions = db.query(models.Session).filter(models.Session.batch_id == batch_id).all()
    session_ids = [s.id for s in sessions]

    records = db.query(models.Attendance).filter(models.Attendance.session_id.in_(session_ids)).all()
    present = sum(1 for r in records if r.status.value == "present")
    absent = sum(1 for r in records if r.status.value == "absent")
    late = sum(1 for r in records if r.status.value == "late")

    return schemas.BatchSummaryResponse(
        batch_id=batch_id,
        batch_name=batch.name,
        total_students=total_students,
        total_sessions=len(sessions),
        total_attendance_marked=len(records),
        present_count=present,
        absent_count=absent,
        late_count=late,
    )
