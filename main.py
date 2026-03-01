#!/usr/bin/env python3
"""
YouTrack MCP Server - A Model Context Protocol server for JetBrains YouTrack.
Uses FastMCP directly for clean stdio/SSE transport support.
"""
import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

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


def create_server(host: str = "0.0.0.0", port: int = 8000, transport: str = "stdio") -> FastMCP:
    """Create and configure the FastMCP server with all tools registered."""
    if transport == "sse":
        mcp = FastMCP(
            config.MCP_SERVER_NAME,
            instructions=config.MCP_SERVER_DESCRIPTION,
            host=host,
            port=port,
        )
    else:
        mcp = FastMCP(
            config.MCP_SERVER_NAME,
            instructions=config.MCP_SERVER_DESCRIPTION,
        )

    # Load and register all tools
    tools = load_all_tools()
    for name, func in tools.items():
        mcp.add_tool(func, name=name)

    logger.info(f"Registered {len(tools)} tools with FastMCP")
    return mcp


def main():
    """Run the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="YouTrack MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default=None,
                        help="Transport mode (default: from TRANSPORT env var, fallback stdio)")
    parser.add_argument("--host", default="0.0.0.0", help="Host for SSE transport")
    parser.add_argument("--port", type=int, default=None, help="Port for SSE transport")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    args = parser.parse_args()

    if args.version:
        print(f"YouTrack MCP Server v{APP_VERSION}")
        sys.exit(0)

    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Determine transport: CLI arg > env var > default stdio
    transport = args.transport or os.getenv("TRANSPORT", "stdio")
    port = args.port or int(os.getenv("PORT", "8000"))

    logger.info(f"Starting YouTrack MCP Server v{APP_VERSION} [{transport}]")

    mcp = create_server(host=args.host, port=port, transport=transport)
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
