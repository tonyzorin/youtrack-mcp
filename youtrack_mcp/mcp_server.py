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
            # Use function from tool definition if provided, otherwise get from class
            function = tool_config.get("function") or getattr(self.issue_tools, tool_name, None)
            if function:
                all_tools[tool_name] = {
                    "description": tool_config["description"],
                    "function": function,
                    "parameter_descriptions": tool_config.get("parameter_descriptions", {}),
                }

        # Add project tools
        project_tool_definitions = self.project_tools.get_tool_definitions()
        for tool_name, tool_config in project_tool_definitions.items():
            function = tool_config.get("function") or getattr(self.project_tools, tool_name, None)
            if function:
                all_tools[tool_name] = {
                    "description": tool_config["description"],
                    "function": function,
                    "parameter_descriptions": tool_config.get("parameter_descriptions", {}),
                }

        # Add user tools
        user_tool_definitions = self.user_tools.get_tool_definitions()
        for tool_name, tool_config in user_tool_definitions.items():
            function = tool_config.get("function") or getattr(self.user_tools, tool_name, None)
            if function:
                all_tools[tool_name] = {
                    "description": tool_config["description"],
                    "function": function,
                    "parameter_descriptions": tool_config.get("parameter_descriptions", {}),
                }

        # Add search tools
        search_tool_definitions = self.search_tools.get_tool_definitions()
        for tool_name, tool_config in search_tool_definitions.items():
            function = tool_config.get("function") or getattr(self.search_tools, tool_name, None)
            if function:
                all_tools[tool_name] = {
                    "description": tool_config["description"],
                    "function": function,
                    "parameter_descriptions": tool_config.get("parameter_descriptions", {}),
                }

        # Add resource tools (with conflict resolution)
        resource_tool_definitions = self.resources_tools.get_tool_definitions()
        for tool_name, tool_config in resource_tool_definitions.items():
            function = tool_config.get("function") or getattr(self.resources_tools, tool_name, None)
            if function:
                # Handle naming conflicts by prefixing resource tools
                final_tool_name = tool_name
                if tool_name in all_tools:
                    final_tool_name = f"resource_{tool_name}"

                all_tools[final_tool_name] = {
                    "description": tool_config["description"],
                    "function": function,
                    "parameter_descriptions": tool_config.get("parameter_descriptions", {}),
                }

        return all_tools
