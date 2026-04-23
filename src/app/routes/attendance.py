from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.attendance_schema import AttendanceMark
from ..services.attendance_services import mark_attendance

from ..security.dependencies import require_role


router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"]
)


@router.post("/mark")
async def mark_attendance_route(
    data: AttendanceMark,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role(["student"]))  #  Only students allowed
):
    """
    Mark attendance for a session.

     Access Control:
    - Requires valid JWT token
    - Only users with role = "student" allowed
    - Automatically enforced via dependency

     Request Body:
    - session_id: int

     Business Rules:
    - Session must exist
    - Session must be active (current time within session window)
    - Student must belong to the batch
    - Duplicate attendance is not allowed

     Response:
    - Success message if attendance marked

     Error Cases:
    - 401 → Invalid / missing token
    - 403 → Not a student OR not part of batch
    - 404 → Session not found
    - 400 → Session inactive / already marked
    """

    result = await mark_attendance(db, data.session_id, user)

    #  Session not found
    if result is None:
        raise HTTPException(status_code=404, detail="Session not found")

    #  Session not active
    if result == "inactive":
        raise HTTPException(status_code=400, detail="Session not active")

    #  Not part of batch
    if result == "not_member":
        raise HTTPException(status_code=403, detail="Not part of this batch")

    #  Duplicate attendance
    if result == "already_marked":
        raise HTTPException(status_code=400, detail="Attendance already marked")

    # Success
    return {"message": "Attendance marked successfully"}