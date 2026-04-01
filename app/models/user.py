import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """
    User account with role-based access.

    Roles:
        - viewer: Can only view dashboard data and own records
        - analyst: Can view records and access insights/summaries
        - admin: Full access - create, update, delete records and manage users
    """

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('viewer', 'analyst', 'admin')",
            name="ck_users_role_valid",
        ),
    )

    # Columns
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    records: Mapped[list["FinancialRecord"]] = relationship(
        back_populates="user", cascade="all,delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} role = {self.role}>"
