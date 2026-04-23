from datetime import datetime
from pydantic import BaseModel



class AttendanceMark(BaseModel):
    session_id: int

class AttendanceResponse(BaseModel):
    id: int
    session_id: int
    student_id: int
    timestamp: datetime

    class Config:
        from_attributes = True