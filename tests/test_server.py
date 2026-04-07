"""Tests for PSN Blade MCP server tools.

Uses mocked PSNClient to test tool logic and formatting without live API calls.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from psn_blade_mcp.server import (
    psn_devices,
    psn_friend_accept,
    psn_friend_remove,
    psn_friends,
    psn_games,
    psn_games_recent,
    psn_presence,
    psn_profile,
    psn_search_users,
    psn_send_message,
    psn_trophies,
    psn_trophy_summary,
)
from tests.conftest import FakeTrophySummary, make_title_stats, make_trophy, make_user


@pytest.fixture(autouse=True)
def reset_client() -> None:
    """Reset the singleton client before each test."""
    import psn_blade_mcp.server as srv

    srv._client = None


def _mock_client() -> MagicMock:
    """Create a mock PSNClient."""
    from psn_blade_mcp.client import PSNClient

    client = MagicMock(spec=PSNClient)
    return client


class TestPsnProfile:
    async def test_own_profile(self) -> None:
        client = _mock_client()
        client.get_profile.return_value = ({"aboutMe": "Hi"}, "123", "MyUser")

        with patch("psn_blade_mcp.server._get_client", return_value=client):
            result = await psn_profile()
            assert "MyUser" in result
            assert "account=123" in result

    async def test_other_profile(self) -> None:
        client = _mock_client()
        client.get_profile.return_value = ({"isPlus": True}, "456", "OtherUser")

        with patch("psn_blade_mcp.server._get_client", return_value=client):
            result = await psn_profile(online_id="OtherUser")
            assert "OtherUser" in result

    async def test_profile_error(self) -> None:
        from psn_blade_mcp.client import PSNClientError

        client = _mock_client()
        client.get_profile.side_effect = PSNClientError("User not found: ghost")

        with patch("psn_blade_mcp.server._get_client", return_value=client):
            result = await psn_profile(online_id="ghost")
            assert "Error" in result
            assert "not found" in result


class TestPsnTrophySummary:
    async def test_own_summary(self) -> None:
        client = _mock_client()
        client.get_trophy_summary.return_value = FakeTrophySummary()

        with patch("psn_blade_mcp.server._get_client", return_value=client):
            result = await psn_trophy_summary()
            assert "Level 350" in result
            assert "P:12" in result


class TestPsnTrophies:
    async def test_list_trophies(self) -> None:
        client = _mock_client()
        client.get_trophies.return_value = [
            make_trophy(1, "GOLD", "First Steps"),
            make_trophy(2, "BRONZE", "Collected 10"),
        ]

        with patch("psn_blade_mcp.server._get_client", return_value=client):
            result = await psn_trophies(np_communication_id="NPWR12345_00")
            assert "Trophies (2)" in result
            assert "First Steps" in result
            assert "Collected 10" in result

    async def test_empty_trophies(self) -> None:
        client = _mock_client()
        client.get_trophies.return_value = []

        with patch("psn_blade_mcp.server._get_client", return_value=client):
            result = await psn_trophies(np_communication_id="NPWR99999_00")
            assert "No trophies found" in result


class TestPsnFriends:
    async def test_list_friends(self) -> None:
        client = _mock_client()
        client.get_friends.return_value = [make_user("Alice", "111"), make_user("Bob", "222")]

        with patch("psn_blade_mcp.server._get_client", return_value=client):
            result = await psn_friends()
            assert "Friends (2)" in result
            assert "Alice" in result
            assert "Bob" in result

    async def test_no_friends(self) -> None:
        client = _mock_client()
        client.get_friends.return_value = []

        with patch("psn_blade_mcp.server._get_client", return_value=client):
            result = await psn_friends()
            assert "No friends found" in result


class TestPsnPresence:
    async def test_online(self) -> None:
        client = _mock_client()
        client.get_presence.return_value = {
            "availability": "availableToPlay",
            "primaryPlatformInfo": {"platform": "PS5"},
            "gameTitleInfoList": [{"titleName": "Elden Ring"}],
        }

        with patch("psn_blade_mcp.server._get_client", return_value=client):
            result = await psn_presence(online_id="TestUser")
            assert "TestUser" in result
            assert "availableToPlay" in result
            assert "Elden Ring" in result


class TestPsnGames:
    async def test_list_games(self) -> None:
        client = _mock_client()
        client.get_title_stats.return_value = [make_title_stats("Astro Bot"), make_title_stats("Elden Ring")]

        with patch("psn_blade_mcp.server._get_client", return_value=client):
            result = await psn_games()
            assert "Games (2)" in result
            assert "Astro Bot" in result
            assert "Elden Ring" in result


class TestPsnGamesRecent:
    async def test_recent(self) -> None:
        client = _mock_client()
        client.get_title_stats.return_value = [make_title_stats("Recent Game")]

        with patch("psn_blade_mcp.server._get_client", return_value=client):
            result = await psn_games_recent()
            assert "Recent games" in result
            assert "Recent Game" in result


class TestPsnDevices:
    async def test_list_devices(self) -> None:
        client = _mock_client()
        client.get_devices.return_value = [{"deviceType": "PS5", "deviceId": "abc"}]

        with patch("psn_blade_mcp.server._get_client", return_value=client):
            result = await psn_devices()
            assert "Devices (1)" in result
            assert "PS5" in result


class TestPsnSearchUsers:
    async def test_search(self) -> None:
        client = _mock_client()
        client.search_users.return_value = [{"result": {"onlineId": "Found", "accountId": "999", "isPsPlus": False}}]

        with patch("psn_blade_mcp.server._get_client", return_value=client):
            result = await psn_search_users(query="Found")
            assert "Found" in result


class TestWriteGatedTools:
    async def test_send_message_blocked(self) -> None:
        with patch.dict(os.environ, {"PSN_WRITE_ENABLED": "false"}):
            result = await psn_send_message(group_id="g1", message="hi")
            assert "disabled" in result.lower()

    async def test_send_message_allowed(self) -> None:
        client = _mock_client()
        client.send_message.return_value = {"messageUid": "msg123"}

        with (
            patch.dict(os.environ, {"PSN_WRITE_ENABLED": "true"}),
            patch("psn_blade_mcp.server._get_client", return_value=client),
        ):
            result = await psn_send_message(group_id="g1", message="hi")
            assert "msg123" in result

    async def test_friend_accept_blocked(self) -> None:
        with patch.dict(os.environ, {"PSN_WRITE_ENABLED": "false"}):
            result = await psn_friend_accept(online_id="Someone")
            assert "disabled" in result.lower()

    async def test_friend_remove_blocked(self) -> None:
        with patch.dict(os.environ, {"PSN_WRITE_ENABLED": "false"}):
            result = await psn_friend_remove(online_id="Someone")
            assert "disabled" in result.lower()
