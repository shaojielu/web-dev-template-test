from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app import initial_data
from app import main as main_module
from app.core import db as db_module

pytestmark = pytest.mark.anyio


async def test_lifespan_disposes_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_engine = SimpleNamespace(dispose=AsyncMock())
    monkeypatch.setattr(main_module, "engine", fake_engine)

    async with main_module.lifespan(main_module.app):
        pass

    fake_engine.dispose.assert_awaited_once()


async def test_create_tables_runs_metadata_create_all(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: dict[str, object] = {}

    class FakeConnection:
        async def run_sync(self, fn: object) -> None:
            called["fn"] = fn

    @asynccontextmanager
    async def fake_begin():
        yield FakeConnection()

    class FakeEngine:
        def begin(self):
            return fake_begin()

    logger_mock = MagicMock()
    monkeypatch.setattr(db_module, "engine", FakeEngine())
    monkeypatch.setattr(db_module, "logger", logger_mock)

    await db_module.create_tables()

    run_sync_fn = called["fn"]
    assert getattr(run_sync_fn, "__self__", None) is db_module.Base.metadata
    assert getattr(run_sync_fn, "__name__", "") == "create_all"
    logger_mock.info.assert_called_once_with("Tables created")


async def test_initial_data_main_calls_init_db(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_session = object()
    init_db_mock = AsyncMock()
    logger_mock = MagicMock()

    @asynccontextmanager
    async def fake_async_session():
        yield fake_session

    monkeypatch.setattr(initial_data, "async_session", fake_async_session)
    monkeypatch.setattr(initial_data, "init_db", init_db_mock)
    monkeypatch.setattr(initial_data, "logger", logger_mock)

    await initial_data.main()

    init_db_mock.assert_awaited_once_with(fake_session)
    assert logger_mock.info.call_count == 2
    assert logger_mock.info.call_args_list[0].args == ("Creating initial data",)
    assert logger_mock.info.call_args_list[1].args == ("Initial data created",)
