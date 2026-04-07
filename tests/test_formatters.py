"""Tests for PSN Blade MCP formatters."""

from __future__ import annotations

from datetime import datetime, timedelta

from psn_blade_mcp.formatters import (
    fmt_datetime,
    fmt_device,
    fmt_duration,
    fmt_entitlement,
    fmt_friend,
    fmt_group_info,
    fmt_message,
    fmt_presence,
    fmt_profile,
    fmt_search_game,
    fmt_search_user,
    fmt_title_stats,
    fmt_trophy,
    fmt_trophy_group,
    fmt_trophy_summary,
    fmt_trophy_title,
)
from tests.conftest import (
    FakeTrophySet,
    make_trophy,
    make_trophy_title,
)


class TestFmtProfile:
    def test_basic_profile(self) -> None:
        profile: dict = {"aboutMe": "Hello world", "isPlus": True}
        result = fmt_profile(profile, "12345", "TestUser")
        assert "TestUser" in result
        assert "account=12345" in result
        assert "PS Plus: True" in result
        assert "Hello world" in result

    def test_empty_profile(self) -> None:
        result = fmt_profile({}, "12345", "TestUser")
        assert "TestUser" in result
        assert "account=12345" in result


class TestFmtTrophySummary:
    def test_formats_all_fields(self, trophy_summary) -> None:  # type: ignore[no-untyped-def]
        result = fmt_trophy_summary(trophy_summary)
        assert "Level 350" in result
        assert "tier 5" in result
        assert "45%" in result
        assert "P:12" in result
        assert "G:85" in result
        assert "S:200" in result
        assert "B:450" in result


class TestFmtTrophyTitle:
    def test_formats_title(self, trophy_title) -> None:  # type: ignore[no-untyped-def]
        result = fmt_trophy_title(trophy_title)
        assert "Astro Bot" in result
        assert "PS5" in result
        assert "75%" in result
        assert "NPWR12345_00" in result
        assert "P:1/1" in result

    def test_no_progress(self) -> None:
        title = make_trophy_title(progress=None)
        result = fmt_trophy_title(title)
        assert "?" in result


class TestFmtTrophy:
    def test_with_progress(self, trophy) -> None:  # type: ignore[no-untyped-def]
        result = fmt_trophy(trophy, with_progress=True)
        assert "#1 GOLD" in result
        assert "First Steps" in result
        assert "EARNED" in result
        assert "RARE" in result
        assert "15.5%" in result

    def test_without_progress(self, trophy) -> None:  # type: ignore[no-untyped-def]
        result = fmt_trophy(trophy, with_progress=False)
        assert "#1 GOLD" in result
        assert "First Steps" in result
        assert "EARNED" not in result

    def test_locked_trophy(self) -> None:
        trophy = make_trophy(earned=False)
        result = fmt_trophy(trophy, with_progress=True)
        assert "locked" in result

    def test_hidden_trophy(self) -> None:
        trophy = make_trophy()
        trophy.trophy_hidden = True
        result = fmt_trophy(trophy)
        assert "[hidden]" in result


class TestFmtTrophyGroup:
    def test_basic_group(self) -> None:
        group = type(
            "G",
            (),
            {
                "trophy_group_id": "default",
                "trophy_group_name": "Base Game",
                "defined_trophies": FakeTrophySet(1, 5, 10, 20),
            },
        )()
        result = fmt_trophy_group(group)
        assert "default: Base Game" in result
        assert "P:1" in result

    def test_with_progress(self) -> None:
        group = type(
            "G",
            (),
            {
                "trophy_group_id": "001",
                "trophy_group_name": "DLC Pack 1",
                "defined_trophies": FakeTrophySet(0, 2, 3, 5),
                "progress": 60,
                "earned_trophies": FakeTrophySet(0, 1, 2, 3),
            },
        )()
        result = fmt_trophy_group(group, with_progress=True)
        assert "DLC Pack 1" in result
        assert "60%" in result


class TestFmtTitleStats:
    def test_formats_all_fields(self, title_stats) -> None:  # type: ignore[no-untyped-def]
        result = fmt_title_stats(title_stats)
        assert "Astro Bot" in result
        assert "plays=15" in result
        assert "25h30m" in result
        assert "PPSA01234_00" in result


class TestFmtFriend:
    def test_formats_friend(self, mock_user) -> None:  # type: ignore[no-untyped-def]
        result = fmt_friend(mock_user)
        assert "TestPlayer" in result
        assert "account=9876543210" in result


class TestFmtPresence:
    def test_online_playing(self) -> None:
        presence = {
            "availability": "availableToPlay",
            "primaryPlatformInfo": {"platform": "PS5"},
            "gameTitleInfoList": [{"titleName": "Elden Ring"}],
        }
        result = fmt_presence(presence)
        assert "availableToPlay" in result
        assert "PS5" in result
        assert "Elden Ring" in result

    def test_offline(self) -> None:
        result = fmt_presence({"availability": "unavailable"})
        assert "unavailable" in result


class TestFmtDevice:
    def test_formats_device(self) -> None:
        result = fmt_device({"deviceType": "PS5", "deviceId": "abc123"})
        assert "PS5" in result
        assert "abc123" in result


class TestFmtSearchUser:
    def test_dict_result(self) -> None:
        result = fmt_search_user({"result": {"onlineId": "CoolPlayer", "accountId": "111", "isPsPlus": True}})
        assert "CoolPlayer" in result
        assert "[PS+]" in result

    def test_non_plus(self) -> None:
        result = fmt_search_user({"result": {"onlineId": "BasicPlayer", "accountId": "222", "isPsPlus": False}})
        assert "BasicPlayer" in result
        assert "[PS+]" not in result


class TestFmtSearchGame:
    def test_dict_result(self) -> None:
        result = fmt_search_game({"result": {"name": "God of War", "platforms": ["PS5", "PS4"]}})
        assert "God of War" in result
        assert "PS5,PS4" in result


class TestFmtEntitlement:
    def test_owned(self) -> None:
        result = fmt_entitlement(
            {
                "gameMeta": {"name": "Spider-Man 2"},
                "isSubscription": False,
                "activeFlag": True,
            }
        )
        assert "Spider-Man 2" in result
        assert "owned" in result
        assert "active" in result


class TestFmtGroupInfo:
    def test_formats_group(self) -> None:
        result = fmt_group_info(
            {
                "groupName": {"value": "Squad"},
                "groupId": "g123",
                "members": [{"onlineId": "Alice"}, {"onlineId": "Bob"}],
                "modifiedTimestamp": "2026-04-01",
            }
        )
        assert "Squad" in result
        assert "g123" in result
        assert "Alice" in result


class TestFmtMessage:
    def test_formats_message(self) -> None:
        result = fmt_message(
            {
                "senderOnlineId": "Alice",
                "body": "Hey!",
                "createdTimestamp": "2026-04-01T12:00:00Z",
            }
        )
        assert "Alice" in result
        assert "Hey!" in result


class TestFmtHelpers:
    def test_datetime_none(self) -> None:
        assert fmt_datetime(None) == "?"

    def test_datetime_value(self) -> None:
        dt = datetime(2026, 3, 15, 14, 30)
        assert fmt_datetime(dt) == "2026-03-15 14:30"

    def test_duration_none(self) -> None:
        assert fmt_duration(None) == "?"

    def test_duration_hours(self) -> None:
        assert fmt_duration(timedelta(hours=5, minutes=30)) == "5h30m"

    def test_duration_minutes_only(self) -> None:
        assert fmt_duration(timedelta(minutes=45)) == "45m"
