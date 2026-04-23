#  SkillBridge Attendance Management API

A FastAPI-based backend system for managing batches, sessions, and attendance with JWT authentication and role-based access control.

---

#  Live API

Base URL:

```
https://attendance-management-system-fb7g.onrender.com/
```



---

##  Test Login (Live)

```bash
curl -X POST "https://your-deployed-api.com/auth/login" \
-H "Content-Type: application/json" \
-d '{
  "email": "trainer1@test.com",
  "password": "123456"
}'
```

---

#  Local Setup

## 1. Clone Repository

```bash
git clone <your-repo-url>
cd skillbridge-assignment
```

---

## 2. Install Dependencies

```bash
pip install poetry
poetry install
```

---

## 3. Create `.env` file

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname
SECRET_KEY=mysecret123
MONITORING_API_KEY=monitor123
```

---

## 4. Run Migrations

```bash
poetry run alembic upgrade head
```

---

## 5. Start Server

```bash
poetry run uvicorn app.main:app --reload
```

---

## 6. API Docs

```
http://127.0.0.1:8000/docs
```

---

# 👤 Test Accounts

| Role               | Email                                         | Password |
| ------------------ | --------------------------------------------- | -------- |
| Trainer            | [trainer1@test.com](mailto:trainer1@test.com) | 123456   |
| Student            | [student1@test.com](mailto:student1@test.com) | 123456   |
| Institution        | [inst1@test.com](mailto:inst1@test.com)       | 123456   |
| Programme Manager  | [pm1@test.com](mailto:pm1@test.com)           | 123456   |
| Monitoring Officer | [monitor1@test.com](mailto:monitor1@test.com) | 123456   |

---

#  Authentication

### Access Token (JWT)

* Used for all protected endpoints
* Contains: `user_id`, `role`, `iat`, `exp`

### Monitoring Token

* Special token for Monitoring Officer
* Valid for 1 hour
* Required for `/monitoring/attendance`

---

#  API Endpoints

---

##  Auth

### Signup

```bash
curl -X POST "http://localhost:8000/auth/signup" \
-H "Content-Type: application/json" \
-d '{
  "name": "Trainer One",
  "email": "trainer1@test.com",
  "password": "123456",
  "role": "trainer"
}'
```

---

### Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
-H "Content-Type: application/json" \
-d '{
  "email": "trainer1@test.com",
  "password": "123456"
}'
```

---

##  Batches

### Create Batch

```bash
curl -X POST "http://localhost:8000/batches/" \
-H "Authorization: Bearer <TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "name": "Batch Alpha",
  "description": "AI Batch"
}'
```

---

### Generate Invite

```bash
curl -X POST "http://localhost:8000/batches/1/invite" \
-H "Authorization: Bearer <TOKEN>"
```

---

### Join Batch

```bash
curl -X POST "http://localhost:8000/batches/join" \
-H "Authorization: Bearer <TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "invite_token": "TOKEN"
}'
```

---

##  Sessions

### Create Session

```bash
curl -X POST "http://localhost:8000/sessions/" \
-H "Authorization: Bearer <TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "title": "Session 1",
  "date": "2026-04-22",
  "start_time": "00:00:00",
  "end_time": "23:59:59",
  "batch_id": 1
}'
```

---

##  Attendance

### Mark Attendance

```bash
curl -X POST "http://localhost:8000/attendance/mark" \
-H "Authorization: Bearer <TOKEN>" \
-H "Content-Type: application/json" \
-d '{
  "session_id": 1
}'
```

---

### Get Session Attendance

```bash
curl -X GET "http://localhost:8000/sessions/1/attendance" \
-H "Authorization: Bearer <TOKEN>"
```

---

##  Summary

### Batch Summary

```bash
curl -X GET "http://localhost:8000/batches/1/summary" \
-H "Authorization: Bearer <TOKEN>"
```

---

### Programme Summary

```bash
curl -X GET "http://localhost:8000/programme/summary" \
-H "Authorization: Bearer <TOKEN>"
```

---

##  Monitoring

### Get Monitoring Token

```bash
curl -X POST "http://localhost:8000/auth/monitoring-token" \
-H "Authorization: Bearer <TOKEN>" \
-H "Content-Type: application/json" \
-d '{"key": "monitor123"}'
```

---

### Get Monitoring Attendance

```bash
curl -X GET "http://localhost:8000/monitoring/attendance" \
-H "Authorization: Bearer <MONITORING_TOKEN>"
```

---

### Blocked Methods (Expected 405)

```bash
POST /monitoring/attendance
PUT /monitoring/attendance
DELETE /monitoring/attendance
```

---

#  Schema Decisions

### batch_trainers

* Designed for many-to-many relationship
* Not used currently (simplified to `created_by`)

### batch_invites

* Stores invite tokens with expiry
* Ensures secure batch joining

### Dual Token System

* Normal JWT → app access
* Monitoring token → restricted analytics access

---

#  What is Working

* JWT Authentication
* Role-based access control
* Batch + Invite system
* Session creation
* Attendance marking
* Monitoring system
* Summary endpoints

---

#  Partial / Limitations

* batch_trainers table not used
* No advanced analytics in summaries
* Minimal validation on some fields

---

#  What I'd Improve

With more time:

* Implement multi-trainer support using `batch_trainers`
* Add caching for summaries
* Add refresh tokens

---

#  Running Tests

```bash
poetry run pytest -v
```

---

#  Tech Stack

* FastAPI
* PostgreSQL
* SQLAlchemy (Async)
* Alembic
* JWT (python-jose)
* Pytest

---

#  Author

Ayush Sharma
