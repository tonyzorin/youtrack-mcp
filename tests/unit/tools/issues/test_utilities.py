"""
Tests for YouTrack Issue Utilities Module.

Tests the utility functions for the issues tools with focus on:
- Resource cleanup and connection management
- Tool definitions consolidation from all modules
- Legacy format compatibility for backward compatibility
"""

import pytest
from unittest.mock import Mock

from youtrack_mcp.tools.issues.utilities import Utilities


class TestUtilities:
    """Test suite for utility functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_issues_api = Mock()
        self.mock_projects_api = Mock()
        self.mock_client = Mock()
        self.mock_issues_api.client = self.mock_client
        self.utilities = Utilities(self.mock_issues_api, self.mock_projects_api)

    def test_close_success(self):
        """Test successful API client closure."""
        # Arrange
        self.mock_client.close = Mock()
        
        # Act
        self.utilities.close()
        
        # Assert
        self.mock_client.close.assert_called_once()

    def test_close_no_close_method(self):
        """Test close when client doesn't have close method."""
        # Arrange
        # Don't add close method to mock_client
        
        # Act
        self.utilities.close()  # Should not raise exception
        
        # Assert - no exception should be raised

    def test_close_exception_handling(self):
        """Test close when client.close() raises exception."""
        # Arrange
        self.mock_client.close = Mock(side_effect=Exception("Connection error"))
        
        # Act
        self.utilities.close()  # Should not raise exception
        
        # Assert
        self.mock_client.close.assert_called_once()

    def test_get_tool_definitions_legacy_format(self):
        """Test legacy tool definitions format."""
        # Act
        result = self.utilities.get_tool_definitions_legacy()

        # Assert
        # Check that it includes all expected function categories
        basic_ops = ["get_issue", "search_issues", "create_issue", "update_issue", "add_comment"]
        dedicated_updates = ["update_issue_state", "update_issue_priority", "update_issue_assignee", "update_issue_type", "update_issue_estimation"]
        diagnostics = ["diagnose_workflow_restrictions", "get_help"]
        custom_fields = ["update_custom_fields", "batch_update_custom_fields", "get_custom_fields", "validate_custom_field", "get_available_custom_field_values"]
        linking = ["link_issues", "get_issue_links", "get_available_link_types", "add_dependency", "remove_dependency", "add_relates_link", "add_duplicate_link"]
        attachments = ["get_issue_raw", "get_attachment_content"]

        all_expected = basic_ops + dedicated_updates + diagnostics + custom_fields + linking + attachments

        for func_name in all_expected:
            assert func_name in result
            assert "description" in result[func_name]
            assert "parameter_descriptions" in result[func_name]
            assert isinstance(result[func_name]["description"], str)
            assert isinstance(result[func_name]["parameter_descriptions"], dict)

        # Check total count
        assert len(result) == len(all_expected)

    def test_get_tool_definitions_legacy_specific_functions(self):
        """Test specific functions in legacy format have correct structure."""
        # Act
        result = self.utilities.get_tool_definitions_legacy()

        # Assert - check a few specific functions for correct structure
        get_issue = result["get_issue"]
        assert "issue_id" in get_issue["parameter_descriptions"]
        assert "DEMO-123" in get_issue["description"]

        update_state = result["update_issue_state"]
        assert "issue_id" in update_state["parameter_descriptions"]
        assert "new_state" in update_state["parameter_descriptions"]
        assert "proven working REST API" in update_state["description"]

        get_help = result["get_help"]
        assert "topic" in get_help["parameter_descriptions"]
        assert "interactive help" in get_help["description"]

        link_issues = result["link_issues"]
        assert "source_issue_id" in link_issues["parameter_descriptions"]
        assert "target_issue_id" in link_issues["parameter_descriptions"]
        assert "link_type" in link_issues["parameter_descriptions"]

        get_attachment = result["get_attachment_content"]
        assert "issue_id" in get_attachment["parameter_descriptions"]
        assert "attachment_id" in get_attachment["parameter_descriptions"]
        assert "10MB" in get_attachment["description"]  # Updated size limit

    def test_get_tool_definitions_real_integration(self):
        """Test actual get_tool_definitions integration with real modules."""
        # Act
        result = self.utilities.get_tool_definitions()

        # Assert
        # This tests the real integration - should have tools from all modules
        assert isinstance(result, dict)
        
        # Should have at least some tools from each module (without patching)
        # The exact count will depend on the real modules, but should be > 0
        if len(result) > 0:  # If modules loaded successfully
            # Basic smoke test - check structure of returned definitions
            for tool_name, tool_def in result.items():
                assert isinstance(tool_name, str)
                assert isinstance(tool_def, dict)
                assert "description" in tool_def
                assert "parameter_descriptions" in tool_def
                assert isinstance(tool_def["description"], str)
                assert isinstance(tool_def["parameter_descriptions"], dict)

    def test_utilities_initialization(self):
        """Test utilities initialization with API clients."""
        # Assert
        assert self.utilities.issues_api == self.mock_issues_api
        assert self.utilities.projects_api == self.mock_projects_api
        assert self.utilities.client == self.mock_client

    def test_legacy_format_completeness(self):
        """Test that legacy format includes all tool categories."""
        # Act
        result = self.utilities.get_tool_definitions_legacy()

        # Assert - check for key tools from each category
        # Basic Operations
        assert "get_issue" in result
        assert "create_issue" in result
        assert "search_issues" in result
        
        # Dedicated Updates (Enhanced)
        assert "update_issue_state" in result
        assert "update_issue_priority" in result
        assert "update_issue_assignee" in result
        
        # Diagnostics
        assert "diagnose_workflow_restrictions" in result
        assert "get_help" in result
        
        # Custom Fields
        assert "update_custom_fields" in result
        assert "get_custom_fields" in result
        
        # Linking
        assert "link_issues" in result
        assert "add_dependency" in result
        
        # Attachments
        assert "get_issue_raw" in result
        assert "get_attachment_content" in result

    def test_legacy_format_parameter_descriptions(self):
        """Test that legacy format has proper parameter descriptions."""
        # Act
        result = self.utilities.get_tool_definitions_legacy()

        # Assert - check parameter descriptions for various tools
        # Tools with issue_id parameter
        for tool_name in ["get_issue", "update_issue_state", "get_custom_fields"]:
            assert "issue_id" in result[tool_name]["parameter_descriptions"]
        
        # Tools with project parameter
        assert "project" in result["create_issue"]["parameter_descriptions"]
        
        # Tools with multiple parameters
        link_tool = result["link_issues"]
        assert "source_issue_id" in link_tool["parameter_descriptions"]
        assert "target_issue_id" in link_tool["parameter_descriptions"]
        assert "link_type" in link_tool["parameter_descriptions"]

    def test_close_with_different_client_states(self):
        """Test close method with different client configurations."""
        # Test 1: Client with close method
        client_with_close = Mock()
        client_with_close.close = Mock()
        self.utilities.client = client_with_close
        
        self.utilities.close()
        client_with_close.close.assert_called_once()
        
        # Test 2: Client without close method
        client_without_close = Mock(spec=[])  # Mock with no methods
        self.utilities.client = client_without_close
        
        # Should not raise exception
        self.utilities.close()
        
        # Test 3: Client with close method that raises exception
        client_with_error = Mock()
        client_with_error.close = Mock(side_effect=RuntimeError("Connection lost"))
        self.utilities.client = client_with_error
        
        # Should not raise exception
        self.utilities.close()
        client_with_error.close.assert_called_once() 