"""
Unit tests for YouTrack MCP tool loading and prioritization.
"""

import pytest
from unittest.mock import patch, Mock

from youtrack_mcp.tools.loader import load_all_tools


class TestToolLoading:
    """Test cases for tool loading functionality."""

    @pytest.mark.unit
    def test_tool_loading_basic(self, mock_youtrack_client):
        """Test that tools can be loaded without errors."""
        # Create simple mock instances that only have get_tool_definitions
        mock_instance = Mock()
        mock_instance.get_tool_definitions.return_value = {}

        with patch("youtrack_mcp.tools.issues.IssueTools", return_value=mock_instance):
            with patch(
                "youtrack_mcp.tools.projects.ProjectTools", return_value=mock_instance
            ):
                with patch(
                    "youtrack_mcp.tools.users.UserTools", return_value=mock_instance
                ):
                    with patch(
                        "youtrack_mcp.tools.search.SearchTools",
                        return_value=mock_instance,
                    ):
                        with patch(
                            "youtrack_mcp.tools.resources.ResourcesTools",
                            return_value=mock_instance,
                        ):
                            tools = load_all_tools()
                            assert isinstance(tools, dict)

    @pytest.mark.unit
    def test_tool_definitions_integration(self, mock_youtrack_client):
        """Test that tool definitions are properly integrated."""
        # Create mock with a simple tool definition
        mock_instance = Mock()
        mock_instance.get_tool_definitions.return_value = {
            "test_tool": {
                "description": "Test tool",
                "function": Mock(),
                "parameter_descriptions": {},
            }
        }

        # Add a simple callable method to the mock
        mock_instance.test_tool = Mock()

        with patch("youtrack_mcp.tools.issues.IssueTools", return_value=mock_instance):
            with patch(
                "youtrack_mcp.tools.projects.ProjectTools",
                return_value=Mock(get_tool_definitions=Mock(return_value={})),
            ):
                with patch(
                    "youtrack_mcp.tools.users.UserTools",
                    return_value=Mock(get_tool_definitions=Mock(return_value={})),
                ):
                    with patch(
                        "youtrack_mcp.tools.search.SearchTools",
                        return_value=Mock(get_tool_definitions=Mock(return_value={})),
                    ):
                        with patch(
                            "youtrack_mcp.tools.resources.ResourcesTools",
                            return_value=Mock(
                                get_tool_definitions=Mock(return_value={})
                            ),
                        ):
                            tools = load_all_tools()

                            # Check that we get a dictionary
                            assert isinstance(tools, dict)
                            # Should have at least the issue_create_issue tool that's added at the end
                            assert len(tools) >= 1

    @pytest.mark.unit
    def test_loader_handles_empty_tools(self, mock_youtrack_client):
        """Test that loader handles tool classes with no tools gracefully."""

        # Create mock instances that return empty tool definitions
        empty_mock = Mock()
        empty_mock.get_tool_definitions.return_value = {}

        with patch("youtrack_mcp.tools.issues.IssueTools", return_value=empty_mock):
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

                            # Should have tools loaded (at least issue_create_issue)
                            assert isinstance(tools, dict)
                            assert (
                                len(tools) >= 1
                            )  # At least the issue_create_issue tool

    @pytest.mark.unit
    def test_loader_returns_dict(self, mock_youtrack_client):
        """Test that loader always returns a dictionary."""

        # Simple test with minimal mocking
        mock_instance = Mock()
        mock_instance.get_tool_definitions.return_value = {}

        with patch("youtrack_mcp.tools.issues.IssueTools", return_value=mock_instance):
            with patch(
                "youtrack_mcp.tools.projects.ProjectTools", return_value=mock_instance
            ):
                with patch(
                    "youtrack_mcp.tools.users.UserTools", return_value=mock_instance
                ):
                    with patch(
                        "youtrack_mcp.tools.search.SearchTools",
                        return_value=mock_instance,
                    ):
                        with patch(
                            "youtrack_mcp.tools.resources.ResourcesTools",
                            return_value=mock_instance,
                        ):
                            tools = load_all_tools()

                            # Should always return a dictionary
                            assert isinstance(tools, dict)
                            # Keys should be strings (tool names)
                            for key in tools.keys():
                                assert isinstance(key, str)
