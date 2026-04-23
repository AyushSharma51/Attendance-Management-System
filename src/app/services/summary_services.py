from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..db_models import Attendance, Session, BatchStudent


# -----------------------------
# 📌 Batch Summary
# -----------------------------
async def get_batch_summary(db: AsyncSession, batch_id: int):
    """
    Calculate attendance summary for a batch.
    """

    # Total sessions in batch
    total_sessions_result = await db.execute(
        select(func.count(Session.id)).where(Session.batch_id == batch_id)
    )
    total_sessions = total_sessions_result.scalar() or 0

    # Get all students in batch
    result = await db.execute(
        select(BatchStudent.student_id).where(BatchStudent.batch_id == batch_id)
    )
    students = result.scalars().all()

    summary = []

    for student_id in students:
        # Count attendance
        result = await db.execute(
            select(func.count(Attendance.id)).join(Session).where(
                Attendance.student_id == student_id,
                Session.batch_id == batch_id
            )
        )
        attended = result.scalar() or 0

        percentage = (attended / total_sessions * 100) if total_sessions > 0 else 0

        summary.append({
            "student_id": student_id,
            "total_sessions": total_sessions,
            "attended": attended,
            "percentage": round(percentage, 2)
        })

    return summary


# -----------------------------
# 📌 Institution Summary
# -----------------------------
async def get_institution_summary(db: AsyncSession, institution_id: int):
    """
    Summary across all batches of an institution.
    """

    # Simplified: assume Batch has institution_id
    result = await db.execute(
        select(Session.id).join(Session.batch).where(
            Session.batch.has(institution_id=institution_id)
        )
    )
    total_sessions = len(result.scalars().all())

    result = await db.execute(select(func.count(Attendance.id)))
    total_attendance = result.scalar() or 0

    return {
        "total_sessions": total_sessions,
        "total_attendance": total_attendance
    }


# -----------------------------
# 📌 Programme Summary
# -----------------------------
async def get_programme_summary(db: AsyncSession):
    """
    Global summary.
    """

    total_sessions = await db.scalar(select(func.count(Session.id)))
    total_attendance = await db.scalar(select(func.count(Attendance.id)))

    return {
        "total_sessions": total_sessions or 0,
        "total_attendance": total_attendance or 0
    }


# -----------------------------
# 📌 Monitoring Attendance
# -----------------------------
async def get_monitoring_attendance(db: AsyncSession):
    """
    Read-only monitoring endpoint.
    """

    result = await db.execute(select(Attendance))
    return result.scalars().all()