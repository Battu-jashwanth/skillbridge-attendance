from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.database import get_db
from src import models, schemas, auth

router = APIRouter(tags=["programme"])


@router.get("/programme/summary", response_model=schemas.ProgrammeSummaryResponse)
def programme_summary(
    current_user: models.User = Depends(auth.require_roles("programme_manager")),
    db: Session = Depends(get_db),
):
    total_institutions = db.query(models.Institution).count()
    total_batches = db.query(models.Batch).count()
    total_students = db.query(models.BatchStudent).count()
    total_sessions = db.query(models.Session).count()
    records = db.query(models.Attendance).all()
    present = sum(1 for r in records if r.status.value == "present")
    absent = sum(1 for r in records if r.status.value == "absent")
    late = sum(1 for r in records if r.status.value == "late")

    return schemas.ProgrammeSummaryResponse(
        total_institutions=total_institutions,
        total_batches=total_batches,
        total_students=total_students,
        total_sessions=total_sessions,
        total_attendance_marked=len(records),
        present_count=present,
        absent_count=absent,
        late_count=late,
    )


@router.get("/monitoring/attendance")
def monitoring_attendance(
    current_user: models.User = Depends(auth.get_monitoring_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.Attendance, models.User, models.Session, models.Batch, models.Institution)
        .join(models.User, models.Attendance.student_id == models.User.id)
        .join(models.Session, models.Attendance.session_id == models.Session.id)
        .join(models.Batch, models.Session.batch_id == models.Batch.id)
        .join(models.Institution, models.Batch.institution_id == models.Institution.id)
        .all()
    )

    result = [
        schemas.MonitoringAttendanceRecord(
            session_id=session.id,
            session_title=session.title,
            batch_id=batch.id,
            batch_name=batch.name,
            institution_id=institution.id,
            institution_name=institution.name,
            student_id=student.id,
            student_name=student.name,
            status=att.status,
            marked_at=att.marked_at,
        )
        for att, student, session, batch, institution in rows
    ]

    return {"total": len(result), "records": result}


@router.post("/monitoring/attendance")
@router.put("/monitoring/attendance")
@router.patch("/monitoring/attendance")
@router.delete("/monitoring/attendance")
def monitoring_attendance_method_not_allowed():
    raise HTTPException(status_code=405, detail="Method not allowed. /monitoring/attendance is read-only.")
