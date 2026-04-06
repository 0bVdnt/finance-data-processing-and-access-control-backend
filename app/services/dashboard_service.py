from collections import defaultdict
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import (
    CategoryTotal,
    DashboardResponse,
    DashboardSummary,
    TrendData,
)
from app.schemas.record import RecordResponse, RecordType
from app.schemas.user import Role


class DashboardService:
    """Business logic for generating dashboard summaries and analytics."""

    def __init__(self, db: AsyncSession):
        self.repo = DashboardRepository(db)

    @staticmethod
    def _cents_to_dollars(cents: int) -> Decimal:
        """Convert cents securely back to fractional Decimal dollars."""
        return Decimal(cents) / Decimal(100)

    async def get_dashboard_data(self, current_user: User) -> DashboardResponse:
        """
        Aggregate all data for the dashboard.
        Scoped appropriately based on the user's role.
        """
        # Admins see global system data; others see only their own data
        user_id = None if current_user.role == Role.ADMIN.value else current_user.id

        # 1. Summary Totals
        totals = await self.repo.get_totals_by_type(user_id)
        income_cents = totals.get(RecordType.INCOME.value, 0)
        expense_cents = totals.get(RecordType.EXPENSE.value, 0)
        net_cents = income_cents - expense_cents

        summary = DashboardSummary(
            total_income=self._cents_to_dollars(income_cents),
            total_expenses=self._cents_to_dollars(expense_cents),
            net_balance=self._cents_to_dollars(net_cents),
        )

        # 2. Category Breakdown (Expenses only)
        categories = await self.repo.get_category_breakdown(user_id)
        category_breakdown = [
            CategoryTotal(category=cat, total=self._cents_to_dollars(amount))
            for cat, amount in categories
        ]

        # 3. Monthly Trends
        raw_trends = await self.repo.get_monthly_trends(user_id)
        trends_map = defaultdict(lambda: {"income": 0, "expense": 0})
        for month, rtype, amount in raw_trends:
            if rtype == RecordType.INCOME.value:
                trends_map[month]["income"] += amount
            elif rtype == RecordType.EXPENSE.value:
                trends_map[month]["expense"] += amount

        # Sorting trends by period string
        trends = [
            TrendData(
                period=month,
                income=self._cents_to_dollars(data["income"]),
                expense=self._cents_to_dollars(data["expense"]),
            )
            for month, data in sorted(trends_map.items())
        ]

        # 4. Recent Activity
        recent_records = await self.repo.get_recent_activity(limit=5, user_id=user_id)

        return DashboardResponse(
            summary=summary,
            category_breakdown=category_breakdown,
            recent_activity=[RecordResponse.from_record(r) for r in recent_records],
            trends=trends,
        )
