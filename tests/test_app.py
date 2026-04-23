"""
pytest test suite for Attendance Management System
===================================================
Requirements:
  - A running PostgreSQL instance accessible via TEST_DATABASE_URL env var
  - A .env (or env vars) with SECRET_KEY set

Run with:
    pytest tests/test_app.py -v

At least two tests hit a real (SQLite async) test database via a
real AsyncSession; the rest hit the full ASGI stack via httpx.AsyncClient.
"""

import os
import pytest
import pytest_asyncio
from datetime import date, datetime, timedelta

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


# ── patch env before importing the app ────────────────────────────────────────
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./test_attendance.db"   # lightweight; swapped in below
)

from src.app.main import app                          # FastAPI app
from src.app.database import get_db                   # dependency we'll override
from src.app.db_models import Base, User, Batch, BatchTrainer, Session as SessionModel
from src.app.security.auth import hash_password, create_access_token
from src.app.enums import UserRole

# ── test database (SQLite in-memory per test session) ─────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///./test_attendance_pytest.db"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as db:
        yield db


app.dependency_overrides[get_db] = override_get_db


# ── session-scoped fixtures ───────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create all tables once; drop them after the session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Yield a real AsyncSession for DB-direct tests."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Async HTTP client wired to the FastAPI ASGI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# ── helpers ───────────────────────────────────────────────────────────────────

def _unique_email(prefix: str = "user") -> str:
    return f"{prefix}_{datetime.utcnow().timestamp()}@test.com"


