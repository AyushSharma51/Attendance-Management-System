from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..security.dependencies import require_role, require_monitoring_token
from ..database import get_db
from fastapi import Request
from ..services.summary_services import (
    get_batch_summary,
    get_institution_summary,
    get_programme_summary,
    get_monitoring_attendance
)


router = APIRouter(tags=["Summary"])


# -----------------------------
# 📌 GET /batches/{id}/summary
# -----------------------------
@router.get("/batches/{batch_id}/summary")
async def batch_summary(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role(["institution"]))  # 🔐 Only institution
):
    """
    Batch attendance summary.

    🔐 Access:
    - Institution only

    📌 Path Param:
    - batch_id

    📤 Response:
    - List of students with attendance %

    ⚙️ Rules:
    - Batch must exist
    - Aggregates attendance per student
    """

    return {
        "batch_id": batch_id,
        "students": await get_batch_summary(db, batch_id)
    }


# -----------------------------
# 📌 GET /institutions/{id}/summary
# -----------------------------
@router.get("/institutions/{institution_id}/summary")
async def institution_summary(
    institution_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role(["programme_manager"]))  # 🔐 Programme Manager
):
    """
    Institution-level summary.

    🔐 Access:
    - Programme Manager only

    📌 Path Param:
    - institution_id

    📤 Response:
    - Aggregated sessions and attendance
    """

    return await get_institution_summary(db, institution_id)


# -----------------------------
# 📌 GET /programme/summary
# -----------------------------
@router.get("/programme/summary")
async def programme_summary(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role(["programme_manager"]))  # 🔐 Programme Manager
):
    """
    Programme-wide summary.

    🔐 Access:
    - Programme Manager only

    📤 Response:
    - Total sessions
    - Total attendance
    """

    return await get_programme_summary(db)


# -----------------------------
# 📌 GET /monitoring/attendance
# -----------------------------
@router.get("/monitoring/attendance")
async def monitoring_attendance(
    db: AsyncSession = Depends(get_db),
    user=Depends(require_monitoring_token)  # 🔐 Special token
):
    """
    Monitoring attendance endpoint.

    🔐 Access:
    - Requires monitoring token (NOT normal JWT)

    📤 Response:
    - Full attendance records (read-only)

    ⚠️ Security:
    - Must use monitoring token
    - Rejects normal access tokens
    """

    return await get_monitoring_attendance(db)

@router.api_route("/monitoring/attendance", methods=["POST", "PUT", "DELETE"])
async def monitoring_not_allowed(request: Request):
    """
    Reject non-GET requests explicitly for monitoring endpoint.
    """
    raise HTTPException(status_code=405, detail="Method Not Allowed")