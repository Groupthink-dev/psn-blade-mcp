"""Authentication for HTTP transport.

Bearer token auth for remote/tunnel access. Set PSN_MCP_API_TOKEN env var.
If unset or empty, bearer auth is disabled (localhost-only setups work without it).
"""

from __future__ import annotations

import os

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class BearerAuthMiddleware:
    """Starlette ASGI middleware for Bearer token auth."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.token = os.environ.get("PSN_MCP_API_TOKEN", "")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        if not self.token:
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()

        if auth_header != f"Bearer {self.token}":
            response = JSONResponse({"error": "Unauthorized"}, status_code=401)
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
