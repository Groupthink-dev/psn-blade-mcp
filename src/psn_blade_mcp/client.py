"""PSN API client wrapper around PSNAWP.

Handles authentication, token lifecycle, and provides typed access
to PSN endpoints. Lazy-initialized singleton pattern.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from psnawp_api import PSNAWP
from psnawp_api.core.psnawp_exceptions import (
    PSNAWPAuthenticationError,
    PSNAWPError,
    PSNAWPForbiddenError,
    PSNAWPNotFoundError,
    PSNAWPTooManyRequestsError,
)
from psnawp_api.models.search import SearchDomain
from psnawp_api.models.trophies.trophy_constants import PlatformType

logger = logging.getLogger(__name__)


class PSNClientError(Exception):
    """Wrapper for PSN API errors with user-friendly messages."""

    def __init__(self, message: str, cause: PSNAWPError | None = None) -> None:
        self.cause = cause
        super().__init__(message)


def _map_platform(platform: str) -> PlatformType:
    """Map platform string to PSNAWP PlatformType enum."""
    mapping = {
        "ps5": PlatformType.PS5,
        "ps4": PlatformType.PS4,
        "ps3": PlatformType.PS3,
        "psvita": PlatformType.PS_VITA,
        "vita": PlatformType.PS_VITA,
        "pspc": PlatformType.PSPC,
        "pc": PlatformType.PSPC,
    }
    return mapping.get(platform.lower(), PlatformType.PS5)


def _map_search_domain(domain: str) -> SearchDomain:
    """Map search domain string to PSNAWP SearchDomain enum."""
    mapping = {
        "games": SearchDomain.FULL_GAMES,
        "addons": SearchDomain.ADD_ONS,
        "users": SearchDomain.USERS,
    }
    return mapping.get(domain.lower(), SearchDomain.FULL_GAMES)


class PSNClient:
    """Wrapper around PSNAWP providing typed, error-handled access to PSN APIs."""

    def __init__(self) -> None:
        npsso = os.environ.get("PSN_NPSSO", "")
        if not npsso:
            raise PSNClientError("PSN_NPSSO environment variable not set")
        try:
            self._api = PSNAWP(npsso)
            self._client = self._api.me()
        except PSNAWPAuthenticationError as e:
            raise PSNClientError(
                "Authentication failed — NPSSO token may be expired. "
                "Visit https://ca.account.sony.com/api/v1/ssocookie to get a fresh token.",
                cause=e,
            ) from e
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to initialize PSN client: {e}", cause=e) from e

    def get_profile(self, online_id: str | None = None) -> tuple[dict[str, Any], str, str]:
        """Get user profile. Returns (profile_dict, account_id, online_id)."""
        try:
            if online_id:
                user = self._api.user(online_id=online_id)
                profile = user.profile()
                return profile, user.account_id, user.online_id
            else:
                profile = self._client.get_profile_legacy()
                return profile, self._client.account_id, self._client.online_id
        except PSNAWPNotFoundError as e:
            raise PSNClientError(f"User not found: {online_id}", cause=e) from e
        except PSNAWPForbiddenError as e:
            raise PSNClientError(f"Profile is private: {online_id}", cause=e) from e
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to get profile: {e}", cause=e) from e

    def get_trophy_summary(self, online_id: str | None = None) -> Any:
        """Get overall trophy summary for a user."""
        try:
            if online_id:
                user = self._api.user(online_id=online_id)
                return user.trophy_summary()
            return self._client.trophy_summary()
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to get trophy summary: {e}", cause=e) from e

    def get_trophy_titles(self, online_id: str | None = None, limit: int = 50) -> list[Any]:
        """Get trophy titles (games with trophies) for a user."""
        try:
            if online_id:
                user = self._api.user(online_id=online_id)
                return list(user.trophy_titles(limit=limit))
            return list(self._client.trophy_titles(limit=limit))
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to get trophy titles: {e}", cause=e) from e

    def get_trophies(
        self,
        np_communication_id: str,
        platform: str = "ps5",
        online_id: str | None = None,
        include_progress: bool = True,
        trophy_group_id: str = "default",
        limit: int = 200,
    ) -> list[Any]:
        """Get trophies for a specific game."""
        try:
            plat = _map_platform(platform)
            if online_id:
                user = self._api.user(online_id=online_id)
                if include_progress:
                    return list(
                        user.trophies(
                            np_communication_id=np_communication_id,
                            platform=plat,
                            include_progress=True,
                            trophy_group_id=trophy_group_id,
                            limit=limit,
                        )
                    )
                return list(
                    user.trophies(
                        np_communication_id=np_communication_id,
                        platform=plat,
                        include_progress=False,
                        trophy_group_id=trophy_group_id,
                        limit=limit,
                    )
                )
            if include_progress:
                return list(
                    self._client.trophies(
                        np_communication_id=np_communication_id,
                        platform=plat,
                        include_progress=True,
                        trophy_group_id=trophy_group_id,
                        limit=limit,
                    )
                )
            return list(
                self._client.trophies(
                    np_communication_id=np_communication_id,
                    platform=plat,
                    include_progress=False,
                    trophy_group_id=trophy_group_id,
                    limit=limit,
                )
            )
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to get trophies: {e}", cause=e) from e

    def get_trophy_groups(
        self,
        np_communication_id: str,
        platform: str = "ps5",
        online_id: str | None = None,
        include_progress: bool = True,
    ) -> Any:
        """Get trophy group summaries (base game + DLC) for a title."""
        try:
            plat = _map_platform(platform)
            if online_id:
                user = self._api.user(online_id=online_id)
                if include_progress:
                    return user.trophy_groups_summary(
                        np_communication_id=np_communication_id,
                        platform=plat,
                        include_progress=True,
                    )
                return user.trophy_groups_summary(
                    np_communication_id=np_communication_id,
                    platform=plat,
                    include_progress=False,
                )
            if include_progress:
                return self._client.trophy_groups_summary(
                    np_communication_id=np_communication_id,
                    platform=plat,
                    include_progress=True,
                )
            return self._client.trophy_groups_summary(
                np_communication_id=np_communication_id,
                platform=plat,
                include_progress=False,
            )
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to get trophy groups: {e}", cause=e) from e

    def get_title_stats(self, online_id: str | None = None, limit: int = 25) -> list[Any]:
        """Get game library with playtime stats."""
        try:
            if online_id:
                user = self._api.user(online_id=online_id)
                return list(user.title_stats(limit=limit))
            return list(self._client.title_stats(limit=limit))
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to get title stats: {e}", cause=e) from e

    def get_friends(self, limit: int = 50) -> list[Any]:
        """Get friends list for authenticated user."""
        try:
            return list(self._client.friends_list(limit=limit))
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to get friends: {e}", cause=e) from e

    def get_presence(self, online_id: str) -> dict[str, Any]:
        """Get presence (online/in-game status) for a user."""
        try:
            user = self._api.user(online_id=online_id)
            return user.get_presence()
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to get presence: {e}", cause=e) from e

    def get_devices(self) -> list[dict[str, Any]]:
        """Get registered account devices."""
        try:
            return self._client.get_account_devices()
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to get devices: {e}", cause=e) from e

    def get_entitlements(self, limit: int = 25) -> list[Any]:
        """Get game entitlements (purchased games) for authenticated user."""
        try:
            return list(self._client.game_entitlements(limit=limit))
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to get entitlements: {e}", cause=e) from e

    def get_game_details(self, title_id: str, platform: str = "ps5") -> list[dict[str, Any]]:
        """Get game title details."""
        try:
            plat = _map_platform(platform)
            game = self._api.game_title(title_id=title_id, platform=plat)
            return game.get_details()
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to get game details: {e}", cause=e) from e

    def search_users(self, query: str, limit: int = 10) -> list[Any]:
        """Search for PSN users."""
        try:
            return list(self._api.search(query, SearchDomain.USERS, limit=limit))
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to search users: {e}", cause=e) from e

    def search_games(self, query: str, limit: int = 10) -> list[Any]:
        """Search PlayStation Store for games."""
        try:
            return list(self._api.search(query, SearchDomain.FULL_GAMES, limit=limit))
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to search games: {e}", cause=e) from e

    def send_message(self, group_id: str, message: str) -> Any:
        """Send a message to a group."""
        try:
            group = self._api.group(group_id=group_id)
            return group.send_message(message)
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to send message: {e}", cause=e) from e

    def accept_friend(self, online_id: str) -> None:
        """Accept a friend request."""
        try:
            user = self._api.user(online_id=online_id)
            user.accept_friend_request()
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to accept friend request: {e}", cause=e) from e

    def remove_friend(self, online_id: str) -> None:
        """Remove a friend."""
        try:
            user = self._api.user(online_id=online_id)
            user.remove_friend()
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to remove friend: {e}", cause=e) from e

    def get_groups(self, limit: int = 20) -> list[Any]:
        """Get message groups for authenticated user."""
        try:
            return list(self._client.get_groups(limit=limit))
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to get groups: {e}", cause=e) from e

    def get_conversation(self, group_id: str, limit: int = 20) -> dict[str, Any]:
        """Get messages from a group conversation."""
        try:
            group = self._api.group(group_id=group_id)
            return group.get_conversation(limit=limit)
        except PSNAWPTooManyRequestsError as e:
            raise PSNClientError(
                "Rate limited by PSN — wait a few minutes before retrying.",
                cause=e,
            ) from e
        except PSNAWPError as e:
            raise PSNClientError(f"Failed to get conversation: {e}", cause=e) from e
