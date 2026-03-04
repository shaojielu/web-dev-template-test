from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.utils.utils import (
    decimal_to_currency_string,
    generate_new_account_email,
    generate_password_reset_token,
    generate_reset_password_email,
    generate_test_email,
    render_email_template,
    send_email,
    verify_password_reset_token,
)


def test_decimal_to_currency_string_none() -> None:
    assert decimal_to_currency_string(None) == "0.00"


def test_decimal_to_currency_string_decimal() -> None:
    assert decimal_to_currency_string(Decimal("123.456")) == "123.46"


def test_decimal_to_currency_string_int() -> None:
    assert decimal_to_currency_string(42) == "42.00"


def test_decimal_to_currency_string_float() -> None:
    assert decimal_to_currency_string(9.1) == "9.10"


def test_decimal_to_currency_string_zero() -> None:
    assert decimal_to_currency_string(Decimal("0")) == "0.00"


def test_render_email_template() -> None:
    html = render_email_template(
        template_name="test_email.html",
        context={"project_name": "Test", "email": "a@b.com"},
    )
    assert isinstance(html, str)
    assert len(html) > 0


def test_generate_test_email() -> None:
    data = generate_test_email(email_to="user@example.com")
    assert "Test email" in data.subject
    assert len(data.html_content) > 0


def test_generate_reset_password_email() -> None:
    data = generate_reset_password_email(
        email_to="user@example.com",
        email="user@example.com",
        token="test-token",
    )
    assert "Password recovery" in data.subject
    assert len(data.html_content) > 0


def test_generate_new_account_email() -> None:
    data = generate_new_account_email(
        email_to="new@example.com",
        username="new@example.com",
        password="secret123",
    )
    assert "New account" in data.subject
    assert len(data.html_content) > 0


def test_generate_and_verify_password_reset_token() -> None:
    email = "roundtrip@example.com"
    token = generate_password_reset_token(email=email)
    result = verify_password_reset_token(token=token)
    assert result == email


def test_verify_password_reset_token_invalid() -> None:
    result = verify_password_reset_token(token="garbage.invalid.token")
    assert result is None


def test_verify_password_reset_token_wrong_type() -> None:
    """A token with a different type claim should be rejected."""
    import jwt

    from app.core.security import ALGORITHM

    token = jwt.encode(
        {"sub": "user@example.com", "type": "access"},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    result = verify_password_reset_token(token=token)
    assert result is None


def test_send_email_raises_when_not_configured() -> None:
    original = settings.SMTP_HOST
    settings.SMTP_HOST = None
    try:
        with pytest.raises(RuntimeError, match="no provided configuration"):
            send_email(
                email_to="test@example.com",
                subject="Test",
                html_content="<p>Hi</p>",
            )
    finally:
        settings.SMTP_HOST = original


def test_send_email_with_tls() -> None:
    original_host = settings.SMTP_HOST
    original_from = settings.EMAILS_FROM_EMAIL
    original_tls = settings.SMTP_TLS
    original_ssl = settings.SMTP_SSL
    original_user = settings.SMTP_USER
    original_password = settings.SMTP_PASSWORD

    settings.SMTP_HOST = "smtp.example.com"
    settings.EMAILS_FROM_EMAIL = "noreply@example.com"  # type: ignore[assignment]
    settings.SMTP_TLS = True
    settings.SMTP_SSL = False
    settings.SMTP_USER = "user"
    settings.SMTP_PASSWORD = "pass"

    try:
        with patch("app.utils.utils.emails.Message") as mock_msg_cls:
            mock_msg = MagicMock()
            mock_msg_cls.return_value = mock_msg
            mock_msg.send.return_value = MagicMock()

            send_email(
                email_to="dest@example.com",
                subject="Subj",
                html_content="<p>Hi</p>",
            )

            mock_msg.send.assert_called_once()
            call_kwargs = mock_msg.send.call_args
            smtp_opts = call_kwargs.kwargs["smtp"]
            assert smtp_opts["tls"] is True
            assert smtp_opts["user"] == "user"
            assert smtp_opts["password"] == "pass"
    finally:
        settings.SMTP_HOST = original_host
        settings.EMAILS_FROM_EMAIL = original_from  # type: ignore[assignment]
        settings.SMTP_TLS = original_tls
        settings.SMTP_SSL = original_ssl
        settings.SMTP_USER = original_user
        settings.SMTP_PASSWORD = original_password


def test_send_email_with_ssl() -> None:
    original_host = settings.SMTP_HOST
    original_from = settings.EMAILS_FROM_EMAIL
    original_tls = settings.SMTP_TLS
    original_ssl = settings.SMTP_SSL
    original_user = settings.SMTP_USER
    original_password = settings.SMTP_PASSWORD

    settings.SMTP_HOST = "smtp.example.com"
    settings.EMAILS_FROM_EMAIL = "noreply@example.com"  # type: ignore[assignment]
    settings.SMTP_TLS = False
    settings.SMTP_SSL = True
    settings.SMTP_USER = None
    settings.SMTP_PASSWORD = None

    try:
        with patch("app.utils.utils.emails.Message") as mock_msg_cls:
            mock_msg = MagicMock()
            mock_msg_cls.return_value = mock_msg
            mock_msg.send.return_value = MagicMock()

            send_email(
                email_to="dest@example.com",
                subject="Subj",
                html_content="<p>Hi</p>",
            )

            call_kwargs = mock_msg.send.call_args
            smtp_opts = call_kwargs.kwargs["smtp"]
            assert smtp_opts["ssl"] is True
            assert "tls" not in smtp_opts
            assert "user" not in smtp_opts
            assert "password" not in smtp_opts
    finally:
        settings.SMTP_HOST = original_host
        settings.EMAILS_FROM_EMAIL = original_from  # type: ignore[assignment]
        settings.SMTP_TLS = original_tls
        settings.SMTP_SSL = original_ssl
        settings.SMTP_USER = original_user
        settings.SMTP_PASSWORD = original_password
