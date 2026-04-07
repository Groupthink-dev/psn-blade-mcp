---
name: psn-blade-mcp
description: PlayStation Network MCP server — trophies, game library, friends, presence, messaging
version: 0.1.0
permissions:
  read:
    - psn_profile
    - psn_trophy_summary
    - psn_trophies
    - psn_trophy_compare
    - psn_trophy_groups
    - psn_games
    - psn_games_recent
    - psn_entitlements
    - psn_game_details
    - psn_search_games
    - psn_search_users
    - psn_friends
    - psn_presence
    - psn_devices
  write:
    - psn_send_message
    - psn_friend_accept
    - psn_friend_remove
---

# PSN Blade MCP — Skill Guide

## Token Efficiency Rules

1. **Use `psn_trophy_summary` before `psn_trophies`** — get the overview first, then drill into specific games
2. **Use `psn_games_recent` over `psn_games`** — smaller response for "what have I been playing?"
3. **Specify `limit=` on all list tools** — default limits are tuned for token efficiency but override when you need fewer
4. **Trophy IDs (`np_communication_id`) come from `psn_trophy_summary`** — don't guess them, query first
5. **Use `psn_presence` for single users, not bulk** — one call per user, no batch endpoint
6. **`psn_trophy_compare` is two API calls internally** — use sparingly

## Quick Start — 5 Most Common Operations

```
# 1. Check your trophy progress
psn_trophy_summary()

# 2. See what you've been playing recently
psn_games_recent(limit=5)

# 3. Get trophies for a specific game (ID from trophy_summary)
psn_trophies(np_communication_id="NPWR12345_00", platform="ps5")

# 4. Check if a friend is online
psn_presence(online_id="FriendName")

# 5. Find a PSN user
psn_search_users(query="username")
```

## Tool Reference

### Profile & Social

| Tool | Purpose | Params |
|------|---------|--------|
| `psn_profile` | User profile (name, avatar, PS+) | `online_id?` |
| `psn_friends` | Your friends list | `limit=50` |
| `psn_presence` | Online/in-game status | `online_id` |
| `psn_search_users` | Find users by name | `query`, `limit=10` |
| `psn_devices` | Registered consoles | — |

### Trophies (Achievements)

| Tool | Purpose | Params |
|------|---------|--------|
| `psn_trophy_summary` | Overall level, tier, counts | `online_id?` |
| `psn_trophies` | Per-game trophy list with earned status | `np_communication_id`, `platform=ps5`, `online_id?`, `trophy_group_id=default`, `limit=200` |
| `psn_trophy_compare` | Side-by-side comparison | `np_communication_id`, `online_id`, `platform=ps5` |
| `psn_trophy_groups` | Base + DLC group breakdown | `np_communication_id`, `platform=ps5`, `online_id?` |

### Games

| Tool | Purpose | Params |
|------|---------|--------|
| `psn_games` | Full game library with playtime | `online_id?`, `limit=25` |
| `psn_games_recent` | Recently played games | `online_id?`, `limit=10` |
| `psn_entitlements` | Purchased games/subs | `limit=25` |
| `psn_game_details` | Title metadata | `title_id`, `platform=ps5` |
| `psn_search_games` | Search PS Store | `query`, `limit=10` |

### Messaging (write-gated)

| Tool | Purpose | Params |
|------|---------|--------|
| `psn_send_message` | Send text to group | `group_id`, `message` |
| `psn_friend_accept` | Accept friend request | `online_id` |
| `psn_friend_remove` | Remove friend | `online_id` |

## Output Format

All tools return compact pipe-delimited text. Null fields are omitted.

**Trophy title:** `Astro Bot | [PS5] | 75% | P:1/1 | G:5/8 | S:10/15 | B:20/25 | id=NPWR12345_00`

**Trophy:** `#1 GOLD: First Steps | EARNED | 2026-03-10 12:00 | rarity=RARE | 15.5% | "Complete the tutorial"`

**Game stats:** `Astro Bot | [ps5_native_game] | plays=15 | time=25h30m | last=2026-04-01 20:00 | id=PPSA01234_00`

**Presence:** `status=availableToPlay | platform=PS5 | playing="Elden Ring"`

## Platform Values

Use these for the `platform` parameter:
- `ps5` — PlayStation 5
- `ps4` — PlayStation 4
- `ps3` — PlayStation 3
- `psvita` or `vita` — PS Vita
- `pspc` or `pc` — PlayStation PC

## Security Notes

- NPSSO token is equivalent to your PSN password — treat as secret
- **Use a dedicated PSN account** for API access (Sony may ban accounts for excessive API use)
- Token expires with your browser session — regenerate at `ca.account.sony.com/api/v1/ssocookie`
- Rate limited to ~300 requests per 15 minutes (enforced by PSNAWP client-side)
- Write operations disabled by default — set `PSN_WRITE_ENABLED=true` to enable
