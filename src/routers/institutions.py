from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src import models, schemas, auth

router = APIRouter(prefix="/institutions", tags=["institutions"])


def _batch_summary(batch: models.Batch, db: Session) -> schemas.BatchSummaryResponse:
    total_students = db.query(models.BatchStudent).filter(models.BatchStudent.batch_id == batch.id).count()
    sessions = db.query(models.Session).filter(models.Session.batch_id == batch.id).all()
    session_ids = [s.id for s in sessions]
    records = db.query(models.Attendance).filter(models.Attendance.session_id.in_(session_ids)).all() if session_ids else []
    present = sum(1 for r in records if r.status.value == "present")
    absent = sum(1 for r in records if r.status.value == "absent")
    late = sum(1 for r in records if r.status.value == "late")
    return schemas.BatchSummaryResponse(
        batch_id=batch.id,
        batch_name=batch.name,
        total_students=total_students,
        total_sessions=len(sessions),
        total_attendance_marked=len(records),
        present_count=present,
        absent_count=absent,
        late_count=late,
    )


@router.get("/{institution_id}/summary", response_model=schemas.InstitutionSummaryResponse)
def institution_summary(
    institution_id: int,
    current_user: models.User = Depends(auth.require_roles("programme_manager")),
    db: Session = Depends(get_db),
):
    institution = db.query(models.Institution).filter(models.Institution.id == institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    batches = db.query(models.Batch).filter(models.Batch.institution_id == institution_id).all()
    batch_summaries = [_batch_summary(b, db) for b in batches]

    return schemas.InstitutionSummaryResponse(
        institution_id=institution_id,
        institution_name=institution.name,
        batches=batch_summaries,
    )
