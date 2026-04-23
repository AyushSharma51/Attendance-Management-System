from pydantic import BaseModel
from datetime import date, time



class SessionCreate(BaseModel):
    title: str
    date: date
    start_time: time
    end_time: time
    batch_id: int


class SessionResponse(BaseModel):
    id: int
    title: str
    date: date
    start_time: time
    end_time: time
    batch_id: int

    class Config:
        from_attributes = True