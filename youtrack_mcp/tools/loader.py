"""
Tool loader module for YouTrack MCP.
Loads all tools from the youtrack_mcp.tools package.
"""

import importlib
import inspect
import logging
from typing import Dict, Callable, Any
from collections import defaultdict

from youtrack_mcp.mcp_wrappers import create_bound_tool

# Set up logger
logger = logging.getLogger(__name__)

# Define priority classes for resolving duplicates
TOOL_PRIORITY = {
    "IssueTools": {
        "create_issue": 100,  # Give highest priority to IssueTools.create_issue
    },
    "ProjectTools": {
        "get_custom_fields": 100,  # Highest priority for this tool in ProjectTools
    },
    "SearchTools": {
        "get_custom_fields": 50,  # Lower priority in SearchTools
        "search_with_custom_fields": 100,  # High priority for search_with_custom_fields in SearchTools
    },
    "ResourcesTools": {
        "get_issue": 200,  # Higher priority for resource-based tools
        "get_project": 200,
        "get_project_issues": 200,
        "get_user": 200,
        "get_all_issues": 200,
        "get_all_projects": 200,
        "get_all_users": 200,
        "get_issue_comments": 200,
        "search_issues": 200,
    },
}


def load_all_tools() -> Dict[str, Callable]:
    """
    Load all tools from the youtrack_mcp.tools package.

    This function loads tools from all tool classes and registers them with their
    short names (without namespaces). If the same tool name exists in multiple classes,
    the tool from the class with higher priority will be used.

    Available tools:
    - get_projects, get_project, get_project_by_name, get_project_issues, get_custom_fields,
      create_project, update_project (from ProjectTools)
    - get_issue, get_issue_raw, search_issues, create_issue, add_comment (from IssueTools)
    - get_user, get_user_by_login, get_user_groups, search_users, get_current_user (from UserTools)
    - advanced_search, filter_issues, search_with_custom_fields (from SearchTools)

    Returns:
        Dict[str, Callable]: Dictionary mapping tool names to their functions
    """
    tools = {}

    # Import tool modules
    from youtrack_mcp.tools.issues import IssueTools
    from youtrack_mcp.tools.projects import ProjectTools
    from youtrack_mcp.tools.users import UserTools
    from youtrack_mcp.tools.search import SearchTools
    from youtrack_mcp.tools.resources import ResourcesTools

    # Initialize tool classes
    tool_classes = [
        IssueTools(),
        ProjectTools(),
        UserTools(),
        SearchTools(),
        ResourcesTools(),
    ]

    # Collect tool definitions from all classes
    all_tool_definitions = {}
    for tool_class in tool_classes:
        class_name = tool_class.__class__.__name__

        # Get tool definitions if the class has the method
        if hasattr(tool_class, "get_tool_definitions") and callable(
            getattr(tool_class, "get_tool_definitions")
        ):
            class_tool_defs = tool_class.get_tool_definitions()
            for tool_name, definition in class_tool_defs.items():
                if tool_name not in all_tool_definitions:
                    all_tool_definitions[tool_name] = definition
                else:
                    # If tool already has a definition, keep higher priority one
                    current_class = all_tool_definitions[tool_name].get(
                        "source_class", ""
                    )
                    current_priority = TOOL_PRIORITY.get(
                        current_class, {}
                    ).get(tool_name, 10)
                    new_priority = TOOL_PRIORITY.get(class_name, {}).get(
                        tool_name, 10
                    )

                    if new_priority > current_priority:
                        definition["source_class"] = class_name
                        all_tool_definitions[tool_name] = definition
                        logger.debug(
                            f"Using tool definition for '{tool_name}' from {class_name} (higher priority)"
                        )

    # Track tool names, their sources, and priorities
    tool_sources = {}
    tool_priorities = {}

    # First pass: collect all tools, their class sources, and priorities
    for tool_class in tool_classes:
        class_name = tool_class.__class__.__name__
        class_tools = _get_tools_from_class(tool_class)

        for name, method in class_tools.items():
            # Skip internal methods
            if name in ["close", "get_tool_definitions"]:
                continue

            # Track where the tool came from
            if name in tool_sources:
                tool_sources[name].append(class_name)
            else:
                tool_sources[name] = [class_name]

            # Set priority for this tool from this class
            priority = TOOL_PRIORITY.get(class_name, {}).get(
                name, 10
            )  # Default priority is 10

            # Store the priority - higher number means higher priority
            if name in tool_priorities:
                tool_priorities[name].append((class_name, priority))
            else:
                tool_priorities[name] = [(class_name, priority)]

    # Log duplicate tools
    for name, sources in tool_sources.items():
        if len(sources) > 1:
            logger.warning(
                f"Tool {name} exists in multiple classes: {', '.join(sources)}"
            )
            # Get the highest priority source
            highest_priority_source = max(
                tool_priorities[name], key=lambda x: x[1]
            )
            logger.info(
                f"Will use {name} from {highest_priority_source[0]} (priority {highest_priority_source[1]})"
            )

    # Second pass: register tools based on priority
    registered_tools = set()

    # Process tools with duplicates first, using the highest priority version
    for name, priorities in tool_priorities.items():
        if len(priorities) > 1:
            # Sort by priority (highest first)
            sorted_priorities = sorted(
                priorities, key=lambda x: x[1], reverse=True
            )
            highest_class_name = sorted_priorities[0][0]

            # Find the class instance with this name
            for tool_class in tool_classes:
                if tool_class.__class__.__name__ == highest_class_name:
                    # Get the method from this class and create a properly bound wrapper
                    bound_tool = create_bound_tool(tool_class, name)

                    # Add tool definition if available
                    if name in all_tool_definitions:
                        definition = all_tool_definitions[name]
                        bound_tool.tool_definition = definition

                    # Register the tool with its short name
                    tools[name] = bound_tool
                    registered_tools.add(name)
                    logger.info(
                        f"Registered tool '{name}' from {highest_class_name} (priority choice)"
                    )
                    break

    # Now register all remaining tools without duplicates
    for tool_class in tool_classes:
        class_name = tool_class.__class__.__name__
        class_tools = _get_tools_from_class(tool_class)

        for name, method in class_tools.items():
            # Skip internal methods or already registered tools
            if (
                name in ["close", "get_tool_definitions"]
                or name in registered_tools
            ):
                continue

            # Create a properly bound wrapper for the method
            bound_tool = create_bound_tool(tool_class, name)

            # Add tool definition if available
            if name in all_tool_definitions:
                definition = all_tool_definitions[name]
                bound_tool.tool_definition = definition

            # Register the tool with its short name
            tools[name] = bound_tool
            registered_tools.add(name)
            # Log in debug level only to reduce verbosity
            logger.debug(f"Registered tool '{name}' from {class_name}")

    # Log total number of tools loaded
    logger.info(f"Loader registered {len(tools)} tools from all tool classes")

    return tools


def _get_tools_from_class(tool_class: Any) -> Dict[str, Callable]:
    """
    Get all tools from a tool class.

    This function extracts all public methods from a tool class,
    excluding special methods (starting with '__'), internal methods,
    and Mock-specific methods when testing.

    Args:
        tool_class: Tool class instance

    Returns:
        Dictionary mapping method names to callables
    """
    result = {}

    # Mock-specific methods to exclude (for testing)
    mock_methods = {
        "assert_any_call",
        "assert_called",
        "assert_called_once",
        "assert_called_once_with",
        "assert_called_with",
        "assert_has_calls",
        "assert_not_called",
        "attach_mock",
        "configure_mock",
        "mock_add_spec",
        "reset_mock",
        "return_value",
        "side_effect",
        "call_args",
        "call_args_list",
        "call_count",
        "called",
        "method_calls",
    }

    # Get all class methods
    for name in dir(tool_class):
        # Skip special and internal methods
        if name.startswith("__") or name in ["close", "get_tool_definitions"]:
            continue

        # Skip Mock-specific methods when testing
        if name in mock_methods:
            continue

        # Get the attribute
        attr = getattr(tool_class, name)

        # Only include if it's a callable
        if callable(attr):
            result[name] = attr

    return result
