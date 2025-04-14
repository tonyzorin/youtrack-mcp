#!/usr/bin/env python3
"""
YouTrack MCP Server - A Model Context Protocol server for JetBrains YouTrack.
"""
import argparse
import logging
import os
import signal
import sys
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from youtrack_mcp.config import Config, config
from youtrack_mcp.server import YouTrackMCPServer
from youtrack_mcp.tools.issues import IssueTools
from youtrack_mcp.tools.projects import ProjectTools
from youtrack_mcp.tools.users import UserTools
from youtrack_mcp.tools.search import SearchTools
from youtrack_mcp.tools.loader import load_all_tools

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="YouTrack MCP Server",
    description="MCP Server for JetBrains YouTrack",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Define request/response models
class ToolRequest(BaseModel):
    name: str = Field(..., description="The name of the tool to execute")
    arguments: Dict[str, Any] = Field(default={}, description="Arguments for the tool")


class ToolResponse(BaseModel):
    result: Any = Field(..., description="Result of the tool execution")


# Initialize tools dictionary
tools = {}


@app.on_event("startup")
async def startup_event():
    """Initialize the MCP server on startup."""
    global tools
    
    # Load configuration from environment variables or file
    load_config()
    
    # Load all tools
    tools = load_all_tools()
    logger.info(f"Loaded {len(tools)} tools")


def load_config():
    """Load configuration from environment variables or file."""
    # Environment variables have higher priority than config file
    env_config = {}
    
    # Extract config variables from environment
    for key in dir(Config):
        if key.isupper() and not key.startswith("_"):
            env_key = f"YOUTRACK_MCP_{key}"
            if env_key in os.environ:
                env_value = os.environ[env_key]
                # Convert string booleans to actual booleans
                if env_value.lower() in ("true", "false"):
                    env_value = env_value.lower() == "true"
                env_config[key] = env_value
    
    # Create config instance from environment variables
    if env_config:
        logger.info("Loading configuration from environment variables")
        Config.from_dict(env_config)
    
    # Log configuration status
    if config.YOUTRACK_URL:
        logger.info(f"Configured for self-hosted YouTrack instance at: {config.YOUTRACK_URL}")
    else:
        logger.info("Configured for YouTrack Cloud instance")
    
    logger.info(f"SSL verification: {'Enabled' if config.VERIFY_SSL else 'Disabled'}")


@app.post("/api/tools/{tool_name}")
async def execute_tool(tool_name: str, request: Request):
    """
    Execute a specific tool by name.
    
    Args:
        tool_name: Name of the tool to execute
        request: The request object containing tool arguments
        
    Returns:
        Tool execution result
    """
    try:
        # Get tool from registry
        if tool_name not in tools:
            return JSONResponse(
                status_code=404,
                content={"error": f"Tool '{tool_name}' not found"}
            )
        
        # Parse request body
        body = await request.json()
        arguments = body.get("arguments", {})
        
        # Execute tool
        logger.info(f"Executing tool: {tool_name} with arguments: {arguments}")
        result = tools[tool_name](**arguments)
        
        return {"result": result}
    except Exception as e:
        logger.exception(f"Error executing tool {tool_name}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/api/tools")
async def list_tools():
    """
    List all available tools.
    
    Returns:
        List of available tools with their definitions
    """
    tool_definitions = {}
    
    for name, tool_func in tools.items():
        # Get tool metadata if available
        if hasattr(tool_func, "tool_definition"):
            tool_definitions[name] = tool_func.tool_definition
        else:
            # Basic definition if metadata not available
            tool_definitions[name] = {
                "name": name,
                "description": tool_func.__doc__ or "No description available"
            }
    
    return {"tools": tool_definitions}


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="YouTrack MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument(
        "--log-level", 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    parser.add_argument(
        "--youtrack-url", 
        help="YouTrack instance URL (not required for YouTrack Cloud)"
    )
    parser.add_argument(
        "--api-token", 
        help="YouTrack API token for authentication"
    )
    parser.add_argument(
        "--verify-ssl",
        action="store_true",
        default=None,
        help="Verify SSL certificates (default: True)"
    )
    parser.add_argument(
        "--no-verify-ssl",
        action="store_false",
        dest="verify_ssl",
        help="Disable SSL certificate verification"
    )
    
    return parser.parse_args()


def apply_cli_args(args):
    """Apply command line arguments to configuration."""
    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Apply YouTrack configuration
    config_dict = {}
    
    if args.youtrack_url:
        config_dict["YOUTRACK_URL"] = args.youtrack_url
    
    if args.api_token:
        config_dict["YOUTRACK_API_TOKEN"] = args.api_token
    
    if args.verify_ssl is not None:
        config_dict["VERIFY_SSL"] = args.verify_ssl
    
    if config_dict:
        Config.from_dict(config_dict)


def handle_signal(signum: int, frame) -> None:
    """
    Handle termination signals.
    
    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logging.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Run the MCP server."""
    args = parse_args()
    
    # Apply command line arguments
    apply_cli_args(args)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Initialize MCP server
    server = YouTrackMCPServer()
    
    try:
        # Initialize tools
        issue_tools = IssueTools()
        project_tools = ProjectTools()
        user_tools = UserTools()
        search_tools = SearchTools()
        
        # Register tools
        server.register_tools(issue_tools.get_tool_definitions())
        server.register_tools(project_tools.get_tool_definitions())
        server.register_tools(user_tools.get_tool_definitions())
        server.register_tools(search_tools.get_tool_definitions())
        
        # Start server with uvicorn
        import uvicorn
        uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level.lower())
        
    except Exception as e:
        logging.exception(f"Error starting server: {e}")
        sys.exit(1)
    finally:
        # Clean up
        if 'issue_tools' in locals():
            issue_tools.close()
        if 'project_tools' in locals():
            project_tools.close()
        if 'user_tools' in locals():
            user_tools.close()
        if 'search_tools' in locals():
            search_tools.close()


if __name__ == "__main__":
    main() 