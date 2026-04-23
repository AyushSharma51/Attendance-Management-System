from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.batch_schema import BatchCreate, BatchInviteResponse, BatchJoin
from ..services.batch_services import (
    create_batch,
    generate_invite,
    join_batch
)

from ..security.dependencies import require_role


router = APIRouter(
    prefix="/batches",
    tags=["Batches"]
)


# -----------------------------
# 📌 POST /batches
# -----------------------------
@router.post("/")
async def create_new_batch(
    data: BatchCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role(["trainer", "institution"]))  #  Allowed roles
):
    """
    Create a new batch.

    🔐 Access:
    - Trainer
    - Institution

    📥 Request Body:
    - name
    - description (optional)

    📤 Response:
    - Created batch object

    ⚠️ Notes:
    - Role validation handled by dependency
    """

    return await create_batch(db, data, user)


# -----------------------------
# 📌 POST /batches/{id}/invite
# -----------------------------
@router.post("/{batch_id}/invite", response_model=BatchInviteResponse)
async def create_invite(
    batch_id: int,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role(["trainer"]))  # 🔐 Only trainer
):
    """
    Generate invite token for a batch.

    🔐 Access:
    - Trainer only

    📌 Path Param:
    - batch_id

    📤 Response:
    - invite_token

    ⚙️ Rules:
    - Batch must exist
    - Trainer must own the batch

    ❌ Errors:
    - 404 → Batch not found
    - 403 → Not your batch
    """

    token = await generate_invite(db, batch_id, user)

    if token is None:
        raise HTTPException(status_code=404, detail="Batch not found")

    if token == "forbidden":
        raise HTTPException(status_code=403, detail="Not your batch")

    return {"invite_token": token}


# -----------------------------
# 📌 POST /batches/join
# -----------------------------
@router.post("/join")
async def join_batch_route(
    data: BatchJoin,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role(["student"]))  # 🔐 Only student
):
    """
    Join a batch using invite token.

    🔐 Access:
    - Student only

    📥 Request Body:
    - invite_token

    📤 Response:
    - batch_id

    ⚙️ Rules:
    - Token must be valid
    - Student joins batch

    ❌ Errors:
    - 404 → Invalid invite token
    """

    batch_id = await join_batch(db, data.invite_token, user)

    if not batch_id:
        raise HTTPException(status_code=404, detail="Invalid invite token")

    return {"batch_id": batch_id}