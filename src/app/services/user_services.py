from ..db_models import User
from ..security.auth import hash_password
from sqlalchemy.ext.asyncio import AsyncSession

async def create_user(db: AsyncSession, data):
    user_data = data.model_dump()

    # Replace plain password with hashed password
    user_data["password"] = hash_password(user_data["password"])

    user = User(**user_data)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user