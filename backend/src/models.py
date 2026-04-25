from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text, Date, Time
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from src.database import Base


class RoleEnum(str, enum.Enum):
    student = "student"
    trainer = "trainer"
    institution = "institution"
    programme_manager = "programme_manager"
    monitoring_officer = "monitoring_officer"


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    late = "late"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    institution = relationship("Institution", back_populates="users")
    sessions_created = relationship("Session", back_populates="trainer")
    attendance_records = relationship("Attendance", back_populates="student")
    invites_created = relationship("BatchInvite", back_populates="creator")


class Institution(Base):
    __tablename__ = "institutions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="institution")
    batches = relationship("Batch", back_populates="institution")


class Batch(Base):
    __tablename__ = "batches"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    institution = relationship("Institution", back_populates="batches")
    trainers = relationship("BatchTrainer", back_populates="batch")
    students = relationship("BatchStudent", back_populates="batch")
    sessions = relationship("Session", back_populates="batch")
    invites = relationship("BatchInvite", back_populates="batch")


class BatchTrainer(Base):
    __tablename__ = "batch_trainers"
    batch_id = Column(Integer, ForeignKey("batches.id"), primary_key=True)
    trainer_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    batch = relationship("Batch", back_populates="trainers")
    trainer = relationship("User")


class BatchStudent(Base):
    __tablename__ = "batch_students"
    batch_id = Column(Integer, ForeignKey("batches.id"), primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

    batch = relationship("Batch", back_populates="students")
    student = relationship("User")


class BatchInvite(Base):
    __tablename__ = "batch_invites"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)

    batch = relationship("Batch", back_populates="invites")
    creator = relationship("User", back_populates="invites_created")


class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    batch = relationship("Batch", back_populates="sessions")
    trainer = relationship("User", back_populates="sessions_created")
    attendance_records = relationship("Attendance", back_populates="session")


class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(AttendanceStatus), nullable=False)
    marked_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="attendance_records")
    student = relationship("User", back_populates="attendance_records")
