from fastapi import APIRouter, Query

from app.api.deps import CurrentActiveUserDep, SessionDep
from app.schemas.customers import CustomerPublic, CustomersPublic, CustomersSummary
from app.services.customer import get_customer_summaries, get_customers

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=CustomersPublic)
async def read_customers(
    session: SessionDep,
    _: CurrentActiveUserDep,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> CustomersPublic:
    customers, count = await get_customers(session, skip=skip, limit=limit)
    return CustomersPublic(
        data=[CustomerPublic.model_validate(customer) for customer in customers],
        count=count,
    )


@router.get("/summary", response_model=CustomersSummary)
async def read_customers_summary(
    session: SessionDep,
    _: CurrentActiveUserDep,
    query: str | None = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> CustomersSummary:
    customers, count = await get_customer_summaries(
        session, query=query, skip=skip, limit=limit
    )
    return CustomersSummary(data=customers, count=count)
