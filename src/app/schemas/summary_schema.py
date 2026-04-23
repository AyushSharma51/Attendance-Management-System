from pydantic import BaseModel



class StudentAttendanceSummary(BaseModel):
    student_id: int
    total_sessions: int
    attended: int
    percentage: float



class BatchSummaryResponse(BaseModel):
    batch_id: int
    students: list[StudentAttendanceSummary]