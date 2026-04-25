from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src import models, schemas, auth

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/mark", response_model=schemas.AttendanceRecord, status_code=201)
def mark_attendance(
    payload: schemas.AttendanceMark,
    current_user: models.User = Depends(auth.require_roles("student")),
    db: Session = Depends(get_db),
):
    session = db.query(models.Session).filter(models.Session.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    enrolled = db.query(models.BatchStudent).filter(
        models.BatchStudent.batch_id == session.batch_id,
        models.BatchStudent.student_id == current_user.id,
    ).first()
    if not enrolled:
        raise HTTPException(status_code=403, detail="You are not enrolled in the batch for this session")

    existing = db.query(models.Attendance).filter(
        models.Attendance.session_id == payload.session_id,
        models.Attendance.student_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=422, detail="Attendance already marked for this session")

    record = models.Attendance(
        session_id=payload.session_id,
        student_id=current_user.id,
        status=payload.status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
