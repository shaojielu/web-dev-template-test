import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import CurrentUserDep, SessionDep, get_current_active_superuser
from app.core.config import settings
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.users import Message, NewPassword, Token, UserPublic
from app.services.user import authenticate, get_user_by_email, set_user_password
from app.utils.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)

router = APIRouter(prefix="/login", tags=["login"])
logger = logging.getLogger(__name__)


def _send_password_recovery_email(
    *, email_to: str, subject: str, html_content: str
) -> None:
    """Best-effort email sender for background tasks."""
    try:
        send_email(email_to=email_to, subject=subject, html_content=html_content)
    except Exception:
        # Keep password-recovery response stable even if email delivery fails.
        logger.exception("Failed to send password recovery email to %s", email_to)


@router.post("/access-token", response_model=Token)
async def login_access_token(
    _request: Request,
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """Login and get access token."""
    user = await authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/test-token", response_model=UserPublic)
async def test_token(current_user: CurrentUserDep) -> User:
    """Test access token."""
    return current_user


@router.post("/password-recovery/{email}")
async def recover_password(
    _request: Request,
    email: str,
    session: SessionDep,
    background_tasks: BackgroundTasks,
) -> Message:
    """Password recovery."""
    user = await get_user_by_email(session=session, email=email)

    if user:
        password_reset_token = generate_password_reset_token(email=email)
        email_data = generate_reset_password_email(
            email_to=user.email, email=email, token=password_reset_token
        )
        background_tasks.add_task(
            _send_password_recovery_email,
            email_to=user.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    # Return same message regardless of whether user exists to prevent enumeration
    return Message(message="Password recovery email sent")


@router.post("/reset-password/")
async def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """Reset password."""
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )
    user = await get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this email does not exist in the system.",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    await set_user_password(session=session, user=user, new_password=body.new_password)
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
)
async def recover_password_html_content(
    email: str, session: SessionDep
) -> HTMLResponse:
    """Get HTML content of password recovery email."""
    user = await get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user with this email does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HTMLResponse(
        content=email_data.html_content, headers={"subject": email_data.subject}
    )
