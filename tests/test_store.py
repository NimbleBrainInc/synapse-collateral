"""Unit tests for store.py — data directory resolution and patch_source coercion."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestResolveBaseDir:
    """_resolve_base_dir picks UPJACK_ROOT when set, else ~/.collateral."""

    def test_defaults_to_home_collateral(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("UPJACK_ROOT", raising=False)
        from mcp_collateral.store import _resolve_base_dir

        result = _resolve_base_dir()
        assert result == Path.home() / ".collateral"

    def test_uses_upjack_root_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("UPJACK_ROOT", "/tmp/test-data")
        from mcp_collateral.store import _resolve_base_dir

        result = _resolve_base_dir()
        assert result == Path("/tmp/test-data")

    def test_ignores_empty_upjack_root(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("UPJACK_ROOT", "")
        from mcp_collateral.store import _resolve_base_dir

        result = _resolve_base_dir()
        assert result == Path.home() / ".collateral"


class TestMigrateLegacyDir:
    """Legacy migration only runs in standalone mode (no UPJACK_ROOT)."""

    def test_skips_migration_when_upjack_root_set(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        legacy = tmp_path / ".typst-pdf"
        legacy.mkdir()
        target = tmp_path / ".collateral"

        monkeypatch.setenv("UPJACK_ROOT", str(tmp_path / "data"))
        monkeypatch.setattr("mcp_collateral.store.BASE_DIR", target)

        from mcp_collateral.store import _migrate_legacy_dir

        _migrate_legacy_dir()
        assert legacy.exists()  # not moved
        assert not target.exists()

    def test_runs_migration_when_standalone(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        legacy = tmp_path / ".typst-pdf"
        legacy.mkdir()
        (legacy / "test.txt").write_text("hello")
        target = tmp_path / ".collateral"

        monkeypatch.delenv("UPJACK_ROOT", raising=False)
        monkeypatch.setattr("mcp_collateral.store.BASE_DIR", target)
        # Patch Path.home() to return tmp_path so legacy dir is found
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        from mcp_collateral.store import _migrate_legacy_dir

        _migrate_legacy_dir()
        assert not legacy.exists()
        assert target.exists()
        assert (target / "test.txt").read_text() == "hello"
