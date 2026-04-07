"""Shared constants, types, and write-gate for PSN Blade MCP."""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

# Default limits for list operations (token efficiency)
DEFAULT_TROPHY_LIMIT = 50
DEFAULT_GAME_LIMIT = 25
DEFAULT_FRIEND_LIMIT = 50
DEFAULT_MESSAGE_LIMIT = 20
DEFAULT_SEARCH_LIMIT = 10

# Platform display names
PLATFORM_NAMES: dict[str, str] = {
    "PS5": "PS5",
    "PS4": "PS4",
    "PS3": "PS3",
    "PSVITA": "PS Vita",
    "PSPC": "PS PC",
}


def is_write_enabled() -> bool:
    """Check if write operations are enabled via env var."""
    return os.environ.get("PSN_WRITE_ENABLED", "").lower() == "true"


def require_write() -> str | None:
    """Return error message if writes disabled, else None."""
    if not is_write_enabled():
        return "Error: Write operations are disabled. Set PSN_WRITE_ENABLED=true to enable."
    return None
