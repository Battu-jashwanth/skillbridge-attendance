"""
5 required pytest tests for SkillBridge API.
Tests 1-3 hit a real (test) database via the db_session fixture.
Tests 4-5 also hit the real test DB (no mocking of DB).
"""
import pytest
from jose import jwt
from src.config import SECRET_KEY, ALGORITHM
from src import models
from src.auth import hash_password


# ── Helper: create a user directly in the DB and return a login token ──────────
def create_user_and_login(client, db_session, name, email, password, role, institution_id=None):
    user = models.User(
        name=name,
        email=email,
        hashed_password=hash_password(password),
        role=models.RoleEnum(role),
        institution_id=institution_id,
    )
    db_session.add(user)
    db_session.commit()
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ── Test 1: Student signup and login — asserts a valid JWT is returned ─────────
def test_student_signup_and_login(client):
    resp = client.post("/auth/signup", json={
        "name": "Test Student",
        "email": "teststudent@test.com",
        "password": "pass1234",
        "role": "student",
    })
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert "access_token" in body
    token = body["access_token"]

    # Decode and verify payload structure
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["role"] == "student"
    assert "user_id" in payload
    assert "exp" in payload
    assert "iat" in payload


# ── Test 2: Trainer creates a session with all required fields ─────────────────
def test_trainer_creates_session(client, db_session):
    # Create institution
    inst = models.Institution(name="Test Institution")
    db_session.add(inst)
    db_session.commit()
    db_session.refresh(inst)

    # Create trainer
    trainer_token = create_user_and_login(
        client, db_session, "Trainer One", "trainer1@test.com", "pass1234", "trainer", inst.id
    )

    # Create batch
    batch_resp = client.post(
        "/batches",
        json={"name": "Test Batch", "institution_id": inst.id},
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert batch_resp.status_code == 201, batch_resp.text
    batch_id = batch_resp.json()["id"]

    # Create session
    session_resp = client.post(
        "/sessions",
        json={
            "title": "Python Basics",
            "date": "2024-08-01",
            "start_time": "09:00:00",
            "end_time": "11:00:00",
            "batch_id": batch_id,
        },
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert session_resp.status_code == 201, session_resp.text
    data = session_resp.json()
    assert data["title"] == "Python Basics"
    assert data["batch_id"] == batch_id


# ── Test 3: Student marks their own attendance ────────────────────────────────
def test_student_marks_attendance(client, db_session):
    # Setup
    inst = models.Institution(name="Inst For Attendance Test")
    db_session.add(inst)
    db_session.commit()
    db_session.refresh(inst)

    trainer_token = create_user_and_login(
        client, db_session, "Trainer Att", "trainer_att@test.com", "pass1234", "trainer", inst.id
    )
    student_token = create_user_and_login(
        client, db_session, "Student Att", "student_att@test.com", "pass1234", "student"
    )

    # Get student id
    payload = jwt.decode(student_token, SECRET_KEY, algorithms=[ALGORITHM])
    student_id = payload["user_id"]

    # Create batch via trainer
    batch_resp = client.post(
        "/batches",
        json={"name": "Attendance Test Batch", "institution_id": inst.id},
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert batch_resp.status_code == 201
    batch_id = batch_resp.json()["id"]

    # Enroll student directly in DB
    db_session.add(models.BatchStudent(batch_id=batch_id, student_id=student_id))
    db_session.commit()

    # Create session
    session_resp = client.post(
        "/sessions",
        json={
            "title": "Attendance Session",
            "date": "2024-08-02",
            "start_time": "10:00:00",
            "end_time": "12:00:00",
            "batch_id": batch_id,
        },
        headers={"Authorization": f"Bearer {trainer_token}"},
    )
    assert session_resp.status_code == 201
    session_id = session_resp.json()["id"]

    # Student marks attendance
    att_resp = client.post(
        "/attendance/mark",
        json={"session_id": session_id, "status": "present"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert att_resp.status_code == 201, att_resp.text
    assert att_resp.json()["status"] == "present"
    assert att_resp.json()["student_id"] == student_id


# ── Test 4: POST to /monitoring/attendance returns 405 ───────────────────────
def test_monitoring_post_returns_405(client):
    resp = client.post("/monitoring/attendance", json={})
    assert resp.status_code == 405, f"Expected 405, got {resp.status_code}"


# ── Test 5: Protected endpoint with no token returns 401 ─────────────────────
def test_no_token_returns_401(client):
    resp = client.get("/sessions/1/attendance")
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"

    resp2 = client.post("/batches", json={"name": "x", "institution_id": 1})
    assert resp2.status_code == 401, f"Expected 401, got {resp2.status_code}"
