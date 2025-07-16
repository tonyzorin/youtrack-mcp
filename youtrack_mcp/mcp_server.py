from youtrack_mcp.tools.issues import IssueTools
from youtrack_mcp.tools.projects import ProjectTools
from youtrack_mcp.tools.users import UserTools
from youtrack_mcp.tools.search import SearchTools
from youtrack_mcp.tools.resources import ResourcesTools
from typing import Dict, Any


class MCPServer:
    """YouTrack MCP Server tool collection."""

    def __init__(self):
        """Initialize the MCP server tool collection."""
        self.issue_tools = IssueTools()
        self.project_tools = ProjectTools()
        self.user_tools = UserTools()
        self.search_tools = SearchTools()
        self.resources_tools = ResourcesTools()

    def get_all_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get all tool definitions from the improved tools."""

        all_tools = {}

        # Add issue tools (now LLM-optimized)
        issue_tool_definitions = self.issue_tools.get_tool_definitions()
        for tool_name, tool_config in issue_tool_definitions.items():
            function = getattr(self.issue_tools, tool_name, None)
            if function:
                all_tools[tool_name] = {
                    "description": tool_config["description"],
                    "function": function,
                    "parameter_descriptions": tool_config.get(
                        "parameter_descriptions", {}
                    ),
                }

        # Add project tools (now LLM-optimized)
        project_tool_definitions = self.project_tools.get_tool_definitions()
        for tool_name, tool_config in project_tool_definitions.items():
            function = getattr(self.project_tools, tool_name, None)
            if function:
                all_tools[tool_name] = {
                    "description": tool_config["description"],
                    "function": function,
                    "parameter_descriptions": tool_config.get(
                        "parameter_descriptions", {}
                    ),
                }

        # Add user tools (now LLM-optimized)
        user_tool_definitions = self.user_tools.get_tool_definitions()
        for tool_name, tool_config in user_tool_definitions.items():
            function = getattr(self.user_tools, tool_name, None)
            if function:
                all_tools[tool_name] = {
                    "description": tool_config["description"],
                    "function": function,
                    "parameter_descriptions": tool_config.get(
                        "parameter_descriptions", {}
                    ),
                }

        # Add search tools (now LLM-optimized)
        search_tool_definitions = self.search_tools.get_tool_definitions()
        for tool_name, tool_config in search_tool_definitions.items():
            function = getattr(self.search_tools, tool_name, None)
            if function:
                all_tools[tool_name] = {
                    "description": tool_config["description"],
                    "function": function,
                    "parameter_descriptions": tool_config.get(
                        "parameter_descriptions", {}
                    ),
                }

        # Add resources tools (avoid conflicts with primary tools)
        resources_tool_definitions = self.resources_tools.get_tool_definitions()
        for tool_name, tool_config in resources_tool_definitions.items():
            function = getattr(self.resources_tools, tool_name, None)
            if function:
                # If there's a conflict, prefix the resource tool with 'resource_'
                final_name = tool_name
                if tool_name in all_tools:
                    final_name = f"resource_{tool_name}"

                all_tools[final_name] = {
                    "description": tool_config["description"],
                    "function": function,
                    "parameter_descriptions": tool_config.get(
                        "parameter_descriptions", {}
                    ),
                }

        return all_tools

    def close(self) -> None:
        """Close the MCP server."""
        self.issue_tools.close()
        self.project_tools.close()
        self.user_tools.close()
        self.search_tools.close()
        self.resources_tools.close()
