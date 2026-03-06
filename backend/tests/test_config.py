import pytest

from app.core.config import Settings, parse_cors


def test_parse_cors_json_string() -> None:
    """A JSON-like string starting with '[' is returned as-is for Pydantic to parse."""
    result = parse_cors('["http://localhost"]')
    assert result == '["http://localhost"]'


def test_parse_cors_list_passthrough() -> None:
    """A list input is returned as-is."""
    result = parse_cors(["http://a.com"])
    assert result == ["http://a.com"]


def test_parse_cors_invalid_type_raises() -> None:
    """Non-string, non-list input should raise ValueError."""
    with pytest.raises(ValueError):
        parse_cors(123)


def test_check_default_secret_raises_in_non_local() -> None:
    """Using default secret in staging/production should raise ValueError."""
    with pytest.raises(ValueError, match="changethis"):
        Settings(
            ENVIRONMENT="staging",
            SECRET_KEY="changethis",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="postgres",
            POSTGRES_PASSWORD="safe_password",
            POSTGRES_DB="app_test",
            PROJECT_NAME="test",
            FIRST_SUPERUSER="admin@example.com",
            FIRST_SUPERUSER_PASSWORD="safe_password",
        )


def test_seed_sample_data_defaults_to_true_for_local() -> None:
    """SEED_SAMPLE_DATA should default to True when ENVIRONMENT is 'local'."""
    s = Settings(
        ENVIRONMENT="local",
        SECRET_KEY="testsecret",
        POSTGRES_SERVER="localhost",
        POSTGRES_USER="postgres",
        POSTGRES_PASSWORD="password",
        POSTGRES_DB="app_test",
        PROJECT_NAME="test",
        FIRST_SUPERUSER="admin@example.com",
        FIRST_SUPERUSER_PASSWORD="password",
    )
    assert s.SEED_SAMPLE_DATA is True
