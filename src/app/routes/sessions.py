from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.attendance_schema import AttendanceResponse
from ..database import get_db
from ..schemas.session_schema import SessionCreate, SessionResponse
from ..services.session_services import create_session
from ..services.attendance_services import get_session_attendance
from ..security.dependencies import require_role


router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"]
)


# -----------------------------
# 📌 POST /sessions
# -----------------------------
@router.post("/", response_model=SessionResponse)
async def create_new_session(
    data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role(["trainer"]))  # 🔐 Only trainer
):
    """
    Create a session.

    🔐 Access:
    - Trainer only

    📥 Request Body:
    - title
    - date
    - start_time
    - end_time
    - batch_id

    ⚙️ Rules:
    - Batch must exist
    - Trainer must own the batch

    ❌ Errors:
    - 404 → Batch not found
    - 403 → Not your batch
    """

    session = await create_session(db, data, user)

    if session is None:
        raise HTTPException(status_code=404, detail="Batch not found")

    if session == "forbidden":
        raise HTTPException(status_code=403, detail="Not your batch")

    return session


# -----------------------------
# 📌 GET /sessions/{id}/attendance
# -----------------------------
@router.get("/{session_id}/attendance", response_model=list[AttendanceResponse])
async def get_attendance(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role(["trainer"]))  # 🔐 Only trainer
):
    """
    Get attendance list for a session.

    🔐 Access:
    - Trainer only

    📌 Path Param:
    - session_id

    📤 Response:
    - List of attendance records

    ⚙️ Rules:
    - Session must exist
    - Trainer must own the batch

    ❌ Errors:
    - 404 → Session not found
    - 403 → Not your batch
    """

    result = await get_session_attendance(db, session_id, user)

    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if result == "forbidden":
        raise HTTPException(status_code=403, detail="Not your batch")

    return result