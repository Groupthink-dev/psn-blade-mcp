# PSN Blade MCP

PlayStation Network MCP server for [Sidereal](https://sidereal.cc). Trophy tracking, game library, friends, presence, and messaging — all through token-efficient compact output designed for LLM consumption.

## Why This Exists

Several PSN libraries exist ([psn-api](https://github.com/achievements-app/psn-api), [PSNAWP](https://github.com/isFakeAccount/psnawp), [psn-php](https://github.com/Tustin/psn-php)). None are MCP servers. This blade bridges that gap:

| | psn-api (npm) | PSNAWP (Python) | psn-php | **PSN Blade MCP** |
|---|---|---|---|---|
| **MCP protocol** | No | No | No | **Yes** — stdio + HTTP |
| **Token-efficient output** | JSON blobs | Python objects | PHP arrays | **Compact text** — 3-5x fewer tokens |
| **Auto token refresh** | No | Yes | Unknown | **Yes** (via PSNAWP) |
| **Rate limiting** | No | Yes | No | **Yes** — 300/15min enforced |
| **Write safety** | No gate | No gate | No gate | **Write-gated** — messaging and friend ops require explicit opt-in |
| **Contract compliance** | N/A | N/A | N/A | **gaming-v1** — portable across PSN, Steam, Xbox |
| **Sidereal integration** | None | None | None | **Full** — marketplace, packs, webhook triggers |

Built on PSNAWP for its mature auth handling, rate limiting, and broadest API coverage (trophies + games + messaging + search + entitlements).

## Quick Start

### Install

```bash
# With uv (recommended)
uv pip install psn-blade-mcp

# Or from source
git clone https://github.com/groupthink-dev/psn-blade-mcp
cd psn-blade-mcp
make install-dev
```

### Get Your NPSSO Token

1. Log in at [store.playstation.com](https://store.playstation.com) in your browser
2. Visit [ca.account.sony.com/api/v1/ssocookie](https://ca.account.sony.com/api/v1/ssocookie)
3. Copy the `npsso` value from the JSON response

> **Security:** Use a dedicated PSN account for API access. Sony may restrict accounts with excessive API usage. The NPSSO token is equivalent to your password — never share it.

### Configure

```bash
# Required
export PSN_NPSSO="your-npsso-token-here"

# Optional — enable messaging and friend management
export PSN_WRITE_ENABLED=true
```

### Run

```bash
# stdio transport (default — for Claude Code, Sidereal)
psn-blade-mcp

# HTTP transport (for remote/tunnel access)
PSN_MCP_TRANSPORT=http PSN_MCP_PORT=8780 psn-blade-mcp
```

### Claude Code Configuration

Add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "psn": {
      "type": "stdio",
      "command": "psn-blade-mcp",
      "env": {
        "PSN_NPSSO": "your-npsso-token"
      }
    }
  }
}
```

## Tools (17)

### Profile & Social
- **`psn_profile`** — User profile (name, avatar, PS Plus status)
- **`psn_friends`** — Friends list
- **`psn_presence`** — Online/in-game status
- **`psn_search_users`** — Find users by name
- **`psn_devices`** — Registered consoles

### Trophies
- **`psn_trophy_summary`** — Overall trophy level, tier, and counts
- **`psn_trophies`** — Per-game trophy list with earned/locked status
- **`psn_trophy_compare`** — Head-to-head trophy comparison
- **`psn_trophy_groups`** — Base game + DLC trophy group breakdown

### Games
- **`psn_games`** — Game library with playtime stats
- **`psn_games_recent`** — Recently played games
- **`psn_entitlements`** — Purchase history
- **`psn_game_details`** — Title metadata
- **`psn_search_games`** — Search PlayStation Store

### Messaging (write-gated)
- **`psn_send_message`** — Send text message to a group
- **`psn_friend_accept`** — Accept friend request
- **`psn_friend_remove`** — Remove friend

## Contract: `gaming-v1`

This MCP implements the `gaming-v1` Sidereal contract — a portable interface across gaming platforms. The same contract will be implemented by `steam-blade-mcp`, `xbox-blade-mcp`, and `retroachievements-blade-mcp`, enabling cross-platform pack skills.

| Classification | Operations | Status |
|---|---|---|
| **Required** | profile, achievements, achievement_summary, games_played | Implemented |
| **Recommended** | games_recent, friends, presence, search_users | Implemented |
| **Optional** | achievement_compare, achievement_groups, games_purchased, devices, game_details, search_games | Implemented |
| **Gated** | send_message, friend_add, friend_remove | Implemented (write-gated) |

## Architecture

```
psn-blade-mcp/
├── src/psn_blade_mcp/
│   ├── server.py       # FastMCP tool definitions (17 tools)
│   ├── client.py       # PSNAWP wrapper with error handling
│   ├── models.py       # Constants, write-gate, shared types
│   ├── formatters.py   # Token-efficient compact text output
│   └── auth.py         # Bearer token middleware (HTTP transport)
├── tests/              # pytest + asyncio (mocked, no live API)
├── sidereal-plugin.yaml  # Marketplace manifest
└── SKILL.md            # LLM usage guide
```

**Key design decisions:**
- **PSNAWP as client layer** — proven auth handling, auto token refresh, built-in rate limiting (300 req/15min), typed exceptions for every HTTP status
- **Compact text output** — all formatters return pipe-delimited strings, not JSON. 3-5x fewer tokens than raw API responses
- **Lazy client initialization** — PSN auth only happens on first tool call, not server startup
- **Write-gated operations** — messaging and friend management require explicit `PSN_WRITE_ENABLED=true`

## Rate Limiting

Sony enforces ~300 requests per 15-minute window. PSNAWP's built-in rate limiter (1 request per 3 seconds via SQLite-backed bucket) prevents exceeding this. The MCP server adds no additional rate limiting — PSNAWP handles it transparently.

If rate limited, the server returns a clear error: `"Rate limited by PSN — wait a few minutes before retrying."`

## Token Lifecycle

| Token | Lifetime | Refresh |
|---|---|---|
| NPSSO | Browser session (~24h) | Manual — re-visit ssocookie URL |
| Access token | ~60 minutes | Automatic (PSNAWP handles transparently) |
| Refresh token | ~2 months | Automatic (PSNAWP handles transparently) |

When your NPSSO expires, the server returns an auth error with instructions to regenerate it.

## Development

```bash
make install-dev     # Install with dev/test dependencies
make test            # Run unit tests
make test-cov        # Tests with coverage report
make check           # Lint + format + type-check
make run             # Run the MCP server
```

## Disclaimer

This project uses Sony's **unofficial, undocumented** PlayStation Network API via [PSNAWP](https://github.com/isFakeAccount/psnawp). There is no official Sony API for PSN data. Sony may change or break these endpoints at any time. Use at your own risk and consider using a dedicated PSN account.

## License

MIT
