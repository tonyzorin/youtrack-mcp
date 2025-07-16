"""
Unit tests for the YouTrack MCP Server.
"""

import pytest
from unittest.mock import Mock, patch

from youtrack_mcp.mcp_server import MCPServer


class TestMCPServer:
    """Test cases for MCPServer class."""

    @pytest.mark.unit
    def test_initialization(self, mock_youtrack_client):
        """Test that MCPServer initializes correctly."""
        mcp_server = MCPServer()

        # Check that all tool instances are created
        assert hasattr(mcp_server, "issue_tools")
        assert hasattr(mcp_server, "project_tools")
        assert hasattr(mcp_server, "user_tools")
        assert hasattr(mcp_server, "search_tools")
        assert hasattr(mcp_server, "resources_tools")

    @pytest.mark.unit
    def test_get_all_tool_definitions_basic(self, mock_youtrack_client):
        """Test basic functionality of get_all_tool_definitions."""
        mcp_server = MCPServer()

        # Should return a dictionary of tool definitions
        all_tools = mcp_server.get_all_tool_definitions()
        assert isinstance(all_tools, dict)
        assert len(all_tools) > 0

    @pytest.mark.unit
    def test_get_all_tool_definitions_with_mocked_tools(
        self, mock_youtrack_client
    ):
        """Test get_all_tool_definitions with mocked tool definitions."""
        mcp_server = MCPServer()

        # Mock the tool definitions
        mock_issue_definitions = {
            "get_issue": {
                "description": "Get issue details",
                "function": Mock(),
                "parameter_descriptions": {"issue_id": "Issue identifier"},
            }
        }

        mock_project_definitions = {
            "get_project": {
                "description": "Get project details",
                "function": Mock(),
                "parameter_descriptions": {"project_id": "Project identifier"},
            }
        }

        # Patch the get_tool_definitions methods
        with patch.object(
            mcp_server.issue_tools,
            "get_tool_definitions",
            return_value=mock_issue_definitions,
        ), patch.object(
            mcp_server.project_tools,
            "get_tool_definitions",
            return_value=mock_project_definitions,
        ), patch.object(
            mcp_server.user_tools, "get_tool_definitions", return_value={}
        ), patch.object(
            mcp_server.search_tools, "get_tool_definitions", return_value={}
        ), patch.object(
            mcp_server.resources_tools, "get_tool_definitions", return_value={}
        ):

            all_tools = mcp_server.get_all_tool_definitions()

            # Verify tools are included
            assert "get_issue" in all_tools
            assert "get_project" in all_tools
            assert len(all_tools) == 2

            # Verify structure
            assert "description" in all_tools["get_issue"]
            assert "function" in all_tools["get_issue"]
            assert "parameter_descriptions" in all_tools["get_issue"]

    @pytest.mark.unit
    def test_conflict_resolution_with_resource_tools(
        self, mock_youtrack_client
    ):
        """Test that resource tools get prefixed when there are naming conflicts."""
        mcp_server = MCPServer()

        # Mock issue tools with get_issue
        mock_issue_definitions = {
            "get_issue": {
                "description": "Get issue details",
                "function": Mock(),
                "parameter_descriptions": {},
            }
        }

        # Mock resource tools with conflicting get_issue
        mock_resource_definitions = {
            "get_issue": {
                "description": "Get issue as resource",
                "function": Mock(),
                "parameter_descriptions": {},
            }
        }

        with patch.object(
            mcp_server.issue_tools,
            "get_tool_definitions",
            return_value=mock_issue_definitions,
        ), patch.object(
            mcp_server.project_tools, "get_tool_definitions", return_value={}
        ), patch.object(
            mcp_server.user_tools, "get_tool_definitions", return_value={}
        ), patch.object(
            mcp_server.search_tools, "get_tool_definitions", return_value={}
        ), patch.object(
            mcp_server.resources_tools,
            "get_tool_definitions",
            return_value=mock_resource_definitions,
        ):

            all_tools = mcp_server.get_all_tool_definitions()

            # Primary tool should keep original name
            assert "get_issue" in all_tools
            assert all_tools["get_issue"]["description"] == "Get issue details"

            # Resource tool should be prefixed
            assert "resource_get_issue" in all_tools
            assert (
                all_tools["resource_get_issue"]["description"]
                == "Get issue as resource"
            )

    @pytest.mark.unit
    def test_empty_tool_definitions_handled(self, mock_youtrack_client):
        """Test that empty tool definitions are handled gracefully."""
        mcp_server = MCPServer()

        # Mock all tools to return empty definitions
        with patch.object(
            mcp_server.issue_tools, "get_tool_definitions", return_value={}
        ), patch.object(
            mcp_server.project_tools, "get_tool_definitions", return_value={}
        ), patch.object(
            mcp_server.user_tools, "get_tool_definitions", return_value={}
        ), patch.object(
            mcp_server.search_tools, "get_tool_definitions", return_value={}
        ), patch.object(
            mcp_server.resources_tools, "get_tool_definitions", return_value={}
        ):

            all_tools = mcp_server.get_all_tool_definitions()
            assert all_tools == {}


class TestMCPServerIntegration:
    """Integration test cases for MCPServer."""

    @pytest.mark.unit
    def test_real_tool_definitions_structure(self, mock_youtrack_client):
        """Test that real tool definitions have the expected structure."""
        mcp_server = MCPServer()
        all_tools = mcp_server.get_all_tool_definitions()

        # Should have tools from all categories
        assert len(all_tools) > 0

        # Each tool should have required fields
        for tool_name, tool_config in all_tools.items():
            assert (
                "description" in tool_config
            ), f"Tool {tool_name} missing description"
            assert (
                "function" in tool_config
            ), f"Tool {tool_name} missing function"
            assert (
                "parameter_descriptions" in tool_config
            ), f"Tool {tool_name} missing parameter_descriptions"
            assert isinstance(tool_config["description"], str)
            assert callable(tool_config["function"])
            assert isinstance(tool_config["parameter_descriptions"], dict)
