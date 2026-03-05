import importlib.util
from pathlib import Path

import pytest


MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "alembic"
    / "versions"
    / "20260304_0001_initial.py"
)


def _load_migration_module():
    spec = importlib.util.spec_from_file_location("migration_20260304_0001", MIGRATION_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeOp:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []

    def f(self, name: str) -> str:
        return name

    def create_table(self, *args, **kwargs) -> None:
        self.calls.append(("create_table", args, kwargs))

    def create_index(self, *args, **kwargs) -> None:
        self.calls.append(("create_index", args, kwargs))

    def drop_index(self, *args, **kwargs) -> None:
        self.calls.append(("drop_index", args, kwargs))

    def drop_table(self, *args, **kwargs) -> None:
        self.calls.append(("drop_table", args, kwargs))


def test_upgrade_creates_expected_tables_and_indexes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_migration_module()
    fake_op = FakeOp()
    monkeypatch.setattr(module, "op", fake_op)

    module.upgrade()

    created_tables = [args[0] for kind, args, _ in fake_op.calls if kind == "create_table"]
    assert created_tables == ["api_keys", "model_registry", "risk_analyses"]

    created_indexes = [
        (args[0], args[1]) for kind, args, _ in fake_op.calls if kind == "create_index"
    ]
    assert ("ix_api_keys_key_hash", "api_keys") in created_indexes
    assert ("ix_api_keys_name", "api_keys") in created_indexes
    assert ("ix_model_registry_is_current", "model_registry") in created_indexes
    assert ("ix_model_registry_version", "model_registry") in created_indexes
    assert ("ix_risk_analyses_created_at", "risk_analyses") in created_indexes
    assert ("ix_risk_analyses_symbol", "risk_analyses") in created_indexes
    assert ("ix_risk_analyses_symbol_created_at", "risk_analyses") in created_indexes


def test_downgrade_drops_expected_tables_and_indexes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_migration_module()
    fake_op = FakeOp()
    monkeypatch.setattr(module, "op", fake_op)

    module.downgrade()

    dropped_indexes = [args[0] for kind, args, _ in fake_op.calls if kind == "drop_index"]
    assert "ix_risk_analyses_symbol_created_at" in dropped_indexes
    assert "ix_risk_analyses_symbol" in dropped_indexes
    assert "ix_risk_analyses_created_at" in dropped_indexes
    assert "ix_model_registry_version" in dropped_indexes
    assert "ix_model_registry_is_current" in dropped_indexes
    assert "ix_api_keys_name" in dropped_indexes
    assert "ix_api_keys_key_hash" in dropped_indexes

    dropped_tables = [args[0] for kind, args, _ in fake_op.calls if kind == "drop_table"]
    assert dropped_tables == ["risk_analyses", "model_registry", "api_keys"]
