#!/usr/bin/env python3
"""
YouTrack MCP Server - A Model Context Protocol server for JetBrains YouTrack.
Uses MCPServer for stdio, SSE, and streamable HTTP transports.
"""
import logging
import os
import stat
import sys

from mcp.server.mcpserver import MCPServer

from youtrack_mcp.version import __version__ as APP_VERSION
from youtrack_mcp.config import config
from youtrack_mcp.tools.loader import load_all_tools

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

# MCP SDK names the remote HTTP transport "streamable-http".
# Accept "http" as an alias so the npm --http flag keeps working.
_HTTP_TRANSPORTS = {"http", "streamable-http"}
_HTTP_RUN_TRANSPORTS = {"sse", "streamable-http"}


def create_server() -> MCPServer:
    """Create and configure the MCPServer with all tools registered."""
    mcp = MCPServer(
        config.MCP_SERVER_NAME,
        instructions=config.MCP_SERVER_DESCRIPTION,
        version=APP_VERSION,
    )

    # Load and register all tools
    tools = load_all_tools()
    for name, func in tools.items():
        mcp.add_tool(func, name=name)

    logger.info(f"Registered {len(tools)} tools with MCPServer")
    return mcp


def _normalize_transport(transport: str) -> str:
    if transport in _HTTP_TRANSPORTS:
        return "streamable-http"
    return transport


def _stdin_is_mcp_client() -> bool:
    """True when stdin is a pipe/socket from an MCP host (docker -i, Claude, Cursor)."""
    try:
        mode = os.fstat(sys.stdin.fileno()).st_mode
    except OSError:
        return False
    return stat.S_ISFIFO(mode) or stat.S_ISSOCK(mode)


def _should_fallback_to_http() -> bool:
    """True when stdio would just EOF (Compose, docker without -i), not a TTY or pipe."""
    if _stdin_is_mcp_client():
        return False
    try:
        return not sys.stdin.isatty()
    except (OSError, ValueError):
        return True


def main():
    """Run the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="YouTrack MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http", "http"],
        default=None,
        help="Transport mode (default: from TRANSPORT env var, fallback stdio)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host for SSE / streamable HTTP")
    parser.add_argument("--port", type=int, default=None, help="Port for SSE / streamable HTTP")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    args = parser.parse_args()

    if args.version:
        print(f"YouTrack MCP Server v{APP_VERSION}")
        sys.exit(0)

    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Determine transport: CLI arg > env var > default stdio
    transport = _normalize_transport(args.transport or os.getenv("TRANSPORT", "stdio"))
    port = args.port or int(os.getenv("PORT", "8000"))

    # Docker Compose (no stdin) looks like a crash: stdio starts, then EOF exits.
    # Switch to streamable HTTP so a long-running service actually stays up.
    # Explicit --transport stdio skips this (Dockerfile ENV TRANSPORT=stdio does not).
    if (
        transport == "stdio"
        and args.transport != "stdio"
        and _should_fallback_to_http()
    ):
        logger.warning(
            "No MCP client on stdin (typical of docker compose without -i). "
            "Switching to streamable-http on 0.0.0.0:%s. "
            "Pass --transport stdio to keep stdio, or set TRANSPORT=streamable-http "
            "and publish port %s.",
            port,
            port,
        )
        transport = "streamable-http"

    logger.info(f"Starting YouTrack MCP Server v{APP_VERSION} [{transport}]")

    mcp = create_server()
    if transport in _HTTP_RUN_TRANSPORTS:
        mcp.run(transport=transport, host=args.host, port=port)
    else:
        mcp.run(transport=transport)


if __name__ == "__main__":
    main()
