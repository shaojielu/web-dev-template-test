from fastapi import APIRouter

from app.api.routes import customers, dashboard, invoices, login, private, users, utils
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(customers.router)
api_router.include_router(invoices.router)
api_router.include_router(dashboard.router)


if settings.ENVIRONMENT in {"local", "test"}:
    api_router.include_router(private.router)
