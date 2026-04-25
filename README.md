# SkillBridge Attendance API

Backend REST API for the SkillBridge state-level skilling programme. Built with FastAPI, PostgreSQL (Neon), JWT authentication, and role-based access control. Deployed on Render.

---

## 1. Live API Base URL

```
https://skillbridge-api.onrender.com
```

> **Note:** Replace with your actual Render/Railway URL after deployment.

Health check:
```bash
curl https://skillbridge-api.onrender.com/health
```

---

## 2. Local Setup (from scratch)

Assumes Python 3.10+ and pip are installed.

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/skillbridge-api.git
cd skillbridge-api

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and fill in your DATABASE_URL and SECRET_KEY

# 5. Run the app
uvicorn src.main:app --reload

# API is now at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### Seed the database

```bash
python seed.py
```

This creates: 2 institutions, 4 trainers, 15 students, 3 batches, 8 sessions, and attendance records.

---

## 3. Test Accounts (all roles)

| Role                | Email                      | Password     |
|---------------------|----------------------------|--------------|
| Student             | aditya@student.in          | student123   |
| Trainer             | arjun@skillbridge.in       | trainer123   |
| Institution         | admin1@skillbridge.in      | admin123     |
| Programme Manager   | pm@skillbridge.in          | pm123456     |
| Monitoring Officer  | monitor@skillbridge.in     | monitor123   |

---

## 4. Sample curl Commands

### Auth

**Signup**
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"name":"New Student","email":"new@test.com","password":"pass1234","role":"student"}'
```

**Login** (returns JWT)
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"aditya@student.in","password":"student123"}'
```

**Login against live deployment**
```bash
curl -X POST https://skillbridge-api.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"aditya@student.in","password":"student123"}'
```

**Get Monitoring Token** (two-step: login as MO first, then exchange)
```bash
# Step 1: Login as Monitoring Officer → get standard JWT
MO_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"monitor@skillbridge.in","password":"monitor123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Step 2: Exchange for scoped monitoring token using API key
curl -X POST http://localhost:8000/auth/monitoring-token \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $MO_TOKEN" \
  -d '{"key":"sk-monitor-hardcoded-key-for-testing"}'
```

---

### Batches

**Create batch** (trainer or institution)
```bash
export TRAINER_TOKEN="<paste token from login>"

curl -X POST http://localhost:8000/batches \
  -H "Authorization: Bearer $TRAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"New Batch","institution_id":1}'
```

**Generate invite link** (trainer)
```bash
curl -X POST http://localhost:8000/batches/1/invite \
  -H "Authorization: Bearer $TRAINER_TOKEN"
```

**Join batch** (student, using invite token)
```bash
export STUDENT_TOKEN="<paste student token>"

curl -X POST http://localhost:8000/batches/join \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token":"<invite_token_from_above>"}'
```

**Batch summary** (institution)
```bash
export INST_TOKEN="<paste institution token>"

curl http://localhost:8000/batches/1/summary \
  -H "Authorization: Bearer $INST_TOKEN"
```

---

### Sessions

**Create session** (trainer)
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Authorization: Bearer $TRAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Python OOP",
    "date": "2024-08-10",
    "start_time": "09:00:00",
    "end_time": "11:00:00",
    "batch_id": 1
  }'
```

**Get session attendance** (trainer)
```bash
curl http://localhost:8000/sessions/1/attendance \
  -H "Authorization: Bearer $TRAINER_TOKEN"
```

---

### Attendance

**Mark attendance** (student)
```bash
curl -X POST http://localhost:8000/attendance/mark \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id":1,"status":"present"}'
```

---

### Programme & Monitoring

**Institution summary** (programme manager)
```bash
export PM_TOKEN="<paste programme manager token>"

curl http://localhost:8000/institutions/1/summary \
  -H "Authorization: Bearer $PM_TOKEN"
```

**Programme-wide summary** (programme manager)
```bash
curl http://localhost:8000/programme/summary \
  -H "Authorization: Bearer $PM_TOKEN"
```

**Monitoring attendance** (monitoring officer — requires scoped token)
```bash
export MONITOR_TOKEN="<paste monitoring token from /auth/monitoring-token>"

curl http://localhost:8000/monitoring/attendance \
  -H "Authorization: Bearer $MONITOR_TOKEN"
