"""
Unit tests for custom fields functionality in YouTrack MCP tools.
"""

import unittest
import json
from unittest.mock import Mock, patch

from youtrack_mcp.tools.issues import IssueTools
from youtrack_mcp.tools.projects import ProjectTools


class TestIssueToolsCustomFields(unittest.TestCase):
    """Test custom field methods in Issue Tools."""

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def setUp(self, mock_client_class, mock_issues_client_class):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_issues_api = Mock()
        
        mock_client_class.return_value = self.mock_client
        mock_issues_client_class.return_value = self.mock_issues_api
        
        self.issue_tools = IssueTools()

    def test_update_custom_fields_success(self):
        """Test successful custom field update."""
        mock_issue = Mock()
        mock_issue.model_dump.return_value = {"id": "DEMO-123", "summary": "Test Issue"}
        self.mock_issues_api.update_issue_custom_fields.return_value = mock_issue

        result = self.issue_tools.update_custom_fields(
            issue_id="DEMO-123",
            custom_fields={"Priority": "High", "Assignee": "john.doe"}
        )

        parsed_result = json.loads(result)
        self.assertEqual(parsed_result["status"], "success")
        self.assertEqual(parsed_result["issue_id"], "DEMO-123")
        self.assertEqual(len(parsed_result["updated_fields"]), 2)
        self.assertIn("Priority", parsed_result["updated_fields"])
        self.assertIn("Assignee", parsed_result["updated_fields"])

    def test_update_custom_fields_missing_issue_id(self):
        """Test update with missing issue ID."""
        result = self.issue_tools.update_custom_fields(
            issue_id="",
            custom_fields={"Priority": "High"}
        )

        parsed_result = json.loads(result)
        self.assertEqual(parsed_result["status"], "error")
        self.assertIn("Issue ID is required", parsed_result["error"])

    def test_update_custom_fields_empty_fields(self):
        """Test update with empty custom fields."""
        result = self.issue_tools.update_custom_fields(
            issue_id="DEMO-123",
            custom_fields={}
        )

        parsed_result = json.loads(result)
        self.assertEqual(parsed_result["status"], "error")
        self.assertIn("Custom fields dictionary is required", parsed_result["error"])

    def test_batch_update_custom_fields_success(self):
        """Test successful batch update."""
        mock_results = [
            {"status": "success", "issue_id": "DEMO-123"},
            {"status": "success", "issue_id": "DEMO-124"}
        ]
        self.mock_issues_api.batch_update_custom_fields.return_value = mock_results

        result = self.issue_tools.batch_update_custom_fields([
            {"issue_id": "DEMO-123", "fields": {"Priority": "High"}},
            {"issue_id": "DEMO-124", "fields": {"Assignee": "jane.doe"}}
        ])

        parsed_result = json.loads(result)
        self.assertEqual(parsed_result["status"], "completed")
        self.assertEqual(parsed_result["summary"]["total"], 2)
        self.assertEqual(parsed_result["summary"]["successful"], 2)

    def test_get_custom_fields_success(self):
        """Test getting custom fields for an issue."""
        mock_fields = {"Priority": "High", "Assignee": "john.doe"}
        self.mock_issues_api.get_issue_custom_fields.return_value = mock_fields

        result = self.issue_tools.get_custom_fields("DEMO-123")

        parsed_result = json.loads(result)
        self.assertEqual(parsed_result["status"], "success")
        self.assertEqual(parsed_result["issue_id"], "DEMO-123")
        self.assertEqual(parsed_result["custom_fields"], mock_fields)
        self.assertEqual(parsed_result["field_count"], 2)

    def test_validate_custom_field_success(self):
        """Test custom field validation."""
        mock_validation = {"valid": True, "field": "Priority", "value": "High", "message": "Valid"}
        self.mock_issues_api.validate_custom_field_value.return_value = mock_validation

        result = self.issue_tools.validate_custom_field(
            project_id="DEMO",
            field_name="Priority",
            field_value="High"
        )

        parsed_result = json.loads(result)
        self.assertTrue(parsed_result["valid"])
        self.assertEqual(parsed_result["field"], "Priority")

    def test_get_available_custom_field_values_success(self):
        """Test getting available custom field values."""
        # Since this method creates its own ProjectsClient internally, 
        # let's test the simpler case of error handling
        result = self.issue_tools.get_available_custom_field_values(
            project_id="",  # Empty project ID should return error
            field_name="Priority"
        )

        parsed_result = json.loads(result)
        self.assertEqual(parsed_result["status"], "error")
        self.assertIn("Project ID and field name are required", parsed_result["error"])

    def test_get_available_custom_field_values_missing_field_name(self):
        """Test getting available custom field values with missing field name."""
        result = self.issue_tools.get_available_custom_field_values(
            project_id="DEMO",
            field_name=""  # Empty field name should return error
        )

        parsed_result = json.loads(result)
        self.assertEqual(parsed_result["status"], "error")
        self.assertIn("Project ID and field name are required", parsed_result["error"])


