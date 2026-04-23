from sqlalchemy import select
from ..db_models import User
from ..security.auth import verify_password

async def authenticate_user(db, email, password):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return None

    if not verify_password(password, user.password):
        return None

    return user