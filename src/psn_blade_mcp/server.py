"""PSN Blade MCP Server — PlayStation Network tools for Sidereal.

Wraps PSNAWP to expose PSN trophies, game library, friends, presence,
and messaging as MCP tools. Token-efficient compact text output.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from psn_blade_mcp.client import PSNClient, PSNClientError
from psn_blade_mcp.formatters import (
    fmt_device,
    fmt_entitlement,
    fmt_friend,
    fmt_presence,
    fmt_profile,
    fmt_search_game,
    fmt_search_user,
    fmt_title_stats,
    fmt_trophy,
    fmt_trophy_group,
    fmt_trophy_summary,
)
from psn_blade_mcp.models import (
    DEFAULT_FRIEND_LIMIT,
    DEFAULT_GAME_LIMIT,
    DEFAULT_SEARCH_LIMIT,
    require_write,
)

logger = logging.getLogger(__name__)

# Transport configuration
TRANSPORT = os.environ.get("PSN_MCP_TRANSPORT", "stdio")
HTTP_HOST = os.environ.get("PSN_MCP_HOST", "127.0.0.1")
HTTP_PORT = int(os.environ.get("PSN_MCP_PORT", "8780"))

mcp = FastMCP(
    "psn-blade-mcp",
    instructions=(
        "PlayStation Network MCP server. Provides trophy tracking, game library, "
        "friends, presence, and messaging via unofficial PSN API. "
        "All output is compact text for token efficiency. "
        "Write operations (messaging, friend management) require PSN_WRITE_ENABLED=true."
    ),
)

_client: PSNClient | None = None


def _get_client() -> PSNClient:
    """Get or create the PSN client singleton."""
    global _client
    if _client is None:
        _client = PSNClient()
    return _client


def _error(e: PSNClientError) -> str:
    """Format error as user-friendly string."""
    return f"Error: {e}"


async def _run(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """Run blocking PSNAWP method in thread to avoid blocking event loop."""
    return await asyncio.to_thread(fn, *args, **kwargs)


# ---------------------------------------------------------------------------
# Profile & Social (contract: required/recommended)
# ---------------------------------------------------------------------------


@mcp.tool()
async def psn_profile(
    online_id: Annotated[str | None, Field(description="PSN online ID. Omit for your own profile.")] = None,
) -> str:
    """Get a PSN user profile — display name, avatar, PS Plus status.

    Returns compact profile summary. Omit online_id to get your own profile.
    """
    try:
        profile, account_id, oid = await _run(_get_client().get_profile, online_id)
        return fmt_profile(profile, account_id, oid)
    except PSNClientError as e:
        return _error(e)


@mcp.tool()
async def psn_friends(
    limit: Annotated[int, Field(description="Max friends to return")] = DEFAULT_FRIEND_LIMIT,
) -> str:
    """List your PSN friends.

    Returns compact list: online_id (account=id) per line.
    """
    try:
        friends = await _run(_get_client().get_friends, limit)
        if not friends:
            return "No friends found."
        lines = [fmt_friend(f) for f in friends]
        return f"Friends ({len(lines)}):\n" + "\n".join(lines)
    except PSNClientError as e:
        return _error(e)


@mcp.tool()
async def psn_presence(
    online_id: Annotated[str, Field(description="PSN online ID to check")],
) -> str:
    """Get online/offline/in-game presence for a PSN user."""
    try:
        presence = await _run(_get_client().get_presence, online_id)
        return f"{online_id}: {fmt_presence(presence)}"
    except PSNClientError as e:
        return _error(e)


@mcp.tool()
async def psn_search_users(
    query: Annotated[str, Field(description="Search query (display name or online ID)")],
    limit: Annotated[int, Field(description="Max results")] = DEFAULT_SEARCH_LIMIT,
) -> str:
    """Search for PSN users by name.

    Returns compact list of matching users with PS Plus status.
    """
    try:
        results = await _run(_get_client().search_users, query, limit)
        if not results:
            return f"No users found for '{query}'."
        lines = [fmt_search_user(r) for r in results]
        return f"Users matching '{query}' ({len(lines)}):\n" + "\n".join(lines)
    except PSNClientError as e:
        return _error(e)


@mcp.tool()
async def psn_devices() -> str:
    """List registered PlayStation devices on your account."""
    try:
        devices = await _run(_get_client().get_devices)
        if not devices:
            return "No devices registered."
        lines = [fmt_device(d) for d in devices]
        return f"Devices ({len(lines)}):\n" + "\n".join(lines)
    except PSNClientError as e:
        return _error(e)


# ---------------------------------------------------------------------------
# Trophies / Achievements (contract: required)
# ---------------------------------------------------------------------------


@mcp.tool()
async def psn_trophy_summary(
    online_id: Annotated[str | None, Field(description="PSN online ID. Omit for your own.")] = None,
) -> str:
    """Get overall trophy level, points, and tier breakdown.

    Returns: level, tier, progress %, and earned counts by type (P/G/S/B).
    """
    try:
        summary = await _run(_get_client().get_trophy_summary, online_id)
        label = online_id or "You"
        return f"{label}: {fmt_trophy_summary(summary)}"
    except PSNClientError as e:
        return _error(e)


@mcp.tool()
async def psn_trophies(
    np_communication_id: Annotated[str, Field(description="Trophy set ID (e.g. NPWR12345_00)")],
    platform: Annotated[str, Field(description="Platform: ps5, ps4, ps3, psvita, pspc")] = "ps5",
    online_id: Annotated[str | None, Field(description="PSN online ID. Omit for your own.")] = None,
    trophy_group_id: Annotated[
        str, Field(description="Trophy group: 'default' for base, 'all' for everything")
    ] = "default",
    limit: Annotated[int, Field(description="Max trophies to return")] = 200,
) -> str:
    """List trophies for a specific game with earned/locked status.

    Use psn_trophy_summary first to find np_communication_id values.
    Returns compact list with trophy type, name, rarity, and earn date.
    """
    try:
        trophies = await _run(
            _get_client().get_trophies,
            np_communication_id,
            platform,
            online_id,
            True,
            trophy_group_id,
            limit,
        )
        if not trophies:
            return "No trophies found."
        lines = [fmt_trophy(t, with_progress=True) for t in trophies]
        return f"Trophies ({len(lines)}):\n" + "\n".join(lines)
    except PSNClientError as e:
        return _error(e)


@mcp.tool()
async def psn_trophy_compare(
    np_communication_id: Annotated[str, Field(description="Trophy set ID (e.g. NPWR12345_00)")],
    online_id: Annotated[str, Field(description="PSN online ID to compare against")],
    platform: Annotated[str, Field(description="Platform: ps5, ps4, ps3, psvita, pspc")] = "ps5",
) -> str:
    """Compare your trophy progress with another user for a specific game.

    Shows side-by-side earned status for each trophy.
    """
    try:
        client = _get_client()
        my_trophies, their_trophies = await asyncio.gather(
            _run(client.get_trophies, np_communication_id, platform, None, True),
            _run(client.get_trophies, np_communication_id, platform, online_id, True),
        )

        their_map = {t.trophy_id: t for t in their_trophies}
        lines = []
        for my_t in my_trophies:
            my_status = "Y" if getattr(my_t, "earned", False) else "-"
            their_t = their_map.get(my_t.trophy_id)
            their_status = "Y" if (their_t and getattr(their_t, "earned", False)) else "-"
            trophy_type = my_t.trophy_type.name if my_t.trophy_type else "?"
            lines.append(f"  #{my_t.trophy_id} {trophy_type} {my_t.trophy_name} | you={my_status} them={their_status}")

        header = f"Trophy comparison for {np_communication_id} vs {online_id}:"
        return header + "\n" + "\n".join(lines)
    except PSNClientError as e:
        return _error(e)


@mcp.tool()
async def psn_trophy_groups(
    np_communication_id: Annotated[str, Field(description="Trophy set ID (e.g. NPWR12345_00)")],
    platform: Annotated[str, Field(description="Platform: ps5, ps4, ps3, psvita, pspc")] = "ps5",
    online_id: Annotated[str | None, Field(description="PSN online ID. Omit for your own.")] = None,
) -> str:
    """Get trophy groups (base game + DLC) with completion progress.

    Shows defined and earned trophy counts per group.
    """
    try:
        groups = await _run(
            _get_client().get_trophy_groups,
            np_communication_id,
            platform,
            online_id,
        )
        lines = [f"Title: {groups.trophy_title_name}"]
        for g in groups.trophy_groups:
            lines.append(fmt_trophy_group(g, with_progress=True))
        return "\n".join(lines)
    except PSNClientError as e:
        return _error(e)


# ---------------------------------------------------------------------------
# Games (contract: required/recommended)
# ---------------------------------------------------------------------------


@mcp.tool()
async def psn_games(
    online_id: Annotated[str | None, Field(description="PSN online ID. Omit for your own.")] = None,
    limit: Annotated[int, Field(description="Max games to return")] = DEFAULT_GAME_LIMIT,
) -> str:
    """List game library with playtime, play count, and dates.

    Returns compact list sorted by last played.
    """
    try:
        stats = await _run(_get_client().get_title_stats, online_id, limit)
        if not stats:
            return "No games found."
        lines = [fmt_title_stats(s) for s in stats]
        return f"Games ({len(lines)}):\n" + "\n".join(lines)
    except PSNClientError as e:
        return _error(e)


@mcp.tool()
async def psn_games_recent(
    online_id: Annotated[str | None, Field(description="PSN online ID. Omit for your own.")] = None,
    limit: Annotated[int, Field(description="Max games to return")] = 10,
) -> str:
    """List recently played games ordered by last session.

    Compact view focused on recency — name, platform, last played, playtime.
    """
    try:
        stats = await _run(_get_client().get_title_stats, online_id, limit)
        if not stats:
            return "No recent games."
        # title_stats comes sorted by last played from the API
        lines = [fmt_title_stats(s) for s in stats[:limit]]
        return f"Recent games ({len(lines)}):\n" + "\n".join(lines)
    except PSNClientError as e:
        return _error(e)


@mcp.tool()
async def psn_entitlements(
    limit: Annotated[int, Field(description="Max entitlements to return")] = DEFAULT_GAME_LIMIT,
) -> str:
    """List your purchased games and subscriptions.

    Returns owned/subscription status for each title.
    """
    try:
        ents = await _run(_get_client().get_entitlements, limit)
        if not ents:
            return "No entitlements found."
        lines = [fmt_entitlement(e) for e in ents]
        return f"Entitlements ({len(lines)}):\n" + "\n".join(lines)
    except PSNClientError as e:
        return _error(e)


@mcp.tool()
async def psn_game_details(
    title_id: Annotated[str, Field(description="Game title ID (e.g. PPSA01234_00)")],
    platform: Annotated[str, Field(description="Platform: ps5, ps4, ps3, psvita, pspc")] = "ps5",
) -> str:
    """Get detailed game title metadata — name, description, platform, icon."""
    try:
        details = await _run(_get_client().get_game_details, title_id, platform)
        if not details:
            return f"No details found for {title_id}."
        # Format first concept result
        d = details[0] if details else {}
        lines = [f"Game: {d.get('name', title_id)}"]
        if desc := d.get("description"):
            lines.append(f"  desc: {desc[:200]}")
        if platforms := d.get("platforms"):
            lines.append(f"  platforms: {', '.join(platforms)}")
        if media := d.get("media"):
            for m in media[:2]:
                if url := m.get("url"):
                    lines.append(f"  media: {url}")
        return "\n".join(lines)
    except PSNClientError as e:
        return _error(e)


@mcp.tool()
async def psn_search_games(
    query: Annotated[str, Field(description="Game title search query")],
    limit: Annotated[int, Field(description="Max results")] = DEFAULT_SEARCH_LIMIT,
) -> str:
    """Search PlayStation Store for games by title.

    Returns compact list with name and platforms.
    """
    try:
        results = await _run(_get_client().search_games, query, limit)
        if not results:
            return f"No games found for '{query}'."
        lines = [fmt_search_game(r) for r in results]
        return f"Games matching '{query}' ({len(lines)}):\n" + "\n".join(lines)
    except PSNClientError as e:
        return _error(e)


# ---------------------------------------------------------------------------
# Messaging (contract: gated)
# ---------------------------------------------------------------------------


@mcp.tool()
async def psn_send_message(
    group_id: Annotated[str, Field(description="Message group ID")],
    message: Annotated[str, Field(description="Message text to send")],
) -> str:
    """Send a text message to a PSN message group. Requires PSN_WRITE_ENABLED=true."""
    gate = require_write()
    if gate:
        return gate
    try:
        result = await _run(_get_client().send_message, group_id, message)
        return f"Message sent. uid={result.get('messageUid', '?')}"
    except PSNClientError as e:
        return _error(e)


# ---------------------------------------------------------------------------
# Friend Management (contract: gated)
# ---------------------------------------------------------------------------


@mcp.tool()
async def psn_friend_accept(
    online_id: Annotated[str, Field(description="PSN online ID of the friend request sender")],
) -> str:
    """Accept a pending friend request. Requires PSN_WRITE_ENABLED=true."""
    gate = require_write()
    if gate:
        return gate
    try:
        await _run(_get_client().accept_friend, online_id)
        return f"Friend request from {online_id} accepted."
    except PSNClientError as e:
        return _error(e)


@mcp.tool()
async def psn_friend_remove(
    online_id: Annotated[str, Field(description="PSN online ID of the friend to remove")],
) -> str:
    """Remove a friend from your PSN friends list. Requires PSN_WRITE_ENABLED=true."""
    gate = require_write()
    if gate:
        return gate
    try:
        await _run(_get_client().remove_friend, online_id)
        return f"Friend {online_id} removed."
    except PSNClientError as e:
        return _error(e)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the PSN Blade MCP server."""
    if TRANSPORT == "http":
        from starlette.middleware import Middleware

        from psn_blade_mcp.auth import BearerAuthMiddleware

        app = mcp.http_app(transport="streamable-http", middleware=[Middleware(BearerAuthMiddleware)])
        import uvicorn

        uvicorn.run(app, host=HTTP_HOST, port=HTTP_PORT)
    else:
        mcp.run(transport="stdio")
