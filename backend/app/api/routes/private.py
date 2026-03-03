from fastapi import APIRouter, Depends, status

from app.api.deps import SessionDep, get_current_active_superuser
from app.models.user import User
from app.schemas.users import PrivateUserCreate, UserCreate, UserPublic
from app.services.user import create_user

router = APIRouter(
    prefix="/private",
    tags=["private"],
    dependencies=[Depends(get_current_active_superuser)],
)


@router.post(
    "/users/",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_private_user(user_in: PrivateUserCreate, session: SessionDep) -> User:
    user_create = UserCreate(
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name,
    )
    return await create_user(session, user_create)
