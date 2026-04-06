import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import ForbiddenError, NotFoundError
from app.models.record import FinancialRecord
from app.models.user import User
from app.repositories.record_repository import RecordRepository
from app.schemas.record import (
    CreateRecordRequest,
    RecordListParams,
    UpdateRecordRequest,
)
from app.schemas.user import Role

logger = logging.getLogger(__name__)


class RecordService:
    """Business logic for financial record operations."""

    def __init__(self, db: AsyncSession):
        self.record_repo = RecordRepository(db)

    @staticmethod
    def _dollars_to_cents(amount: Decimal) -> int:
        """
        Convert a currency amount to cents using exact Decimal arithmetic.

        Decimal('1500.50') * 100  ->  Decimal('150050')  ->  int 150050
        No floating-point involved at any step.
        """
        return int(amount * 100)

    async def create_record(
        self, data: CreateRecordRequest, current_user: User
    ) -> FinancialRecord:
        """
        Create a new financial record.

        The record is attached to the authenticated user's ID.
        Only admins can create records (enforced at router level).
        """
        record = await self.record_repo.create(
            user_id=current_user.id,
            type=data.type.value,
            category=data.category,
            amount=self._dollars_to_cents(data.amount),
            record_date=data.date,
            description=data.description,
        )

        logger.info(f"Record created: id={record.id} by user={current_user.id}")
        return record

    async def get_record(self, record_id: UUID, current_user: User) -> FinancialRecord:
        """
        Get a single record by ID.

        Access control:
          - Admins can view any record
          - Viewers and analysts can only view their own records
        """
        record = await self.record_repo.get_by_id(record_id)
        if record is None:
            raise NotFoundError("Record", str(record_id))

        # Non-admin users can only view their own records
        if current_user.role != Role.ADMIN.value and record.user_id != current_user.id:
            raise ForbiddenError("You can only view your own records")

        return record

    async def list_records(
        self, params: RecordListParams, current_user: User
    ) -> tuple[list[FinancialRecord], int]:
        """
        List records with filtering and pagination.

        Access control:
          - Admins see all records
          - Viewers and analysts see only their own records
        """
        # Scope by user role
        user_id = None if current_user.role == Role.ADMIN.value else current_user.id
        type_value = params.type.value if params.type else None

        records, total = await self.record_repo.list_records(
            user_id=user_id,
            type=type_value,
            category=params.category,
            date_from=params.date_from,
            date_to=params.date_to,
            limit=params.per_page,
            offset=params.offset,
        )

        return records, total

    async def update_record(
        self,
        record_id: UUID,
        data: UpdateRecordRequest,
        current_user: User,
    ) -> FinancialRecord:
        """
        Update a record's fields (partial update).

        Only admins can update records (enforced at router level).
        """
        # Verify record exists
        record = await self.record_repo.get_by_id(record_id)
        if record is None:
            raise NotFoundError("Record", str(record_id))

        # Build update dict, converting amount if provided
        update_fields = {}
        if data.type is not None:
            update_fields["type"] = data.type.value
        if data.category is not None:
            update_fields["category"] = data.category
        if data.amount is not None:
            update_fields["amount"] = self._dollars_to_cents(data.amount)
        if data.description is not None:
            update_fields["description"] = data.description
        if data.date is not None:
            update_fields["date"] = data.date

        updated = await self.record_repo.update(record_id, **update_fields)
        if updated is None:
            raise NotFoundError("Record", str(record_id))

        logger.info(f"Record updated: id={record_id} by user={current_user.id}")
        return updated

    async def delete_record(
        self, record_id: UUID, current_user: User
    ) -> FinancialRecord:
        """
        Soft-delete a record.

        The record is marked as deleted and excluded from all queries,
        but not permanently removed from the database.
        Only admins can delete records (enforced at router level).
        """
        record = await self.record_repo.get_by_id(record_id)
        if record is None:
            raise NotFoundError("Record", str(record_id))

        deleted = await self.record_repo.soft_delete(record_id)
        if deleted is None:
            raise NotFoundError("Record", str(record_id))

        logger.info(f"Record soft-deleted: id={record_id} by user={current_user.id}")
        return deleted