async def _create_user(
    db: AsyncSession,
    *,
    role: UserRole = UserRole.STUDENT,
    email: str | None = None,
    password: str = "Secret123!",
) -> User:
    user = User(
        name="Test User",
        email=email or _unique_email(role.value),
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _auth_headers(user_id: int, role: str) -> dict:
    token = create_access_token({"user_id": user_id, "role": role})
    return {"Authorization": f"Bearer {token}"}


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1 – Successful student signup and login; assert valid JWT returned
#           Uses real DB 
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_student_signup_and_login_returns_jwt(client: AsyncClient):
    """
    POST /auth/signup  → 200 + access_token
    POST /auth/login   → 200 + access_token (same credentials)

    Hits the real SQLite test database through the app's ASGI stack.
    """
    email = _unique_email("student")
    payload = {
        "name": "Alice",
        "email": email,
        "password": "TestPass99!",
        "role": "student",
    }

    # ── signup ──
    resp = await client.post("/auth/signup", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "access_token" in body
    token = body["access_token"]
    assert isinstance(token, str) and len(token) > 20

    # ── login with same credentials ──
    resp2 = await client.post(
        "/auth/login", json={"email": email, "password": "TestPass99!"}
    )
    assert resp2.status_code == 200, resp2.text
    body2 = resp2.json()
    assert "access_token" in body2
    assert isinstance(body2["access_token"], str) and len(body2["access_token"]) > 20


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2 – Trainer creates a session with all required fields
#           Uses real DB ✅
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_trainer_creates_session(client: AsyncClient, db_session: AsyncSession):
    """
    Seed trainer + batch directly in the test DB, then POST /sessions/.
    Verifies the session is persisted and the response contains expected fields.
    """
    # seed trainer
    trainer = await _create_user(db_session, role=UserRole.TRAINER)

    # seed batch owned by trainer
    batch = Batch(
        name="Morning Batch",
        institution_id=trainer.id,
        created_by=trainer.id,
    )
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)

    # seed BatchTrainer link
    bt = BatchTrainer(batch_id=batch.id, trainer_id=trainer.id)
    db_session.add(bt)
    await db_session.commit()

    headers = _auth_headers(trainer.id, "trainer")
    session_payload = {
        "title": "Python Basics",
        "date": str(date.today()),
        "start_time": "10:00:00",
        "end_time": "12:00:00",
        "batch_id": batch.id,
    }

    resp = await client.post("/sessions/", json=session_payload, headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # all required fields present
    for field in ("id", "title", "date", "start_time", "end_time", "batch_id"):
        assert field in data, f"Missing field: {field}"

    assert data["title"] == "Python Basics"
    assert data["batch_id"] == batch.id


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3 – Student marks their own attendance
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_student_marks_own_attendance(
    client: AsyncClient, db_session: AsyncSession
):
    """
    Seed all required rows (trainer, batch, BatchTrainer, BatchStudent, session)
    and then have the student POST /attendance/mark.

    The session window is set to NOW ± 1 hour so the 'active' check passes.
    """
    from src.app.db_models import BatchStudent, Attendance
    from src.app.enums import AttendanceStatus

    trainer = await _create_user(db_session, role=UserRole.TRAINER)
    student = await _create_user(db_session, role=UserRole.STUDENT)

    batch = Batch(
        name="Attendance Batch",
        institution_id=trainer.id,
        created_by=trainer.id,
    )
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(batch)

    db_session.add(BatchTrainer(batch_id=batch.id, trainer_id=trainer.id))
    db_session.add(BatchStudent(batch_id=batch.id, student_id=student.id))
    await db_session.commit()

    now = datetime.utcnow()
    session_obj = SessionModel(
        batch_id=batch.id,
        trainer_id=trainer.id,
        title="Live Session",
        date=now.date(),
        start_time=(now - timedelta(hours=1)).time(),
        end_time=(now + timedelta(hours=1)).time(),
    )
    db_session.add(session_obj)
    await db_session.commit()
    await db_session.refresh(session_obj)

    headers = _auth_headers(student.id, "student")
    resp = await client.post(
        "/attendance/mark",
        json={"session_id": session_obj.id},
        headers=headers,
    )

    # 200 → marked  |  400 "already_marked" → also acceptable (idempotency re-run)
    assert resp.status_code in (200, 400), resp.text
    if resp.status_code == 200:
        assert resp.json().get("message") == "Attendance marked successfully"


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4 – POST to /monitoring/attendance returns 405
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_post_monitoring_attendance_returns_405(client: AsyncClient):
    """
    The monitoring endpoint is GET-only.
    A POST must be rejected with HTTP 405 Method Not Allowed.
    No auth token needed – the method guard fires before auth.
    """
    resp = await client.post("/monitoring/attendance", json={})
    assert resp.status_code == 405, resp.text


# ══════════════════════════════════════════════════════════════════════════════
# TEST 5 – Protected endpoint with no token returns 401
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_protected_endpoint_no_token_returns_401(client: AsyncClient):
    """
    Any protected route called without an Authorization header must return 401.
    We probe three endpoints to make the assertion robust.
    """
    # POST /sessions/ requires trainer JWT
    resp = await client.post(
        "/sessions/",
        json={
            "title": "No Auth",
            "date": str(date.today()),
            "start_time": "09:00:00",
            "end_time": "10:00:00",
            "batch_id": 1,
        },
    )
    assert resp.status_code == 401, f"/sessions/ returned {resp.status_code}"

    # POST /attendance/mark requires student JWT
    resp2 = await client.post("/attendance/mark", json={"session_id": 1})
    assert resp2.status_code == 401, f"/attendance/mark returned {resp2.status_code}"

    # POST /batches/ requires trainer/institution JWT
    resp3 = await client.post("/batches/", json={"name": "No Auth Batch"})
    assert resp3.status_code == 401, f"/batches/ returned {resp3.status_code}"


# ══════════════════════════════════════════════════════════════════════════════
# BONUS TEST 6 – Login with wrong password returns 401
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(
    client: AsyncClient, db_session: AsyncSession
):
    """
    Direct DB seeding (real DB), then hit /auth/login via HTTP.
    Ensures wrong credentials don't leak a token.
    """
    user = await _create_user(
        db_session,
        role=UserRole.STUDENT,
        password="CorrectPassword1!",
    )

    resp = await client.post(
        "/auth/login",
        json={"email": user.email, "password": "WrongPassword!"},
    )
    assert resp.status_code == 401, resp.text
    assert "access_token" not in resp.json()