from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..db_models import Session, Batch


async def create_session(db: AsyncSession, data, user):
    """
    Create a session for a batch.

    Rules:
    - Only trainer can create session
    - Trainer must own the batch
    """

    # Check batch exists
    result = await db.execute(
        select(Batch).where(Batch.id == data.batch_id)
    )
    batch = result.scalar_one_or_none()

    if not batch:
        return None

    #  Ownership check
    if batch.created_by != user["user_id"]:
        return "forbidden"

    # 🧠 Create session using clean pattern
    session_data = data.model_dump()

    db_session = Session(
    **session_data,
    trainer_id=user["user_id"]   
)

    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)

    return db_session