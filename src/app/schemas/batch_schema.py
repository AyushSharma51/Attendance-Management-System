from pydantic import BaseModel


class BatchCreate(BaseModel):
    name: str
    description: str | None = None

class BatchInviteResponse(BaseModel):
    invite_token: str

class BatchJoin(BaseModel):
    invite_token: str