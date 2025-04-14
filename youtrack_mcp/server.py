"""
MCP server implementation for YouTrack.
"""
import logging
from typing import Dict, List, Any, Optional, Callable

from mcp.server.fastmcp import FastMCP

from youtrack_mcp.config import config

logger = logging.getLogger(__name__)


class YouTrackMCPServer:
    """MCP server for YouTrack integration."""
    
    def __init__(self):
        """Initialize the YouTrack MCP server."""
        # Initialize server
        self.server = FastMCP(
            name=config.MCP_SERVER_NAME,
            instructions=config.MCP_SERVER_DESCRIPTION
        )
        
        # Initialize tool registry
        self._tools: Dict[str, Callable] = {}
        
    def register_tool(self, name: str, func: Callable, description: str, 
                     parameter_descriptions: Optional[Dict[str, str]] = None) -> None:
        """
        Register a tool with the MCP server.
        
        Args:
            name: The tool name
            func: The tool function
            description: Description of what the tool does
            parameter_descriptions: Optional descriptions for function parameters
        """
        if name in self._tools:
            logger.warning(f"Tool {name} already registered, will be overwritten")
        
        self._tools[name] = func
        
        # Register with MCP server
        self.server.add_tool(
            fn=func,
            name=name,
            description=description
        )
        
        logger.info(f"Registered tool: {name}")
        
    def register_tools(self, tools: Dict[str, Dict[str, Any]]) -> None:
        """
        Register multiple tools at once.
        
        Args:
            tools: Dictionary mapping tool names to their configuration
        """
        for name, config in tools.items():
            self.register_tool(
                name=name,
                func=config["function"],
                description=config["description"],
                parameter_descriptions=config.get("parameter_descriptions")
            )
            
    def run(self) -> None:
        """Run the MCP server."""
        logger.info(f"Starting YouTrack MCP server ({config.MCP_SERVER_NAME})")
        self.server.run()
            
    def stop(self) -> None:
        """Stop the MCP server."""
        logger.info("Stopping YouTrack MCP server")
        # Server automatically stops when run() completes 