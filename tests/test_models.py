"""Tests for PSN Blade MCP models."""

from __future__ import annotations

import os
from unittest.mock import patch

from psn_blade_mcp.models import (
    DEFAULT_FRIEND_LIMIT,
    DEFAULT_GAME_LIMIT,
    DEFAULT_TROPHY_LIMIT,
    is_write_enabled,
    require_write,
)


class TestWriteGate:
    def test_disabled_by_default(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            assert is_write_enabled() is False
            assert require_write() is not None
            assert "disabled" in require_write().lower()  # type: ignore[union-attr]

    def test_enabled_true(self) -> None:
        with patch.dict(os.environ, {"PSN_WRITE_ENABLED": "true"}):
            assert is_write_enabled() is True
            assert require_write() is None

    def test_enabled_case_insensitive(self) -> None:
        with patch.dict(os.environ, {"PSN_WRITE_ENABLED": "True"}):
            assert is_write_enabled() is True

    def test_enabled_false(self) -> None:
        with patch.dict(os.environ, {"PSN_WRITE_ENABLED": "false"}):
            assert is_write_enabled() is False
            assert require_write() is not None


class TestDefaults:
    def test_limits_are_positive(self) -> None:
        assert DEFAULT_TROPHY_LIMIT > 0
        assert DEFAULT_GAME_LIMIT > 0
        assert DEFAULT_FRIEND_LIMIT > 0
