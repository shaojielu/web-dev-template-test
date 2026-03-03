import datetime
import uuid

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import BaseSchema


class Token(BaseModel):
    """Token returned after successful login."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload."""

    sub: uuid.UUID | None = None


class Message(BaseModel):
    """Generic message response."""

    message: str


class NewPassword(BaseModel):
    """Data required for password reset."""

    token: str
    new_password: str = Field(min_length=8, max_length=128)


class UserBase(BaseModel):
    """User core fields."""

    email: EmailStr = Field(max_length=255)
    full_name: str = Field(default="", max_length=255)
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    """Data required for creating a user."""

    password: str = Field(..., min_length=8, max_length=128)


class UserRegister(BaseModel):
    """Data required for user registration."""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(BaseModel):
    """Optional data for updating a user."""

    email: EmailStr | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None
    is_superuser: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(BaseModel):
    """Data for updating current user profile."""

    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(BaseModel):
    """Data for updating current user password."""

    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class UserPublic(UserBase, BaseSchema):
    """Public user information, excluding password."""

    id: uuid.UUID
    created_at: datetime.datetime | None = None
    updated_at: datetime.datetime | None = None


class UsersPublic(BaseSchema):
    """Paginated list of users."""

    data: list[UserPublic]
    count: int


class PrivateUserCreate(BaseModel):
    """Data for creating a user via internal API."""

    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(max_length=255)
