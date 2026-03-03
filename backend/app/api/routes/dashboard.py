from fastapi import APIRouter

from app.api.deps import CurrentActiveUserDep, SessionDep
from app.schemas.dashboard import DashboardCards, RevenuePoint
from app.services.dashboard import get_dashboard_cards, get_revenue_last_12_months

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/cards", response_model=DashboardCards)
async def read_dashboard_cards(
    session: SessionDep,
    _: CurrentActiveUserDep,
) -> DashboardCards:
    data = await get_dashboard_cards(session)
    return DashboardCards(**data)


@router.get("/revenue", response_model=list[RevenuePoint])
async def read_revenue(
    session: SessionDep,
    _: CurrentActiveUserDep,
) -> list[RevenuePoint]:
    revenue = await get_revenue_last_12_months(session)
    return [RevenuePoint(**item) for item in revenue]
