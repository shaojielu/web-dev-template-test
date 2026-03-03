from pydantic import BaseModel


class DashboardCards(BaseModel):
    number_of_invoices: int
    number_of_customers: int
    total_paid_invoices: str
    total_pending_invoices: str


class RevenuePoint(BaseModel):
    month: str
    revenue: float
