"""
Tests for YouTrack Issue Dedicated Updates Module.

Tests the 5 specialized update functions with focus on:
- Enhanced workflow error handling
- Specific guidance messages
- Proven simple string format validation
- Fallback mechanisms
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from youtrack_mcp.tools.issues.dedicated_updates import DedicatedUpdates
from youtrack_mcp.api.client import YouTrackAPIError


class TestDedicatedUpdates:
    """Test suite for dedicated update functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_issues_api = Mock()
        self.mock_projects_api = Mock()
        self.dedicated_updates = DedicatedUpdates(self.mock_issues_api, self.mock_projects_api)

    def test_update_issue_state_success_direct_api(self):
        """Test successful state update using direct API."""
        # Arrange
        issue_id = "DEMO-123"
        new_state = "In Progress"
        mock_issue = {"id": "3-123", "idReadable": "DEMO-123", "summary": "Test issue"}
        
        self.mock_issues_api._apply_direct_state_update.return_value = True
        self.mock_issues_api.get_issue.return_value = mock_issue
        
        # Act
        result = self.dedicated_updates.update_issue_state(issue_id, new_state)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "success"
        assert result_data["issue_id"] == issue_id
        assert result_data["new_state"] == new_state
        assert result_data["api_method"] == "Direct Field Update API"
        assert "Successfully updated" in result_data["message"]
        
        self.mock_issues_api._apply_direct_state_update.assert_called_once_with(issue_id, new_state)
        self.mock_issues_api.get_issue.assert_called_once_with(issue_id)

    def test_update_issue_state_fallback_to_commands_api(self):
        """Test fallback to Commands API when direct API fails."""
        # Arrange
        issue_id = "DEMO-123"
        new_state = "Fixed"
        mock_issue = {"id": "3-123", "idReadable": "DEMO-123"}
        
        self.mock_issues_api._apply_direct_state_update.return_value = False
        self.mock_issues_api.client.post.return_value = {}
        self.mock_issues_api.get_issue.return_value = mock_issue
        
        # Act
        result = self.dedicated_updates.update_issue_state(issue_id, new_state)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "success"
        assert result_data["api_method"] == "Commands API (fallback)"
        
        # Verify Commands API was called
        expected_command_data = {
            "query": f"State \"{new_state}\"",
            "issues": [{"id": issue_id}]
        }
        self.mock_issues_api.client.post.assert_called_once_with("commands", data=expected_command_data)

    def test_update_issue_state_workflow_restriction_submitted_to_open(self):
        """Test specific workflow guidance for Submitted → Open restriction."""
        # Arrange
        issue_id = "DEMO-123"
        new_state = "Open"
        current_issue = {
            "customFields": [
                {"name": "State", "value": {"name": "Submitted"}}
            ]
        }
        
        self.mock_issues_api._apply_direct_state_update.return_value = False
        self.mock_issues_api.client.post.side_effect = YouTrackAPIError("status 405")
        self.mock_issues_api.get_issue.return_value = current_issue
        
        # Act
        result = self.dedicated_updates.update_issue_state(issue_id, new_state)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["workflow_restriction"] is True
        assert "Transition from 'Submitted' to 'Open'" in result_data["error"]
        
        specific_guidance = result_data["specific_guidance"]
        assert len(specific_guidance) > 0
        assert any("WORKFLOW RESTRICTION" in guidance for guidance in specific_guidance)
        assert any("Move to 'In Progress'" in guidance for guidance in specific_guidance)
        assert any("Once submitted/reviewed" in guidance for guidance in specific_guidance)

    def test_update_issue_state_workflow_restriction_in_progress_needs_assignee(self):
        """Test specific guidance for In Progress requiring assignee."""
        # Arrange
        issue_id = "DEMO-123"
        new_state = "In Progress"
        current_issue = {
            "customFields": [
                {"name": "State", "value": {"name": "Open"}}
            ]
        }
        
        self.mock_issues_api._apply_direct_state_update.return_value = False
        # Use "Failed to transition" to trigger the workflow restriction detection
        self.mock_issues_api.client.post.side_effect = YouTrackAPIError("Failed to transition: assignee required")
        self.mock_issues_api.get_issue.return_value = current_issue
        
        # Act
        result = self.dedicated_updates.update_issue_state(issue_id, new_state)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["workflow_restriction"] is True
        
        specific_guidance = result_data["specific_guidance"]
        assert any("may require an assignee" in guidance for guidance in specific_guidance)
        assert any("update_issue_assignee()" in guidance for guidance in specific_guidance)
        assert any(f"update_issue_assignee('{issue_id}', 'admin')" in guidance for guidance in specific_guidance)

    def test_update_issue_state_http_405_error_handling(self):
        """Test specific guidance for HTTP 405 errors."""
        # Arrange
        issue_id = "DEMO-123"
        new_state = "Open"
        
        self.mock_issues_api._apply_direct_state_update.return_value = False
        self.mock_issues_api.client.post.side_effect = YouTrackAPIError("API request failed with status 405")
        self.mock_issues_api.get_issue.side_effect = Exception("Failed to get issue")
        
        # Act
        result = self.dedicated_updates.update_issue_state(issue_id, new_state)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["workflow_restriction"] is True
        
        specific_guidance = result_data["specific_guidance"]
        assert any("HTTP 405 indicates this operation is not allowed" in guidance for guidance in specific_guidance)
        assert any("Forward transitions like 'In Progress' or 'Fixed'" in guidance for guidance in specific_guidance)

    def test_update_issue_state_missing_parameters(self):
        """Test error handling for missing parameters."""
        # Test missing issue_id
        result = self.dedicated_updates.update_issue_state("", "In Progress")
        result_data = json.loads(result)
        assert "Both issue ID and new state are required" in result_data["error"]
        
        # Test missing new_state
        result = self.dedicated_updates.update_issue_state("DEMO-123", "")
        result_data = json.loads(result)
        assert "Both issue ID and new state are required" in result_data["error"]

    @patch('youtrack_mcp.tools.issues.custom_fields.CustomFields')
    def test_update_issue_priority_success(self, mock_custom_fields_class):
        """Test successful priority update."""
        # Arrange
        issue_id = "DEMO-123"
        new_priority = "Critical"
        
        mock_custom_fields = Mock()
        mock_custom_fields_class.return_value = mock_custom_fields
        mock_custom_fields.update_custom_fields.return_value = json.dumps({
            "status": "success",
            "updated_fields": ["Priority"],
            "issue_data": {"id": "3-123"}
        })
        
        # Act
        result = self.dedicated_updates.update_issue_priority(issue_id, new_priority)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "success"
        assert result_data["new_priority"] == new_priority
        assert result_data["api_method"] == "Direct Field Update API"
        
        mock_custom_fields.update_custom_fields.assert_called_once_with(
            issue_id=issue_id,
            custom_fields={"Priority": new_priority}
        )

    @patch('youtrack_mcp.tools.issues.custom_fields.CustomFields')
    def test_update_issue_priority_failure_with_guidance(self, mock_custom_fields_class):
        """Test priority update failure with specific guidance."""
        # Arrange
        issue_id = "DEMO-123"
        new_priority = "InvalidPriority"
        
        mock_custom_fields = Mock()
        mock_custom_fields_class.return_value = mock_custom_fields
        mock_custom_fields.update_custom_fields.return_value = json.dumps({
            "status": "error",
            "error": "Field validation failed"
        })
        
        # Act
        result = self.dedicated_updates.update_issue_priority(issue_id, new_priority)
        result_data = json.loads(result)
        
        # Assert
        assert "Priority update failed" in result_data["error"]
        assert result_data["target_priority"] == new_priority
        
        troubleshooting = result_data["troubleshooting"]
        assert any("priority value exists" in item for item in troubleshooting)
        assert any("Common priority values" in item for item in troubleshooting)

    @patch('youtrack_mcp.tools.issues.custom_fields.CustomFields')
    def test_update_issue_assignee_success(self, mock_custom_fields_class):
        """Test successful assignee update."""
        # Arrange
        issue_id = "DEMO-123"
        assignee = "admin"
        
        mock_custom_fields = Mock()
        mock_custom_fields_class.return_value = mock_custom_fields
        mock_custom_fields.update_custom_fields.return_value = json.dumps({
            "status": "success",
            "updated_fields": ["Assignee"],
            "issue_data": {"assignee": {"login": "admin"}}
        })
        
        # Act
        result = self.dedicated_updates.update_issue_assignee(issue_id, assignee)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "success"
        assert result_data["assignee"] == assignee
        assert "Successfully assigned" in result_data["message"]

    @patch('youtrack_mcp.tools.issues.custom_fields.CustomFields')
    def test_update_issue_assignee_user_not_found(self, mock_custom_fields_class):
        """Test assignee update with user not found error."""
        # Arrange
        issue_id = "DEMO-123"
        assignee = "nonexistent_user"
        
        mock_custom_fields = Mock()
        mock_custom_fields_class.return_value = mock_custom_fields
        mock_custom_fields.update_custom_fields.return_value = json.dumps({
            "status": "error",
            "error": "User not found"
        })
        
        # Act
        result = self.dedicated_updates.update_issue_assignee(issue_id, assignee)
        result_data = json.loads(result)
        
        # Assert
        assert "Assignee update failed" in result_data["error"]
        troubleshooting = result_data["troubleshooting"]
        assert any("user exists in your YouTrack instance" in item for item in troubleshooting)
        assert any("Use login names" in item for item in troubleshooting)

    @patch('youtrack_mcp.tools.issues.custom_fields.CustomFields')
    def test_update_issue_type_success(self, mock_custom_fields_class):
        """Test successful type update."""
        # Arrange
        issue_id = "DEMO-123"
        issue_type = "Bug"
        
        mock_custom_fields = Mock()
        mock_custom_fields_class.return_value = mock_custom_fields
        mock_custom_fields.update_custom_fields.return_value = json.dumps({
            "status": "success",
            "updated_fields": ["Type"],
            "issue_data": {"type": {"name": "Bug"}}
        })
        
        # Act
        result = self.dedicated_updates.update_issue_type(issue_id, issue_type)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "success"
        assert result_data["issue_type"] == issue_type

    @patch('youtrack_mcp.tools.issues.custom_fields.CustomFields')
    def test_update_issue_estimation_success(self, mock_custom_fields_class):
        """Test successful estimation update."""
        # Arrange
        issue_id = "DEMO-123"
        estimation = "4h"
        
        mock_custom_fields = Mock()
        mock_custom_fields_class.return_value = mock_custom_fields
        mock_custom_fields.update_custom_fields.return_value = json.dumps({
            "status": "success",
            "updated_fields": ["Estimation"],
            "issue_data": {"estimation": {"text": "4h"}}
        })
        
        # Act
        result = self.dedicated_updates.update_issue_estimation(issue_id, estimation)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "success"
        assert result_data["estimation"] == estimation

    @patch('youtrack_mcp.tools.issues.custom_fields.CustomFields')
    def test_update_issue_estimation_invalid_format(self, mock_custom_fields_class):
        """Test estimation update with invalid format guidance."""
        # Arrange
        issue_id = "DEMO-123"
        estimation = "invalid_format"
        
        mock_custom_fields = Mock()
        mock_custom_fields_class.return_value = mock_custom_fields
        mock_custom_fields.update_custom_fields.return_value = json.dumps({
            "status": "error",
            "error": "Invalid time format"
        })
        
        # Act
        result = self.dedicated_updates.update_issue_estimation(issue_id, estimation)
        result_data = json.loads(result)
        
        # Assert
        assert "Estimation update failed" in result_data["error"]
        troubleshooting = result_data["troubleshooting"]
        assert any("simple time formats" in item for item in troubleshooting)
        
        format_examples = result_data["format_examples"]
        assert any("4h (4 hours)" in item for item in format_examples)
        assert any("2d (2 days)" in item for item in format_examples)

    def test_all_functions_require_both_parameters(self):
        """Test that all update functions require both parameters."""
        functions_to_test = [
            (self.dedicated_updates.update_issue_state, "In Progress"),
            (self.dedicated_updates.update_issue_priority, "Critical"),
            (self.dedicated_updates.update_issue_assignee, "admin"),
            (self.dedicated_updates.update_issue_type, "Bug"),
            (self.dedicated_updates.update_issue_estimation, "4h")
        ]
        
        for func, value in functions_to_test:
            # Test empty issue_id
            with patch('youtrack_mcp.tools.issues.custom_fields.CustomFields'):
                result = func("", value)
                result_data = json.loads(result)
                assert "required" in result_data["error"].lower()
            
            # Test empty value
            with patch('youtrack_mcp.tools.issues.custom_fields.CustomFields'):
                result = func("DEMO-123", "")
                result_data = json.loads(result)
                assert "required" in result_data["error"].lower()

    def test_get_tool_definitions(self):
        """Test tool definitions for all dedicated functions."""
        definitions = self.dedicated_updates.get_tool_definitions()
        
        expected_functions = [
            "update_issue_state",
            "update_issue_priority", 
            "update_issue_assignee",
            "update_issue_type",
            "update_issue_estimation"
        ]
        
        for func_name in expected_functions:
            assert func_name in definitions
            assert "description" in definitions[func_name]
            assert "parameter_descriptions" in definitions[func_name]
            assert "issue_id" in definitions[func_name]["parameter_descriptions"]

    def test_exception_handling(self):
        """Test that all functions handle exceptions gracefully."""
        issue_id = "DEMO-123"
        
        # Mock an exception from the API
        self.mock_issues_api._apply_direct_state_update.side_effect = Exception("API error")
        
        with patch('youtrack_mcp.tools.issues.custom_fields.CustomFields') as mock_cf:
            mock_cf.side_effect = Exception("Custom fields error")
            
            # Test each function handles exceptions
            result = self.dedicated_updates.update_issue_state(issue_id, "Fixed")
            result_data = json.loads(result)
            assert "error" in result_data
            
            result = self.dedicated_updates.update_issue_priority(issue_id, "Critical")
            result_data = json.loads(result)
            assert "error" in result_data 