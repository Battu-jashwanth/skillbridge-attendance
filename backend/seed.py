"""
Seed script: creates 2 institutions, 4 trainers, 15 students, 3 batches, 8 sessions
with attendance records. Also creates 1 programme_manager and 1 monitoring_officer.

Run: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import date, time, datetime, timedelta, timezone
from src.database import SessionLocal, engine
from src import models
from src.auth import hash_password
from src.database import Base

Base.metadata.create_all(bind=engine)

db = SessionLocal()

def clean():
    db.query(models.Attendance).delete()
    db.query(models.BatchInvite).delete()
    db.query(models.BatchStudent).delete()
    db.query(models.BatchTrainer).delete()
    db.query(models.Session).delete()
    db.query(models.Batch).delete()
    db.query(models.User).delete()
    db.query(models.Institution).delete()
    db.commit()
    print("Cleaned existing data.")

clean()

# --- Institutions ---
inst1 = models.Institution(name="Sunrise Polytechnic Institute")
inst2 = models.Institution(name="Greenfield Skill Development Centre")
db.add_all([inst1, inst2])
db.commit()
db.refresh(inst1)
db.refresh(inst2)
print(f"Institutions: {inst1.id} {inst1.name}, {inst2.id} {inst2.name}")

# --- Trainers ---
trainers_data = [
    ("Arjun Mehta", "arjun@skillbridge.in", inst1.id),
    ("Priya Nair", "priya@skillbridge.in", inst1.id),
    ("Ravi Kumar", "ravi@skillbridge.in", inst2.id),
    ("Sneha Pillai", "sneha@skillbridge.in", inst2.id),
]
trainers = []
for name, email, inst_id in trainers_data:
    u = models.User(name=name, email=email, hashed_password=hash_password("trainer123"),
                    role=models.RoleEnum.trainer, institution_id=inst_id)
    db.add(u)
    trainers.append(u)
db.commit()
for t in trainers:
    db.refresh(t)
print(f"Trainers created: {[t.email for t in trainers]}")

# --- Students ---
students_data = [
    ("Aditya Sharma", "aditya@student.in"),
    ("Bhavna Reddy", "bhavna@student.in"),
    ("Chirag Patel", "chirag@student.in"),
    ("Divya Singh", "divya@student.in"),
    ("Elan Raj", "elan@student.in"),
    ("Fatima Begum", "fatima@student.in"),
    ("Ganesh Iyer", "ganesh@student.in"),
    ("Harini Das", "harini@student.in"),
    ("Ishaan Bose", "ishaan@student.in"),
    ("Jaya Krishnan", "jaya@student.in"),
    ("Kiran Rao", "kiran@student.in"),
    ("Lakshmi Menon", "lakshmi@student.in"),
    ("Mohan Tiwari", "mohan@student.in"),
    ("Nisha Verma", "nisha@student.in"),
    ("Om Prakash", "om@student.in"),
]
students = []
for name, email in students_data:
    u = models.User(name=name, email=email, hashed_password=hash_password("student123"),
                    role=models.RoleEnum.student)
    db.add(u)
    students.append(u)
db.commit()
for s in students:
    db.refresh(s)
print(f"Students created: {len(students)}")

# --- Programme Manager ---
pm = models.User(name="Lakshmi Programme", email="pm@skillbridge.in",
                 hashed_password=hash_password("pm123456"),
                 role=models.RoleEnum.programme_manager)
db.add(pm)

# --- Monitoring Officer ---
mo = models.User(name="Suresh Monitor", email="monitor@skillbridge.in",
                 hashed_password=hash_password("monitor123"),
                 role=models.RoleEnum.monitoring_officer)
db.add(mo)

# --- Institution Admins ---
admin1 = models.User(name="Inst Admin One", email="admin1@skillbridge.in",
                     hashed_password=hash_password("admin123"),
                     role=models.RoleEnum.institution, institution_id=inst1.id)
admin2 = models.User(name="Inst Admin Two", email="admin2@skillbridge.in",
                     hashed_password=hash_password("admin123"),
                     role=models.RoleEnum.institution, institution_id=inst2.id)
db.add_all([admin1, admin2])
db.commit()
print("PM, Monitoring Officer, Institution admins created.")

# --- Batches ---
batch1 = models.Batch(name="Python Fundamentals - Batch A", institution_id=inst1.id)
batch2 = models.Batch(name="Data Science Bootcamp", institution_id=inst1.id)
batch3 = models.Batch(name="Web Development - Batch B", institution_id=inst2.id)
db.add_all([batch1, batch2, batch3])
db.commit()
db.refresh(batch1); db.refresh(batch2); db.refresh(batch3)
print(f"Batches: {batch1.id}, {batch2.id}, {batch3.id}")

# --- Assign Trainers to Batches ---
db.add_all([
    models.BatchTrainer(batch_id=batch1.id, trainer_id=trainers[0].id),
    models.BatchTrainer(batch_id=batch1.id, trainer_id=trainers[1].id),
    models.BatchTrainer(batch_id=batch2.id, trainer_id=trainers[1].id),
    models.BatchTrainer(batch_id=batch3.id, trainer_id=trainers[2].id),
    models.BatchTrainer(batch_id=batch3.id, trainer_id=trainers[3].id),
])
db.commit()

# --- Enroll Students in Batches ---
batch1_students = students[:6]
batch2_students = students[3:10]
batch3_students = students[8:]

for s in batch1_students:
    db.add(models.BatchStudent(batch_id=batch1.id, student_id=s.id))
for s in batch2_students:
    db.add(models.BatchStudent(batch_id=batch2.id, student_id=s.id))
for s in batch3_students:
    db.add(models.BatchStudent(batch_id=batch3.id, student_id=s.id))
db.commit()
print(f"Enrolled: {len(batch1_students)} in batch1, {len(batch2_students)} in batch2, {len(batch3_students)} in batch3")

# --- Sessions ---
today = date.today()
sessions_data = [
    (batch1.id, trainers[0].id, "Intro to Python", today - timedelta(days=10), time(9, 0), time(11, 0)),
    (batch1.id, trainers[0].id, "Control Flow & Functions", today - timedelta(days=7), time(9, 0), time(11, 0)),
    (batch1.id, trainers[1].id, "OOP in Python", today - timedelta(days=4), time(14, 0), time(16, 0)),
    (batch2.id, trainers[1].id, "NumPy & Pandas Basics", today - timedelta(days=9), time(10, 0), time(12, 0)),
    (batch2.id, trainers[1].id, "Data Visualisation", today - timedelta(days=6), time(10, 0), time(12, 0)),
    (batch3.id, trainers[2].id, "HTML & CSS Foundations", today - timedelta(days=8), time(9, 30), time(11, 30)),
    (batch3.id, trainers[2].id, "JavaScript Essentials", today - timedelta(days=5), time(9, 30), time(11, 30)),
    (batch3.id, trainers[3].id, "Responsive Design", today - timedelta(days=2), time(14, 0), time(16, 0)),
]
session_objs = []
for batch_id, trainer_id, title, d, start, end in sessions_data:
    s = models.Session(batch_id=batch_id, trainer_id=trainer_id, title=title,
                       date=d, start_time=start, end_time=end)
    db.add(s)
    session_objs.append(s)
db.commit()
for s in session_objs:
    db.refresh(s)
print(f"Sessions created: {len(session_objs)}")

# --- Attendance Records ---
import random
random.seed(42)
statuses = [models.AttendanceStatus.present, models.AttendanceStatus.absent, models.AttendanceStatus.late]
weights = [0.7, 0.2, 0.1]

batch_student_map = {
    batch1.id: batch1_students,
    batch2.id: batch2_students,
    batch3.id: batch3_students,
}

att_count = 0
for session in session_objs:
    enrolled = batch_student_map[session.batch_id]
    for student in enrolled:
        status = random.choices(statuses, weights=weights)[0]
        att = models.Attendance(session_id=session.id, student_id=student.id, status=status)
        db.add(att)
        att_count += 1

db.commit()
print(f"Attendance records created: {att_count}")

db.close()
print("\n✅ Seed complete! Test accounts:")
print("  Student:             aditya@student.in       / student123")
print("  Trainer:             arjun@skillbridge.in     / trainer123")
print("  Institution:         admin1@skillbridge.in    / admin123")
print("  Programme Manager:   pm@skillbridge.in        / pm123456")
print("  Monitoring Officer:  monitor@skillbridge.in   / monitor123")
