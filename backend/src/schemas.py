from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from datetime import date, time, datetime
from src.models import RoleEnum, AttendanceStatus


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    age: int
    role: RoleEnum
    password: str   # ✅ ADD THIS
    institution_id: Optional[int] = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MonitoringTokenRequest(BaseModel):
    key: str


# --- Batch ---
class BatchCreate(BaseModel):
    name: str
    institution_id: int


class BatchResponse(BaseModel):
    id: int
    name: str
    institution_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteResponse(BaseModel):
    token: str
    expires_at: datetime
    batch_id: int


class JoinBatchRequest(BaseModel):
    token: str


# --- Session ---
class SessionCreate(BaseModel):
    title: str
    date: date
    start_time: time
    end_time: time
    batch_id: int


class SessionResponse(BaseModel):
    id: int
    title: str
    date: date
    start_time: time
    end_time: time
    batch_id: int
    trainer_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Attendance ---
class AttendanceMark(BaseModel):
    session_id: int
    status: AttendanceStatus


class AttendanceRecord(BaseModel):
    id: int
    session_id: int
    student_id: int
    status: AttendanceStatus
    marked_at: datetime

    model_config = {"from_attributes": True}


class AttendanceWithStudent(BaseModel):
    student_id: int
    student_name: str
    student_email: str
    status: AttendanceStatus
    marked_at: datetime


class SessionAttendanceResponse(BaseModel):
    session_id: int
    session_title: str
    total: int
    records: List[AttendanceWithStudent]


# --- Summaries ---
class BatchSummaryResponse(BaseModel):
    batch_id: int
    batch_name: str
    total_students: int
    total_sessions: int
    total_attendance_marked: int
    present_count: int
    absent_count: int
    late_count: int


class InstitutionSummaryResponse(BaseModel):
    institution_id: int
    institution_name: str
    batches: List[BatchSummaryResponse]


class ProgrammeSummaryResponse(BaseModel):
    total_institutions: int
    total_batches: int
    total_students: int
    total_sessions: int
    total_attendance_marked: int
    present_count: int
    absent_count: int
    late_count: int


class MonitoringAttendanceRecord(BaseModel):
    session_id: int
    session_title: str
    batch_id: int
    batch_name: str
    institution_id: int
    institution_name: str
    student_id: int
    student_name: str
    status: AttendanceStatus
    marked_at: datetime
