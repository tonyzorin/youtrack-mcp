"""
Tests for YouTrack Issue Diagnostics Module.

Tests the diagnostic and help functions with focus on:
- Workflow restriction analysis with accurate detection
- Interactive help system with comprehensive coverage
- Error handling and edge cases
- Tool definitions validation
"""

import json
import pytest
from unittest.mock import Mock, patch

from youtrack_mcp.tools.issues.diagnostics import Diagnostics


class TestDiagnostics:
    """Test suite for diagnostic functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_issues_api = Mock()
        self.mock_projects_api = Mock()
        self.diagnostics = Diagnostics(self.mock_issues_api, self.mock_projects_api)

    def test_diagnose_workflow_restrictions_success_state_machine(self):
        """Test successful workflow analysis for state machine workflow."""
        # Arrange
        issue_id = "DEMO-123"
        mock_issue = {"id": "3-123", "summary": "Test issue"}
        mock_state_fields = [
            {
                "name": "State",
                "$type": "StateMachineIssueCustomField",
                "value": {"name": "Open"},
                "possibleEvents": [
                    {"id": "event-1", "presentation": "Start Progress"},
                    {"id": "event-2", "presentation": "Close Issue"}
                ]
            }
        ]
        
        self.mock_issues_api.get_issue.return_value = mock_issue
        self.mock_issues_api.client.get.return_value = mock_state_fields
        
        # Act
        result = self.diagnostics.diagnose_workflow_restrictions(issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "success"
        workflow_analysis = result_data["workflow_analysis"]
        
        assert workflow_analysis["issue_id"] == issue_id
        assert workflow_analysis["current_state"] == "Open"
        assert workflow_analysis["field_type"] == "StateMachineIssueCustomField"
        assert workflow_analysis["workflow_type"] == "state_machine"
        
        # Check available transitions
        transitions = workflow_analysis["available_transitions"]
        assert len(transitions) == 2
        assert transitions[0]["presentation"] == "Start Progress"
        assert transitions[1]["presentation"] == "Close Issue"
        
        # Check restrictions and recommendations
        assert any("State machine workflow detected" in restriction for restriction in workflow_analysis["restrictions"])
        assert any("event-based transitions" in rec for rec in workflow_analysis["recommendations"])

    def test_diagnose_workflow_restrictions_success_direct_field(self):
        """Test successful workflow analysis for direct field workflow."""
        # Arrange
        issue_id = "DEMO-123"
        mock_issue = {"id": "3-123", "summary": "Test issue"}
        mock_state_fields = [
            {
                "name": "State",
                "$type": "StateIssueCustomField",
                "value": {"name": "In Progress"},
                "possibleEvents": [
                    {"id": "event-1", "presentation": "Complete Work"}
                ]
            }
        ]
        
        self.mock_issues_api.get_issue.return_value = mock_issue
        self.mock_issues_api.client.get.return_value = mock_state_fields
        
        # Act
        result = self.diagnostics.diagnose_workflow_restrictions(issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "success"
        workflow_analysis = result_data["workflow_analysis"]
        
        assert workflow_analysis["workflow_type"] == "direct_field"
        assert workflow_analysis["current_state"] == "In Progress"
        assert any("Direct state updates should work" in rec for rec in workflow_analysis["recommendations"])

    def test_diagnose_workflow_restrictions_no_transitions_available(self):
        """Test workflow analysis when no transitions are available."""
        # Arrange
        issue_id = "DEMO-123"
        mock_issue = {"id": "3-123", "summary": "Test issue"}
        mock_state_fields = [
            {
                "name": "State",
                "$type": "StateIssueCustomField",
                "value": {"name": "Closed"},
                "possibleEvents": []  # No events available
            }
        ]
        
        self.mock_issues_api.get_issue.return_value = mock_issue
        self.mock_issues_api.client.get.return_value = mock_state_fields
        
        # Act
        result = self.diagnostics.diagnose_workflow_restrictions(issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "success"
        workflow_analysis = result_data["workflow_analysis"]
        
        assert len(workflow_analysis["available_transitions"]) == 0
        assert any("No transition events available" in restriction for restriction in workflow_analysis["restrictions"])
        assert any("Check user permissions" in rec for rec in workflow_analysis["recommendations"])

    def test_diagnose_workflow_restrictions_no_state_field(self):
        """Test workflow analysis when no state field is found."""
        # Arrange
        issue_id = "DEMO-123"
        mock_issue = {"id": "3-123", "summary": "Test issue"}
        mock_fields = [
            {"name": "Priority", "$type": "EnumIssueCustomField"},
            {"name": "Assignee", "$type": "UserIssueCustomField"}
        ]
        
        self.mock_issues_api.get_issue.return_value = mock_issue
        self.mock_issues_api.client.get.return_value = mock_fields
        
        # Act
        result = self.diagnostics.diagnose_workflow_restrictions(issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert "No State field found for this issue" in result_data["error"]
        assert result_data["issue_id"] == issue_id

    def test_diagnose_workflow_restrictions_api_error(self):
        """Test workflow analysis when API call fails."""
        # Arrange
        issue_id = "DEMO-123"
        self.mock_issues_api.get_issue.return_value = {"id": "3-123"}
        self.mock_issues_api.client.get.side_effect = Exception("API Error")
        
        # Act
        result = self.diagnostics.diagnose_workflow_restrictions(issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert "Failed to analyze workflow" in result_data["error"]
        assert "API Error" in result_data["error"]
        assert result_data["issue_id"] == issue_id

    def test_diagnose_workflow_restrictions_missing_issue_id(self):
        """Test workflow analysis with missing issue ID."""
        # Act
        result = self.diagnostics.diagnose_workflow_restrictions("")
        result_data = json.loads(result)
        
        # Assert
        assert "Issue ID is required" in result_data["error"]

    def test_diagnose_workflow_restrictions_includes_technical_notes(self):
        """Test that workflow analysis includes technical notes and troubleshooting."""
        # Arrange
        issue_id = "DEMO-123"
        mock_issue = {"id": "3-123"}
        mock_state_fields = [
            {
                "name": "State",
                "$type": "StateIssueCustomField",
                "value": {"name": "Open"},
                "possibleEvents": []
            }
        ]
        
        self.mock_issues_api.get_issue.return_value = mock_issue
        self.mock_issues_api.client.get.return_value = mock_state_fields
        
        # Act
        result = self.diagnostics.diagnose_workflow_restrictions(issue_id)
        result_data = json.loads(result)
        
        # Assert
        workflow_analysis = result_data["workflow_analysis"]
        
        # Check technical notes
        technical_notes = workflow_analysis["technical_notes"]
        assert "command_api" in technical_notes
        assert "direct_api" in technical_notes
        assert "state_machine_api" in technical_notes
        assert "permission_check" in technical_notes
        
        # Check troubleshooting
        troubleshooting = workflow_analysis["troubleshooting"]
        assert len(troubleshooting) > 0
        assert any("Open → In Progress" in item for item in troubleshooting)

    def test_get_help_all_topics(self):
        """Test get_help function with 'all' topic."""
        # Act
        result = self.diagnostics.get_help("all")
        result_data = json.loads(result)
        
        # Assert
        assert result_data["help_topic"] == "all"
        assert "youtrack_help" in result_data
        assert "quick_examples" in result_data
        assert "available_functions" in result_data
        assert "quick_tips" in result_data

    def test_get_help_workflow_topic(self):
        """Test get_help function with 'workflow' topic."""
        # Act
        result = self.diagnostics.get_help("workflow")
        result_data = json.loads(result)
        
        # Assert
        assert result_data["help_topic"] == "workflow"
        assert "workflow_guidance" in result_data
        
        workflow_guidance = result_data["workflow_guidance"]
        assert "common_restrictions" in workflow_guidance
        assert "best_practices" in workflow_guidance
        assert "troubleshooting_steps" in workflow_guidance
        
        # Check specific workflow guidance content
        common_restrictions = workflow_guidance["common_restrictions"]
        assert any("Submitted → Open" in restriction for restriction in common_restrictions)
        assert any("In Progress" in restriction for restriction in common_restrictions)

    def test_get_help_examples_topic(self):
        """Test get_help function with 'examples' topic."""
        # Act
        result = self.diagnostics.get_help("examples")
        result_data = json.loads(result)
        
        # Assert
        assert result_data["help_topic"] == "examples"
        
        quick_examples = result_data["quick_examples"]
        assert "most_common_operations" in quick_examples
        assert "workflow_combinations" in quick_examples
        
        # Check specific examples
        most_common = quick_examples["most_common_operations"]
        assert "move_to_in_progress" in most_common
        assert "set_critical_priority" in most_common
        assert "assign_to_user" in most_common
        assert "change_to_bug" in most_common
        assert "set_estimation" in most_common
        
        # Check workflow combinations
        combinations = quick_examples["workflow_combinations"]
        assert "escalate_issue" in combinations
        assert "complete_issue" in combinations
        assert "triage_new_issue" in combinations

    def test_get_help_functions_topic(self):
        """Test get_help function with 'functions' topic."""
        # Act
        result = self.diagnostics.get_help("functions")
        result_data = json.loads(result)
        
        # Assert
        assert result_data["help_topic"] == "functions"
        
        available_functions = result_data["available_functions"]
        assert "dedicated_updates" in available_functions
        assert "issue_management" in available_functions
        assert "custom_fields" in available_functions
        assert "diagnostics" in available_functions
        
        # Check dedicated updates functions
        dedicated_updates = available_functions["dedicated_updates"]
        assert "update_issue_state" in dedicated_updates
        assert "update_issue_priority" in dedicated_updates
        assert "update_issue_assignee" in dedicated_updates
        assert "update_issue_type" in dedicated_updates
        assert "update_issue_estimation" in dedicated_updates

    def test_get_help_quick_tips_included(self):
        """Test that get_help includes comprehensive quick tips."""
        # Act
        result = self.diagnostics.get_help("all")
        result_data = json.loads(result)
        
        # Assert
        quick_tips = result_data["quick_tips"]
        assert "proven_formats" in quick_tips
        assert "troubleshooting" in quick_tips
        
        # Check proven formats
        proven_formats = quick_tips["proven_formats"]
        assert "states" in proven_formats
        assert "priorities" in proven_formats
        assert "users" in proven_formats
        assert "time" in proven_formats
        
        # Check troubleshooting tips
        troubleshooting = quick_tips["troubleshooting"]
        assert "workflow_errors" in troubleshooting
        assert "field_values" in troubleshooting
        assert "permissions" in troubleshooting
        assert "format_errors" in troubleshooting

    def test_get_help_error_handling(self):
        """Test get_help error handling."""
        # Arrange - simulate an exception during help generation
        with patch.object(self.diagnostics, 'get_help') as mock_get_help:
            mock_get_help.side_effect = Exception("Help generation error")
            
            # Create a new instance to test the actual method
            diagnostics = Diagnostics(self.mock_issues_api, self.mock_projects_api)
            
            # Manually trigger the exception path by mocking format_json_response to raise
            with patch('youtrack_mcp.tools.issues.diagnostics.format_json_response') as mock_format:
                mock_format.side_effect = Exception("Formatting error")
                
                # Act & Assert - this will test the exception handling
                try:
                    result = diagnostics.get_help("all")
                    # If we get here, the exception was handled
                    assert True
                except Exception:
                    # The method should handle exceptions gracefully
                    assert False, "get_help should handle exceptions gracefully"

    def test_get_tool_definitions(self):
        """Test tool definitions for diagnostic functions."""
        # Act
        definitions = self.diagnostics.get_tool_definitions()
        
        # Assert
        expected_functions = [
            "diagnose_workflow_restrictions",
            "get_help"
        ]
        
        for func_name in expected_functions:
            assert func_name in definitions
            assert "description" in definitions[func_name]
            assert "parameter_descriptions" in definitions[func_name]
        
        # Check specific parameter descriptions
        diagnose_def = definitions["diagnose_workflow_restrictions"]
        assert "issue_id" in diagnose_def["parameter_descriptions"]
        
        help_def = definitions["get_help"]
        assert "topic" in help_def["parameter_descriptions"]

    def test_exception_handling_in_diagnose_workflow_restrictions(self):
        """Test exception handling in diagnose_workflow_restrictions."""
        # Arrange
        issue_id = "DEMO-123"
        self.mock_issues_api.get_issue.side_effect = Exception("Database connection error")
        
        # Act
        result = self.diagnostics.diagnose_workflow_restrictions(issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert "error" in result_data
        assert "troubleshooting" in result_data
        
        troubleshooting = result_data["troubleshooting"]
        assert any("Verify issue ID format" in item for item in troubleshooting)
        assert any("Check user permissions" in item for item in troubleshooting)

    def test_diagnose_workflow_includes_all_required_fields(self):
        """Test that diagnose_workflow_restrictions includes all required analysis fields."""
        # Arrange
        issue_id = "DEMO-123"
        mock_issue = {"id": "3-123"}
        mock_state_fields = [
            {
                "name": "State",
                "$type": "StateIssueCustomField",
                "value": {"name": "Open"},
                "possibleEvents": [{"id": "1", "presentation": "Start Work"}]
            }
        ]
        
        self.mock_issues_api.get_issue.return_value = mock_issue
        self.mock_issues_api.client.get.return_value = mock_state_fields
        
        # Act
        result = self.diagnostics.diagnose_workflow_restrictions(issue_id)
        result_data = json.loads(result)
        
        # Assert
        workflow_analysis = result_data["workflow_analysis"]
        
        required_fields = [
            "issue_id", "current_state", "field_type", "workflow_type",
            "available_transitions", "restrictions", "recommendations",
            "technical_notes", "troubleshooting"
        ]
        
        for field in required_fields:
            assert field in workflow_analysis, f"Missing required field: {field}"

    def test_get_help_default_topic_parameter(self):
        """Test get_help with default topic parameter."""
        # Act
        result = self.diagnostics.get_help()  # No topic parameter
        result_data = json.loads(result)
        
        # Assert
        assert result_data["help_topic"] == "all" 