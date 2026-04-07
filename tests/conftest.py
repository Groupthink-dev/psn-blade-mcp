"""Shared test fixtures for PSN Blade MCP."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest


class FakeTrophySet:
    """Mimics PSNAWP TrophySet dataclass."""

    def __init__(self, platinum: int = 0, gold: int = 0, silver: int = 0, bronze: int = 0) -> None:
        self.platinum = platinum
        self.gold = gold
        self.silver = silver
        self.bronze = bronze


class FakeTrophySummary:
    """Mimics PSNAWP TrophySummary dataclass."""

    def __init__(self) -> None:
        self.account_id = "1234567890"
        self.trophy_level = 350
        self.progress = 45
        self.tier = 5
        self.earned_trophies = FakeTrophySet(platinum=12, gold=85, silver=200, bronze=450)


class FakePlatformType:
    """Mimics PSNAWP PlatformType enum member."""

    def __init__(self, value: str = "PS5") -> None:
        self.value = value
        self.name = value

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FakePlatformType):
            return self.value == other.value
        return NotImplemented


class FakeTrophyType:
    """Mimics PSNAWP TrophyType enum member."""

    def __init__(self, name: str = "GOLD") -> None:
        self.name = name


class FakeTrophyRarity:
    """Mimics PSNAWP TrophyRarity enum member."""

    def __init__(self, name: str = "RARE") -> None:
        self.name = name


class FakePlatformCategory:
    """Mimics PSNAWP PlatformCategory enum member."""

    def __init__(self, value: str = "ps5_native_game") -> None:
        self.value = value


def make_trophy_title(
    title_name: str = "Astro Bot",
    np_communication_id: str = "NPWR12345_00",
    progress: int = 75,
) -> MagicMock:
    """Create a mock TrophyTitle."""
    title = MagicMock()
    title.title_name = title_name
    title.np_communication_id = np_communication_id
    title.title_platform = frozenset([FakePlatformType("PS5")])
    title.has_trophy_groups = True
    title.progress = progress
    title.hidden_flag = False
    title.earned_trophies = FakeTrophySet(platinum=1, gold=5, silver=10, bronze=20)
    title.defined_trophies = FakeTrophySet(platinum=1, gold=8, silver=15, bronze=25)
    title.last_updated_datetime = datetime(2026, 3, 15, 14, 30, tzinfo=UTC)
    return title


def make_trophy(
    trophy_id: int = 1,
    trophy_type: str = "GOLD",
    trophy_name: str = "First Steps",
    earned: bool = True,
) -> MagicMock:
    """Create a mock Trophy with progress."""
    trophy = MagicMock()
    trophy.trophy_id = trophy_id
    trophy.trophy_type = FakeTrophyType(trophy_type)
    trophy.trophy_name = trophy_name
    trophy.trophy_detail = "Complete the tutorial"
    trophy.trophy_hidden = False
    trophy.trophy_icon_url = "https://example.com/icon.png"
    trophy.trophy_group_id = "default"
    trophy.trophy_progress_target_value = None
    trophy.trophy_reward_name = None
    trophy.trophy_reward_img_url = None
    trophy.earned = earned
    trophy.progress = 100 if earned else 0
    trophy.progress_rate = 100 if earned else 0
    trophy.progressed_date_time = datetime(2026, 3, 10, 12, 0, tzinfo=UTC) if earned else None
    trophy.earned_date_time = datetime(2026, 3, 10, 12, 0, tzinfo=UTC) if earned else None
    trophy.trophy_rarity = FakeTrophyRarity("RARE")
    trophy.trophy_earn_rate = 15.5
    return trophy


def make_title_stats(
    name: str = "Astro Bot",
    title_id: str = "PPSA01234_00",
    play_count: int = 15,
    play_duration: timedelta | None = None,
) -> MagicMock:
    """Create a mock TitleStats."""
    stats = MagicMock()
    stats.name = name
    stats.title_id = title_id
    stats.category = FakePlatformCategory("ps5_native_game")
    stats.play_count = play_count
    stats.play_duration = play_duration or timedelta(hours=25, minutes=30)
    stats.last_played_date_time = datetime(2026, 4, 1, 20, 0, tzinfo=UTC)
    stats.first_played_date_time = datetime(2026, 1, 15, 10, 0, tzinfo=UTC)
    stats.image_url = "https://example.com/game.png"
    return stats


def make_user(online_id: str = "TestPlayer", account_id: str = "9876543210") -> MagicMock:
    """Create a mock User."""
    user = MagicMock()
    user.online_id = online_id
    user.account_id = account_id
    return user


@pytest.fixture
def trophy_summary() -> FakeTrophySummary:
    return FakeTrophySummary()


@pytest.fixture
def trophy_title() -> MagicMock:
    return make_trophy_title()


@pytest.fixture
def trophy() -> MagicMock:
    return make_trophy()


@pytest.fixture
def title_stats() -> MagicMock:
    return make_title_stats()


@pytest.fixture
def mock_user() -> MagicMock:
    return make_user()
