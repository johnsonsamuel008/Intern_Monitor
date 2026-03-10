from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Integer,
    ForeignKey,
    BigInteger,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


# =========================
# USERS
# =========================

class User(Base):
    __tablename__ = "users"

    # Primary Key as Auto-incrementing Integer
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    role = Column(String, nullable=False)  # admin | intern

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))

    devices = relationship(
        "Device",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'intern')",
            name="ck_users_role"
        ),
    )


# =========================
# DEVICES
# =========================

class Device(Base):
    __tablename__ = "devices"

    # Primary Key as Auto-incrementing Integer
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    device_name = Column(String, nullable=True)
    os_type = Column(String, nullable=True)

    pairing_token = Column(String, unique=True, index=True, nullable=True)

    is_active = Column(Boolean, default=True)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="devices")

    __table_args__ = (
        # Supports online intern calculation: active + last_seen window + distinct user_id.
        Index("ix_devices_active_last_seen_user", "is_active", "last_seen", "user_id"),
    )


# =========================
# ACTIVITY LOGS (CANONICAL)
# =========================

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    activity_type = Column(String, nullable=False)
    recorded_at = Column(DateTime(timezone=True), index=True, nullable=False)

    # Combined Fields
    activity_metadata = Column(JSONB, nullable=False)
    is_flagged = Column(Boolean, default=False, index=True)
    flag_reason = Column(String, nullable=True)
    
    # Performance metrics (SRS 3.4)
    cpu_percent = Column(Integer, nullable=True)
    ram_percent = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    device = relationship("Device")
    user = relationship("User")

    __table_args__ = (
        Index(
            "ix_activity_logs_device_time",
            "device_id",
            "recorded_at"
        ),
        # Supports flagged-log pages sorted by newest first.
        Index(
            "ix_activity_logs_flagged_time",
            "is_flagged",
            "recorded_at",
        ),
    )

# =========================
# TASKS
# =========================

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    assigned_to = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )

    title = Column(String, nullable=False)
    description = Column(String)

    status = Column(String, default="pending")
    progress = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed')",
            name="ck_tasks_status"
        ),
        CheckConstraint(
            "progress BETWEEN 0 AND 100",
            name="ck_tasks_progress"
        ),
        # Supports admin task listing with status filter and recency sorting.
        Index("ix_tasks_status_id", "status", "id"),
    )
