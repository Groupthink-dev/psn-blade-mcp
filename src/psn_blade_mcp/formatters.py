"""Token-efficient output formatters for PSN data.

All formatters return compact text — no JSON objects. Null fields omitted.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any


def fmt_profile(profile: dict[str, Any], account_id: str, online_id: str) -> str:
    """Format user profile as compact text."""
    lines = [f"PSN Profile: {online_id} (account={account_id})"]

    if avatar := profile.get("avatarUrls"):
        if isinstance(avatar, list) and avatar:
            lines.append(f"  avatar: {avatar[0].get('avatarUrl', 'n/a')}")
    if plus := profile.get("isPlus"):
        lines.append(f"  PS Plus: {plus}")
    if about := profile.get("aboutMe"):
        lines.append(f"  about: {about}")
    if langs := profile.get("languages"):
        lines.append(f"  languages: {', '.join(langs)}")

    return "\n".join(lines)


def fmt_trophy_summary(summary: Any) -> str:
    """Format trophy summary as compact one-liner."""
    earned = summary.earned_trophies
    return (
        f"Trophy Level {summary.trophy_level} (tier {summary.tier}, {summary.progress}%) | "
        f"P:{earned.platinum} G:{earned.gold} S:{earned.silver} B:{earned.bronze}"
    )


def fmt_trophy_title(title: Any) -> str:
    """Format a single trophy title as compact line."""
    platforms = ",".join(sorted(p.value if hasattr(p, "value") else str(p) for p in title.title_platform))
    earned = title.earned_trophies
    defined = title.defined_trophies
    progress = f"{title.progress}%" if title.progress is not None else "?"

    parts = [
        f"{title.title_name}",
        f"[{platforms}]",
        f"{progress}",
        f"P:{earned.platinum}/{defined.platinum}",
        f"G:{earned.gold}/{defined.gold}",
        f"S:{earned.silver}/{defined.silver}",
        f"B:{earned.bronze}/{defined.bronze}",
    ]
    if title.np_communication_id:
        parts.append(f"id={title.np_communication_id}")

    return " | ".join(parts)


def fmt_trophy(trophy: Any, with_progress: bool = False) -> str:
    """Format a single trophy as compact line."""
    trophy_type = trophy.trophy_type.name if trophy.trophy_type else "?"
    hidden = " [hidden]" if trophy.trophy_hidden else ""

    parts = [f"#{trophy.trophy_id} {trophy_type}{hidden}: {trophy.trophy_name}"]

    if with_progress:
        if hasattr(trophy, "earned") and trophy.earned is not None:
            status = "EARNED" if trophy.earned else "locked"
            parts.append(status)
        if hasattr(trophy, "earned_date_time") and trophy.earned_date_time:
            parts.append(fmt_datetime(trophy.earned_date_time))
        if hasattr(trophy, "trophy_rarity") and trophy.trophy_rarity is not None:
            parts.append(f"rarity={trophy.trophy_rarity.name}")
        if hasattr(trophy, "trophy_earn_rate") and trophy.trophy_earn_rate is not None:
            parts.append(f"{trophy.trophy_earn_rate}%")

    if trophy.trophy_detail:
        parts.append(f'"{trophy.trophy_detail}"')

    return " | ".join(parts)


def fmt_trophy_group(group: Any, with_progress: bool = False) -> str:
    """Format a trophy group summary as compact line."""
    defined = group.defined_trophies
    parts = [
        f"{group.trophy_group_id}: {group.trophy_group_name}",
        f"P:{defined.platinum} G:{defined.gold} S:{defined.silver} B:{defined.bronze}",
    ]

    if with_progress and hasattr(group, "progress") and group.progress is not None:
        earned = group.earned_trophies
        parts.insert(
            1,
            f"{group.progress}% | earned P:{earned.platinum} G:{earned.gold} S:{earned.silver} B:{earned.bronze}",
        )

    return " | ".join(parts)


def fmt_title_stats(stats: Any) -> str:
    """Format game title stats as compact line."""
    parts = [stats.name or "Unknown"]

    if stats.category:
        parts.append(f"[{stats.category.value if hasattr(stats.category, 'value') else stats.category}]")
    if stats.play_count is not None:
        parts.append(f"plays={stats.play_count}")
    if stats.play_duration is not None:
        parts.append(f"time={fmt_duration(stats.play_duration)}")
    if stats.last_played_date_time:
        parts.append(f"last={fmt_datetime(stats.last_played_date_time)}")
    if stats.first_played_date_time:
        parts.append(f"first={fmt_datetime(stats.first_played_date_time)}")
    if stats.title_id:
        parts.append(f"id={stats.title_id}")

    return " | ".join(parts)


def fmt_friend(user: Any) -> str:
    """Format a friend entry as compact line."""
    return f"{user.online_id} (account={user.account_id})"


def fmt_presence(presence: dict[str, Any]) -> str:
    """Format presence data as compact text."""
    availability = presence.get("availability", "unknown")
    parts = [f"status={availability}"]

    if primary := presence.get("primaryPlatformInfo"):
        if platform := primary.get("platform"):
            parts.append(f"platform={platform}")
    if game_title := presence.get("gameTitleInfoList"):
        if isinstance(game_title, list) and game_title:
            g = game_title[0]
            parts.append(f'playing="{g.get("titleName", "?")}"')

    return " | ".join(parts)


def fmt_device(device: dict[str, Any]) -> str:
    """Format account device as compact line."""
    device_type = device.get("deviceType", "unknown")
    device_id = device.get("deviceId", "?")
    return f"{device_type} | id={device_id}"


def fmt_search_user(result: Any) -> str:
    """Format user search result as compact line."""
    player = result.get("result", result) if isinstance(result, dict) else result
    if isinstance(player, dict):
        online_id = player.get("onlineId", "?")
        account_id = player.get("accountId", "?")
        is_plus = player.get("isPsPlus", False)
        plus_str = " [PS+]" if is_plus else ""
        return f"{online_id}{plus_str} (account={account_id})"
    return str(player)


def fmt_search_game(result: Any) -> str:
    """Format game search result as compact line."""
    if isinstance(result, dict):
        concept = result.get("result", result)
        if isinstance(concept, dict):
            name = concept.get("name") or concept.get("invariantName", "?")
            platforms = concept.get("platforms", [])
            plat_str = ",".join(platforms) if platforms else "?"
            return f"{name} [{plat_str}]"
    return str(result)


def fmt_entitlement(ent: dict[str, Any]) -> str:
    """Format game entitlement as compact line."""
    game_meta = ent.get("gameMeta", {})
    name = game_meta.get("name", "Unknown")
    ent_type = "subscription" if ent.get("isSubscription") else "owned"
    active = "active" if ent.get("activeFlag") else "inactive"
    return f"{name} | {ent_type} | {active}"


def fmt_group_info(info: dict[str, Any]) -> str:
    """Format group information as compact text."""
    group_name = info.get("groupName", {}).get("value", "Unnamed")
    group_id = info.get("groupId", "?")
    members = info.get("members", [])
    member_names = [m.get("onlineId", "?") for m in members]
    modified = info.get("modifiedTimestamp", "")
    return f"{group_name} | id={group_id} | members={','.join(member_names)} | modified={modified}"


def fmt_message(msg: dict[str, Any]) -> str:
    """Format a single message as compact line."""
    sender = msg.get("senderOnlineId") or msg.get("sender", {}).get("onlineId", "?")
    body = msg.get("body", "")
    ts = msg.get("createdTimestamp", "")
    return f"{ts} {sender}: {body}"


def fmt_datetime(dt: datetime | None) -> str:
    """Format datetime as compact ISO string."""
    if dt is None:
        return "?"
    return dt.strftime("%Y-%m-%d %H:%M")


def fmt_duration(td: timedelta | None) -> str:
    """Format timedelta as human-readable string."""
    if td is None:
        return "?"
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h{minutes}m"
    return f"{minutes}m"
