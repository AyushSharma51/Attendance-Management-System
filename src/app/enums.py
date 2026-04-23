import enum


class UserRole(str, enum.Enum):
    STUDENT = "student"
    TRAINER = "trainer"
    INSTITUTION = "institution"
    PROGRAMME_MANAGER = "programme_manager"
    MONITORING_OFFICER = "monitoring_officer"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"