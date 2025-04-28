"""
Tool loader module for YouTrack MCP.
Loads all tools from the youtrack_mcp.tools package.
"""

import importlib
import inspect
import logging
from typing import Dict, Callable, Any

# Set up logger
logger = logging.getLogger(__name__)

def load_all_tools() -> Dict[str, Callable]:
    """
    Load all tools from the youtrack_mcp.tools package.
    
    Returns:
        Dict[str, Callable]: Dictionary mapping tool names to their functions
    """
    tools = {}
    
    # Import tool modules
    from youtrack_mcp.tools.issues import IssueTools
    from youtrack_mcp.tools.projects import ProjectTools
    from youtrack_mcp.tools.users import UserTools
    from youtrack_mcp.tools.search import SearchTools
    
    # Initialize tool classes
    tool_classes = [
        IssueTools(),
        ProjectTools(),
        UserTools(),
        SearchTools()
    ]
    
    # Collect tools from each class
    for tool_class in tool_classes:
        class_tools = _get_tools_from_class(tool_class)
        tools.update(class_tools)
        logger.info(f"Loaded {len(class_tools)} tools from {tool_class.__class__.__name__}")
    
    return tools

def _get_tools_from_class(tool_class: Any) -> Dict[str, Callable]:
    """
    Extract tool methods from a tool class.
    
    Args:
        tool_class: An instance of a tool class
        
    Returns:
        Dict[str, Callable]: Dictionary mapping tool names to their methods
    """
    tools = {}
    
    # Get all methods that don't start with underscore
    for name, method in inspect.getmembers(tool_class, inspect.ismethod):
        if not name.startswith('_'):
            tools[name] = method
    
    return tools 