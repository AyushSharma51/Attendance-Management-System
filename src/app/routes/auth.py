from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from ..security.dependencies import get_current_user  # ✅ FIXED
from ..database import get_db
from ..db_models import User
from ..schemas.user_schema import UserCreate, UserLogin
from ..schemas.auth_schema import MonitoringTokenRequest  # ✅ NEW
from ..security.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_monitoring_token
)

router = APIRouter(prefix="/auth", tags=["Auth"])


# -----------------------------
# 📌 POST /auth/signup
# -----------------------------
@router.post("/signup")
async def signup(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Create user + return JWT
    """

    user_data = data.model_dump()
    user_data["hashed_password"] = hash_password(user_data.pop("password"))

    user = User(**user_data)

    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token({
        "user_id": user.id,
        "role": user.role
    })

    return {"access_token": token}


# -----------------------------
# 📌 POST /auth/login
# -----------------------------
@router.post("/login")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Validate user + return JWT
    """

    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "user_id": user.id,
        "role": user.role
    })

    return {"access_token": token}


# -----------------------------
# 📌 POST /auth/monitoring-token
# -----------------------------
@router.post("/monitoring-token")
async def get_monitoring_token(
    data: MonitoringTokenRequest,
    user=Depends(get_current_user)
):
    """
    Generate monitoring scoped token.

    🔐 Access:
    - Requires valid JWT (access token)
    - Only Monitoring Officer role allowed

    📥 Request Body:
    - key: API key (from .env)

    📤 Response:
    - monitoring_token (1 hour expiry, read-only scope)
    """

    #  Ensure correct token type
    if user.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    #  Role check
    if user["role"] != "monitoring_officer":
        raise HTTPException(status_code=403, detail="Not allowed")

    #  API key validation
    if data.key != os.getenv("MONITORING_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")

    #  Generate monitoring token
    token = create_monitoring_token({
        "user_id": user["user_id"],
        "role": user["role"]
    })

    return {"monitoring_token": token}