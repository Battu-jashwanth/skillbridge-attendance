from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src import models, schemas, auth

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=schemas.SessionResponse, status_code=201)
def create_session(
    payload: schemas.SessionCreate,
    current_user: models.User = Depends(auth.require_roles("trainer")),
    db: Session = Depends(get_db),
):
    batch = db.query(models.Batch).filter(models.Batch.id == payload.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    is_trainer = db.query(models.BatchTrainer).filter(
        models.BatchTrainer.batch_id == payload.batch_id,
        models.BatchTrainer.trainer_id == current_user.id,
    ).first()
    if not is_trainer:
        raise HTTPException(status_code=403, detail="You are not a trainer for this batch")

    session = models.Session(
        batch_id=payload.batch_id,
        trainer_id=current_user.id,
        title=payload.title,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}/attendance", response_model=schemas.SessionAttendanceResponse)
def get_session_attendance(
    session_id: int,
    current_user: models.User = Depends(auth.require_roles("trainer")),
    db: Session = Depends(get_db),
):
    session = db.query(models.Session).filter(models.Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    records = (
        db.query(models.Attendance, models.User)
        .join(models.User, models.Attendance.student_id == models.User.id)
        .filter(models.Attendance.session_id == session_id)
        .all()
    )

    attendance_list = [
        schemas.AttendanceWithStudent(
            student_id=user.id,
            student_name=user.name,
            student_email=user.email,
            status=att.status,
            marked_at=att.marked_at,
        )
        for att, user in records
    ]

    return schemas.SessionAttendanceResponse(
        session_id=session_id,
        session_title=session.title,
        total=len(attendance_list),
        records=attendance_list,
    )
