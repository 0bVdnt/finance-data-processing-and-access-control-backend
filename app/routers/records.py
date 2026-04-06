import datetime as dt
import math
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import RequireRole
from app.models.user import User
from app.schemas.common import ApiResponse, Meta
from app.schemas.record import (
    CreateRecordRequest,
    RecordListParams,
    RecordResponse,
    RecordType,
    UpdateRecordRequest,
)
from app.schemas.user import Role
from app.services.record_service import RecordService

router = APIRouter(prefix="/records", tags=["Financial Records"])


@router.post(
    "/",
    response_model=ApiResponse[RecordResponse],
    status_code=201,
    summary="Create a financial record (Admin only)",
    description=(
        "Create a new income or expense record. "
        "Amount should be in currency units "
        "and is stored internally as cents to avoid floating-point errors."
    ),
)
async def create_record(
    data: CreateRecordRequest,
    current_user: User = Depends(RequireRole(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    service = RecordService(db)
    record = await service.create_record(data, current_user)
    return ApiResponse(success=True, data=RecordResponse.from_record(record))


@router.get(
    "/",
    response_model=ApiResponse[list[RecordResponse]],
    summary="List financial records",
    description=(
        "Retrieve a paginated list of financial records. "
        "Viewers and analysts see only their own records. "
        "Admins see all records. Supports filtering by type, category, and date range."
    ),
)
async def list_records(
    type: RecordType | None = Query(None, description="Filter by record type"),
    category: str | None = Query(None, description="Filter by category"),
    date_from: dt.date | None = Query(None, description="Start date (inclusive)"),
    date_to: dt.date | None = Query(None, description="End date (inclusive)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    params = RecordListParams(
        type=type,
        category=category,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=per_page,
    )

    service = RecordService(db)
    records, total = await service.list_records(params, current_user)

    return ApiResponse(
        success=True,
        data=[RecordResponse.from_record(r) for r in records],
        meta=Meta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=math.ceil(total / per_page) if total > 0 else 0,
        ),
    )


@router.get(
    "/{record_id}",
    response_model=ApiResponse[RecordResponse],
    summary="Get a financial record",
    description=(
        "Retrieve a single financial record by ID. "
        "Non-admin users can only view their own records."
    ),
)
async def get_record(
    record_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = RecordService(db)
    record = await service.get_record(record_id, current_user)
    return ApiResponse(success=True, data=RecordResponse.from_record(record))


@router.patch(
    "/{record_id}",
    response_model=ApiResponse[RecordResponse],
    summary="Update a financial record (Admin only)",
    description=(
        "Update one or more fields of a financial record. "
        "Only the provided fields are updated (partial update)."
    ),
)
async def update_record(
    record_id: UUID,
    data: UpdateRecordRequest,
    current_user: User = Depends(RequireRole(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    service = RecordService(db)
    record = await service.update_record(record_id, data, current_user)
    return ApiResponse(success=True, data=RecordResponse.from_record(record))


@router.delete(
    "/{record_id}",
    response_model=ApiResponse[RecordResponse],
    summary="Delete a financial record (Admin only)",
    description=(
        "Soft-delete a financial record. The record is marked as deleted "
        "and excluded from all queries, but not permanently removed."
    ),
)
async def delete_record(
    record_id: UUID,
    current_user: User = Depends(RequireRole(Role.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    service = RecordService(db)
    record = await service.delete_record(record_id, current_user)
    return ApiResponse(success=True, data=RecordResponse.from_record(record))
