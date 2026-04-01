import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FinancialRecord(Base):
    """
    A financial entry (income or expense).

    Amount is stored in cents (integer) to avoid floating-point
    precision issues.
    """

    __tablename__ = "financial_records"
    __table_args__ = (
        CheckConstraint(
            "type IN ('income', 'expense')",
            name="ck_records_type_valid",
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_records_amount_positive",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(20), index=True)
    category: Mapped[str] = mapped_column(String(50), index=True)
    amount: Mapped[int] = mapped_column(BigInteger)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    date: Mapped[date] = mapped_column(Date, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="records")

    def __repr__(self) -> str:
        return f"<Record {self.type} {self.amount} {self.category}"
