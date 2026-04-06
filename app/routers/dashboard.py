from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=ApiResponse[DashboardResponse],
    summary="Get dashboard aggregate summary",
    description=(
        "Retrieve aggregate financial data for the dashboard. "
        "Includes total income, total expenses, net balance, category breakdown, "
        "monthly trends, and recent activity. "
        "Admins will see system-wide aggregations; other roles will see only their own data."
    ),
)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    dashboard_data = await service.get_dashboard_data(current_user)

    return ApiResponse(success=True, data=dashboard_data)
