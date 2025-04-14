from youtrack_mcp.tools.auth import AuthTools
from youtrack_mcp.tools.issues import IssueTools
from youtrack_mcp.tools.projects import ProjectTools
from youtrack_mcp.tools.users import UserTools
from youtrack_mcp.tools.search import SearchTools

class MCPServer:
    """YouTrack MCP Server."""

    def __init__(self):
        """Initialize the MCP server."""
        self.auth_tools = AuthTools()
        self.issue_tools = IssueTools()
        self.project_tools = ProjectTools()
        self.user_tools = UserTools()
        self.search_tools = SearchTools()

    def register_tools(self) -> None:
        """Register all MCP tools."""
        # Register auth tools
        auth_tool_definitions = self.auth_tools.get_tool_definitions()
        for tool_name, tool_config in auth_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
            )

        # Register issue tools
        issue_tool_definitions = self.issue_tools.get_tool_definitions()
        for tool_name, tool_config in issue_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
            )
            
        # Register project tools
        project_tool_definitions = self.project_tools.get_tool_definitions()
        for tool_name, tool_config in project_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
            )
            
        # Register user tools
        user_tool_definitions = self.user_tools.get_tool_definitions()
        for tool_name, tool_config in user_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
            )
            
        # Register search tools
        search_tool_definitions = self.search_tools.get_tool_definitions()
        for tool_name, tool_config in search_tool_definitions.items():
            self.register_tool(
                name=tool_name,
                description=tool_config["description"],
                function=tool_config["function"],
                parameter_descriptions=tool_config.get("parameter_descriptions", {}),
            )

    def close(self) -> None:
        """Close the MCP server."""
        self.auth_tools.close()
        self.issue_tools.close()
        self.project_tools.close()
        self.user_tools.close()
        self.search_tools.close()

 