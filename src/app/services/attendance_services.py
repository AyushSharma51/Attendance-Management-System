from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from ..db_models import Session, Attendance, BatchStudent


async def mark_attendance(db: AsyncSession, session_id: int, user):
    """
    Mark attendance for a student.

    Rules:
    - Session must exist
    - Session must be active
    - Student must belong to batch
    - No duplicate attendance
    """

    #  Get session
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    if result == "not_member":
        raise HTTPException(status_code=403)
    
    session = result.scalar_one_or_none()

    if not session:
        return None

    #  Check if session is active
    now = datetime.utcnow()

    session_start = datetime.combine(session.date, session.start_time)
    session_end = datetime.combine(session.date, session.end_time)

    if not (session_start <= now <= session_end):
        return "inactive"

    #  Check student belongs to batch
    result = await db.execute(
        select(BatchStudent).where(
            BatchStudent.batch_id == session.batch_id,
            BatchStudent.student_id == user["user_id"]
        )
    )
    membership = result.scalar_one_or_none()

    if not membership:
        return "not_member"

    #  Prevent duplicate attendance
    result = await db.execute(
        select(Attendance).where(
            Attendance.session_id == session_id,
            Attendance.student_id == user["user_id"]
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        return "already_marked"

    #  Mark attendance
    attendance = Attendance(
        session_id=session_id,
        student_id=user["user_id"],
        status="present" 
    )

    db.add(attendance)
    await db.commit()

    return attendance



async def get_session_attendance(db: AsyncSession, session_id: int, user):
    """
    Get attendance list for a session.

    Rules:
    - Only trainer allowed
    - Must own the batch
    """

    # 🔍 Get session
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        return None

    #  Ownership check
    if session.batch.created_by != user["user_id"]:
        return "forbidden"

    #  Get attendance
    result = await db.execute(
        select(Attendance).where(Attendance.session_id == session_id)
    )

    return result.scalars().all()