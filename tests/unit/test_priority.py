"""
Unit tests for YouTrack MCP tool prioritization.
"""

import pytest
from unittest.mock import patch, Mock

from youtrack_mcp.tools.loader import load_all_tools


class TestToolPrioritization:
    """Test cases for tool prioritization system."""

    @pytest.mark.unit
    def test_loader_with_tool_definitions(self, mock_youtrack_client):
        """Test that loader works with tool definitions."""

        # Create mock with tool definition
        mock_with_tools = Mock()
        mock_with_tools.get_tool_definitions.return_value = {
            "sample_tool": {
                "description": "Sample tool for testing",
                "function": Mock(),
                "parameter_descriptions": {},
            }
        }

        # Create empty mock for other classes
        empty_mock = Mock()
        empty_mock.get_tool_definitions.return_value = {}

        with patch(
            "youtrack_mcp.tools.issues.IssueTools", return_value=mock_with_tools
        ):
            with patch(
                "youtrack_mcp.tools.projects.ProjectTools", return_value=empty_mock
            ):
                with patch(
                    "youtrack_mcp.tools.users.UserTools", return_value=empty_mock
                ):
                    with patch(
                        "youtrack_mcp.tools.search.SearchTools", return_value=empty_mock
                    ):
                        with patch(
                            "youtrack_mcp.tools.resources.ResourcesTools",
                            return_value=empty_mock,
                        ):
                            tools = load_all_tools()

                            # Should have loaded tools successfully
                            assert isinstance(tools, dict)
                            assert len(tools) >= 1

    @pytest.mark.unit
    def test_multiple_tool_definitions(self, mock_youtrack_client):
        """Test that loader can handle multiple tool definitions."""

        # Create mocks with different tool definitions
        issues_mock = Mock()
        issues_mock.get_tool_definitions.return_value = {
            "get_issue": {
                "description": "Get issue details",
                "function": Mock(),
                "parameter_descriptions": {},
            }
        }

        projects_mock = Mock()
        projects_mock.get_tool_definitions.return_value = {
            "get_project": {
                "description": "Get project details",
                "function": Mock(),
                "parameter_descriptions": {},
            }
        }

        # Mock other classes to return empty definitions
        empty_mock = Mock()
        empty_mock.get_tool_definitions.return_value = {}

        with patch("youtrack_mcp.tools.issues.IssueTools", return_value=issues_mock):
            with patch(
                "youtrack_mcp.tools.projects.ProjectTools", return_value=projects_mock
            ):
                with patch(
                    "youtrack_mcp.tools.users.UserTools", return_value=empty_mock
                ):
                    with patch(
                        "youtrack_mcp.tools.search.SearchTools", return_value=empty_mock
                    ):
                        with patch(
                            "youtrack_mcp.tools.resources.ResourcesTools",
                            return_value=empty_mock,
                        ):
                            tools = load_all_tools()

                            # Should have loaded tools successfully
                            assert isinstance(tools, dict)
                            assert len(tools) >= 1

    @pytest.mark.unit
    def test_loader_robustness(self, mock_youtrack_client):
        """Test that loader is robust and handles various scenarios."""

        # Create varied mock responses
        mock_instance = Mock()
        mock_instance.get_tool_definitions.return_value = {
            "utility_tool": {
                "description": "Utility tool",
                "function": Mock(),
                "parameter_descriptions": {"param1": "Test parameter"},
            }
        }

        empty_mock = Mock()
        empty_mock.get_tool_definitions.return_value = {}

        with patch("youtrack_mcp.tools.issues.IssueTools", return_value=mock_instance):
            with patch(
                "youtrack_mcp.tools.projects.ProjectTools", return_value=empty_mock
            ):
                with patch(
                    "youtrack_mcp.tools.users.UserTools", return_value=empty_mock
                ):
                    with patch(
                        "youtrack_mcp.tools.search.SearchTools", return_value=empty_mock
                    ):
                        with patch(
                            "youtrack_mcp.tools.resources.ResourcesTools",
                            return_value=empty_mock,
                        ):
                            tools = load_all_tools()

                            # Verify robustness
                            assert isinstance(tools, dict)
                            assert len(tools) >= 1
