from datetime import datetime, timedelta
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db_models import Batch, BatchInvite, BatchStudent


async def create_batch(db: AsyncSession, data, user):
    batch = Batch(
        **data.model_dump(), created_by=user["user_id"], institution_id=user["user_id"]
    )
    db.add(batch)
    await db.commit()
    await db.refresh(batch)
    return batch


async def generate_invite(db: AsyncSession, batch_id: int, user):

    # Check batch exists
    result = await db.execute(select(Batch).where(Batch.id == batch_id))
    batch = result.scalar_one_or_none()

    if not batch:
        return None

    # Optional: check ownership
    if batch.created_by != user["user_id"]:
        return "forbidden"

    # Generate token
    token = str(uuid.uuid4())

    invite = BatchInvite(
        batch_id=batch_id, token=token, created_by=user["user_id"], expires_at=datetime.utcnow() + timedelta(hours=24)  
    )

    db.add(invite)
    await db.commit()

    return token


async def join_batch(db: AsyncSession, token: str, user):

    # Find invite
    result = await db.execute(select(BatchInvite).where(BatchInvite.token == token))
    invite = result.scalar_one_or_none()

    if not invite:
        return None

    # Add student to batch
    batch_student = BatchStudent(batch_id=invite.batch_id, student_id=user["user_id"])

    db.add(batch_student)
    await db.commit()

    return invite.batch_id