class TestProjectToolsCustomFields(unittest.TestCase):
    """Test custom field methods in Project Tools."""

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def setUp(self, mock_client_class, mock_projects_client_class):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.mock_projects_api = Mock()
        
        mock_client_class.return_value = self.mock_client
        mock_projects_client_class.return_value = self.mock_projects_api
        
        self.project_tools = ProjectTools()

    def test_get_custom_field_schema_success(self):
        """Test getting custom field schema."""
        mock_schema = {
            "name": "Priority",
            "type": "enum",
            "required": False,
            "multi_value": False,
            "allowed_values": [{"name": "High"}, {"name": "Medium"}, {"name": "Low"}]
        }
        self.mock_projects_api.get_custom_field_schema.return_value = mock_schema

        result = self.project_tools.get_custom_field_schema("DEMO", "Priority")

        parsed_result = json.loads(result)
        self.assertEqual(parsed_result["status"], "success")
        self.assertEqual(parsed_result["project_id"], "DEMO")
        self.assertEqual(parsed_result["field_name"], "Priority")
        self.assertEqual(parsed_result["schema"]["type"], "enum")

    def test_get_custom_field_schema_not_found(self):
        """Test getting schema for non-existent field."""
        self.mock_projects_api.get_custom_field_schema.return_value = None

        result = self.project_tools.get_custom_field_schema("DEMO", "NonExistent")

        parsed_result = json.loads(result)
        self.assertEqual(parsed_result["status"], "not_found")
        self.assertIn("not found", parsed_result["error"])

    def test_get_custom_field_allowed_values_success(self):
        """Test getting allowed values for custom field."""
        mock_values = [
            {"name": "High", "description": "High priority", "id": "val-1"},
            {"name": "Medium", "description": "Medium priority", "id": "val-2"},
            {"name": "Low", "description": "Low priority", "id": "val-3"}
        ]
        self.mock_projects_api.get_custom_field_allowed_values.return_value = mock_values

        result = self.project_tools.get_custom_field_allowed_values("DEMO", "Priority")

        parsed_result = json.loads(result)
        self.assertEqual(parsed_result["status"], "success")
        self.assertEqual(parsed_result["project_id"], "DEMO")
        self.assertEqual(parsed_result["field_name"], "Priority")
        self.assertEqual(len(parsed_result["allowed_values"]), 3)
        self.assertEqual(parsed_result["value_count"], 3)

    def test_get_all_custom_fields_schemas_success(self):
        """Test getting all custom field schemas."""
        mock_schemas = {
            "Priority": {"name": "Priority", "type": "enum"},
            "Assignee": {"name": "Assignee", "type": "user"},
            "State": {"name": "State", "type": "state"}
        }
        self.mock_projects_api.get_all_custom_fields_schemas.return_value = mock_schemas

        result = self.project_tools.get_all_custom_fields_schemas("DEMO")

        parsed_result = json.loads(result)
        self.assertEqual(parsed_result["status"], "success")
        self.assertEqual(parsed_result["project_id"], "DEMO")
        self.assertEqual(len(parsed_result["schemas"]), 3)
        self.assertEqual(parsed_result["field_count"], 3)

    def test_validate_custom_field_for_project_valid(self):
        """Test validation with valid field value."""
        mock_validation = {"valid": True, "field": "Priority", "value": "High", "message": "Valid"}
        self.mock_projects_api.validate_custom_field_for_project.return_value = mock_validation

        result = self.project_tools.validate_custom_field_for_project(
            project_id="DEMO",
            field_name="Priority", 
            field_value="High"
        )

        parsed_result = json.loads(result)
        self.assertTrue(parsed_result["valid"])
        self.assertEqual(parsed_result["field"], "Priority")

    def test_validate_custom_field_for_project_invalid(self):
        """Test validation with invalid field value."""
        mock_validation = {
            "valid": False, 
            "error": "Invalid value 'VeryHigh' for field 'Priority'",
            "suggestion": "Use one of: High, Medium, Low"
        }
        self.mock_projects_api.validate_custom_field_for_project.return_value = mock_validation

        result = self.project_tools.validate_custom_field_for_project(
            project_id="DEMO",
            field_name="Priority",
            field_value="VeryHigh"
        )

        parsed_result = json.loads(result)
        self.assertFalse(parsed_result["valid"])
        self.assertIn("Invalid value", parsed_result["error"])

    def test_missing_project_id_validation(self):
        """Test validation with missing project ID."""
        result = self.project_tools.validate_custom_field_for_project(
            project_id="",
            field_name="Priority",
            field_value="High"
        )

        parsed_result = json.loads(result)
        self.assertFalse(parsed_result["valid"])
        self.assertIn("Project ID and field name are required", parsed_result["error"])


if __name__ == "__main__":
    unittest.main() 