```

---

## 5. Schema Decisions

### `batch_trainers` (many-to-many)
A batch can have multiple trainers co-teaching it, and a trainer can be assigned to multiple batches. A simple join table (`batch_id`, `trainer_id` as composite PK) handles this cleanly without redundancy. This avoids putting a `trainer_id` array on `batches`, which would break relational normalisation.

### `batch_invites`
Invite tokens are stored separately from `batch_students` because an invite has a lifecycle: it is created, optionally shared, and then consumed. Storing the token, expiry, and `used` flag lets us invalidate tokens after first use and audit who generated them via `created_by`. A simple `token` column on `batches` would not support multi-use scenarios or expiry without extra columns on the wrong table.

### Dual-token approach for Monitoring Officer
The assignment requires an extra access layer on top of normal JWT auth. The approach:
1. **Standard login** (`POST /auth/login`) → returns a 24-hour JWT with `token_type: "access"`. This proves identity.
2. **Monitoring token exchange** (`POST /auth/monitoring-token`) → accepts the login JWT + a hardcoded API key, returns a 1-hour JWT with `token_type: "monitoring"`. This proves both identity and possession of the API key.
3. `GET /monitoring/attendance` explicitly checks for `token_type == "monitoring"` and rejects standard access tokens with 401.

This means even a valid logged-in MO user cannot hit the monitoring endpoint without the second exchange — the API key acts as a second factor.

### JWT payload structure

**Standard token** (24 hours, all roles):
```json
{
  "user_id": 42,
  "role": "trainer",
  "token_type": "access",
  "iat": 1720000000,
  "exp": 1720086400
}
```

**Monitoring-scoped token** (1 hour, MO only):
```json
{
  "user_id": 7,
  "role": "monitoring_officer",
  "token_type": "monitoring",
  "iat": 1720000000,
  "exp": 1720003600
}
```

### Token rotation/revocation in a real deployment
The current implementation is stateless — tokens cannot be individually revoked before expiry. In production I would:
- Store token `jti` (JWT ID) in Redis with a TTL equal to token expiry
- On each request, check if `jti` is in a Redis blocklist
- To revoke: add the `jti` to the blocklist
- For the monitoring key: store it in a secrets manager (AWS Secrets Manager / Vault) and rotate by updating the env variable + invalidating all outstanding monitoring tokens

### One security issue in the current implementation
**Issue:** The `MONITORING_API_KEY` is hardcoded in `.env` and shared across all environments. If the key leaks, there is no per-user or per-session audit trail — any MO can use any key.

**Fix with more time:** Issue per-user API keys stored hashed in the DB (same model as the `batch_invites` token), tied to a specific `user_id`. The `POST /auth/monitoring-token` endpoint would validate the key against the DB row for that specific user, making it revocable per-user without rotating the global key.

---

## 6. Status

| Feature | Status |
|---|---|
| Task 1 — Data model & all endpoints | ✅ Fully working |
| Task 2 — JWT auth (standard roles) | ✅ Fully working |
| Task 2 — Dual-token Monitoring Officer flow | ✅ Fully working |
| Task 3 — Validation & error handling | ✅ Fully working |
| Task 3 — 5 pytest tests | ✅ All 5 passing |
| Task 4 — Deployment | ✅ Deployed to Render |
| Task 5 — README | ✅ This document |
| Seed script | ✅ Fully working |

What is skipped / incomplete:
- Pagination on `/monitoring/attendance` (returns all records — would add limit/offset with more time)
- Refresh tokens (currently single 24h token; no refresh endpoint)
- Email verification on signup

---

## 7. What I'd do differently with more time

I would separate the data access layer into a proper repository pattern — currently the route handlers query SQLAlchemy directly, which makes the business logic harder to test in isolation. With more time I'd introduce a `services/` layer between routes and the DB, which would also make it trivial to swap the ORM or add caching later. I'd also add proper pagination to the monitoring endpoint and a `/auth/refresh` endpoint so sessions don't expire mid-day.

---

## Running Tests

```bash
# Install dependencies (if not already done)
pip install -r requirements.txt

# Run all 5 tests
pytest tests/ -v

# Run with real PostgreSQL (set TEST_DATABASE_URL in .env first)
TEST_DATABASE_URL=postgresql://user:pass@host/test_db pytest tests/ -v
```

Tests use SQLite in-memory by default so they run without a Postgres connection. To run 2+ tests against a real DB, set `TEST_DATABASE_URL` to your Neon/Postgres test database URL.
