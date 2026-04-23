from datetime import datetime, date as dt_date, time
from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Date,
    Time,
    DateTime,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from .enums import UserRole, AttendanceStatus

# =========================
# BASE
# =========================

class Base(DeclarativeBase):
    pass


# =========================
# USERS
# =========================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(255), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    hashed_password: Mapped[str] = mapped_column(String(255))

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), index=True
    )

    institution_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # Self reference
    institution: Mapped["User"] = relationship(remote_side=[id])


# =========================
# BATCHES
# =========================

class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(String(255), index=True)

    description = Column(String, nullable=True)

    institution_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    created_by = Column(Integer, ForeignKey("users.id"))
    
    institution: Mapped["User"] = relationship(foreign_keys=[institution_id])


# =========================
# BATCH TRAINERS (M:N)
# =========================

class BatchTrainer(Base):
    __tablename__ = "batch_trainers"

    __table_args__ = (
        UniqueConstraint("batch_id", "trainer_id", name="uq_batch_trainer"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id"), index=True
    )

    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True
    )

    batch: Mapped["Batch"] = relationship()
    trainer: Mapped["User"] = relationship()


# =========================
# BATCH STUDENTS (M:N)
# =========================

class BatchStudent(Base):
    __tablename__ = "batch_students"

    __table_args__ = (
        UniqueConstraint("batch_id", "student_id", name="uq_batch_student"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id"), index=True
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True
    )

    batch: Mapped["Batch"] = relationship()
    student: Mapped["User"] = relationship()


# =========================
# BATCH INVITES
# =========================

class BatchInvite(Base):
    __tablename__ = "batch_invites"

    id: Mapped[int] = mapped_column(primary_key=True)

    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id"), index=True
    )

    token: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True
    )

    expires_at: Mapped[datetime]

    used: Mapped[bool] = mapped_column(Boolean, default=False)

    batch: Mapped["Batch"] = relationship()
    creator: Mapped["User"] = relationship()


# =========================
# SESSIONS
# =========================

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id"), index=True
    )

    trainer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True
    )

    title: Mapped[str] = mapped_column(String(255))

    date: Mapped[dt_date] = mapped_column(Date, index=True)

    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    batch: Mapped["Batch"] = relationship()
    trainer: Mapped["User"] = relationship()


# =========================
# ATTENDANCE
# =========================

class Attendance(Base):
    __tablename__ = "attendance"

    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_attendance"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id"), index=True
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True
    )

    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus), index=True
    )

    marked_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    session: Mapped["Session"] = relationship()
    student: Mapped["User"] = relationship()