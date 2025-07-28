"""
Tests for YouTrack Issue Custom Fields Module.

Tests the custom field management functions with focus on:
- Field value updates with validation
- Batch operations with comprehensive results
- Field validation against project schemas
- Available value retrieval for enum/state fields
- Error handling and edge cases
"""

import json
import pytest
from unittest.mock import Mock, patch

from youtrack_mcp.tools.issues.custom_fields import CustomFields


class TestCustomFields:
    """Test suite for custom field functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_issues_api = Mock()
        self.mock_projects_api = Mock()
        self.custom_fields = CustomFields(self.mock_issues_api, self.mock_projects_api)

    def test_update_custom_fields_success(self):
        """Test successful custom field update."""
        # Arrange
        issue_id = "DEMO-123"
        custom_fields_input = {"Priority": "Critical", "Assignee": "admin"}
        mock_updated_issue = {
            "id": "3-123",
            "summary": "Test issue",
            "customFields": [
                {"name": "Priority", "value": {"name": "Critical"}},
                {"name": "Assignee", "value": {"login": "admin"}}
            ]
        }
        
        self.mock_issues_api.update_issue_custom_fields.return_value = mock_updated_issue
        
        # Act
        result = self.custom_fields.update_custom_fields(
            issue_id=issue_id,
            custom_fields=custom_fields_input,
            validate=True
        )
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "success"
        assert result_data["issue_id"] == issue_id
        assert result_data["updated_fields"] == ["Priority", "Assignee"]
        assert result_data["message"] == "Updated 2 custom field(s)"
        assert "issue_data" in result_data
        
        # Verify API call
        self.mock_issues_api.update_issue_custom_fields.assert_called_once_with(
            issue_id=issue_id,
            custom_fields=custom_fields_input,
            validate=True
        )

    def test_update_custom_fields_missing_issue_id(self):
        """Test update_custom_fields with missing issue ID."""
        # Act
        result = self.custom_fields.update_custom_fields(
            issue_id="",
            custom_fields={"Priority": "High"}
        )
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "error"
        assert "Issue ID is required" in result_data["error"]

    def test_update_custom_fields_missing_fields(self):
        """Test update_custom_fields with missing custom fields."""
        # Act
        result = self.custom_fields.update_custom_fields(
            issue_id="DEMO-123",
            custom_fields={}
        )
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "error"
        assert "Custom fields dictionary is required" in result_data["error"]

    def test_update_custom_fields_api_error(self):
        """Test update_custom_fields when API call fails."""
        # Arrange
        issue_id = "DEMO-123"
        custom_fields_input = {"Priority": "Invalid"}
        
        self.mock_issues_api.update_issue_custom_fields.side_effect = Exception("Validation failed")
        
        # Act
        result = self.custom_fields.update_custom_fields(
            issue_id=issue_id,
            custom_fields=custom_fields_input
        )
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "error"
        assert "Validation failed" in result_data["error"]
        assert result_data["issue_id"] == issue_id
        assert result_data["attempted_fields"] == ["Priority"]

    def test_batch_update_custom_fields_success(self):
        """Test successful batch custom field update."""
        # Arrange
        updates = [
            {"issue_id": "DEMO-123", "fields": {"Priority": "High"}},
            {"issue_id": "DEMO-124", "fields": {"Assignee": "jane.doe"}}
        ]
        mock_results = [
            {"status": "success", "issue_id": "DEMO-123"},
            {"status": "success", "issue_id": "DEMO-124"}
        ]
        
        self.mock_issues_api.batch_update_custom_fields.return_value = mock_results
        
        # Act
        result = self.custom_fields.batch_update_custom_fields(updates)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "completed"
        assert result_data["summary"]["total"] == 2
        assert result_data["summary"]["successful"] == 2
        assert result_data["summary"]["errors"] == 0
        assert result_data["summary"]["skipped"] == 0
        assert result_data["results"] == mock_results
        
        # Verify API call
        self.mock_issues_api.batch_update_custom_fields.assert_called_once_with(updates)

    def test_batch_update_custom_fields_mixed_results(self):
        """Test batch update with mixed success/error results."""
        # Arrange
        updates = [
            {"issue_id": "DEMO-123", "fields": {"Priority": "High"}},
            {"issue_id": "DEMO-124", "fields": {"Priority": "Invalid"}},
            {"issue_id": "DEMO-125", "fields": {"Assignee": "admin"}}
        ]
        mock_results = [
            {"status": "success", "issue_id": "DEMO-123"},
            {"status": "error", "issue_id": "DEMO-124", "error": "Invalid priority"},
            {"status": "skipped", "issue_id": "DEMO-125", "reason": "No permissions"}
        ]
        
        self.mock_issues_api.batch_update_custom_fields.return_value = mock_results
        
        # Act
        result = self.custom_fields.batch_update_custom_fields(updates)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "completed"
        assert result_data["summary"]["total"] == 3
        assert result_data["summary"]["successful"] == 1
        assert result_data["summary"]["errors"] == 1
        assert result_data["summary"]["skipped"] == 1

    def test_batch_update_custom_fields_empty_updates(self):
        """Test batch update with empty updates list."""
        # Act
        result = self.custom_fields.batch_update_custom_fields([])
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "error"
        assert "Either 'updates' list or both 'issues' and 'custom_fields' parameters are required" in result_data["error"]

    def test_batch_update_custom_fields_api_error(self):
        """Test batch update when API call fails."""
        # Arrange
        updates = [{"issue_id": "DEMO-123", "fields": {"Priority": "High"}}]
        self.mock_issues_api.batch_update_custom_fields.side_effect = Exception("API Error")
        
        # Act
        result = self.custom_fields.batch_update_custom_fields(updates)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "error"
        assert "API Error" in result_data["error"]
        assert result_data["attempted_updates"] == 1

    def test_get_custom_fields_success(self):
        """Test successful get custom fields."""
        # Arrange
        issue_id = "DEMO-123"
        mock_custom_fields = [
            {"name": "Priority", "value": {"name": "High"}},
            {"name": "State", "value": {"name": "Open"}},
            {"name": "Assignee", "value": {"login": "admin"}}
        ]
        
        self.mock_issues_api.get_issue_custom_fields.return_value = mock_custom_fields
        
        # Act
        result = self.custom_fields.get_custom_fields(issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "success"
        assert result_data["issue_id"] == issue_id
        assert result_data["custom_fields"] == mock_custom_fields
        assert result_data["field_count"] == 3
        
        # Verify API call
        self.mock_issues_api.get_issue_custom_fields.assert_called_once_with(issue_id)

    def test_get_custom_fields_missing_issue_id(self):
        """Test get_custom_fields with missing issue ID."""
        # Act
        result = self.custom_fields.get_custom_fields("")
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "error"
        assert "Issue ID is required" in result_data["error"]

    def test_get_custom_fields_api_error(self):
        """Test get_custom_fields when API call fails."""
        # Arrange
        issue_id = "DEMO-123"
        self.mock_issues_api.get_issue_custom_fields.side_effect = Exception("Not found")
        
        # Act
        result = self.custom_fields.get_custom_fields(issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "error"
        assert "Not found" in result_data["error"]
        assert result_data["issue_id"] == issue_id

    def test_validate_custom_field_success(self):
        """Test successful custom field validation."""
        # Arrange
        project_id = "DEMO"
        field_name = "Priority"
        field_value = "Critical"
        mock_validation_result = {
            "valid": True,
            "field": field_name,
            "value": field_value,
            "message": "Value is valid"
        }
        
        self.mock_issues_api.validate_custom_field_value.return_value = mock_validation_result
        
        # Act
        result = self.custom_fields.validate_custom_field(project_id, field_name, field_value)
        result_data = json.loads(result)
        
        # Assert
        assert result_data == mock_validation_result
        
        # Verify API call
        self.mock_issues_api.validate_custom_field_value.assert_called_once_with(
            project_id=project_id,
            field_name=field_name,
            field_value=field_value
        )

    def test_validate_custom_field_missing_parameters(self):
        """Test validate_custom_field with missing parameters."""
        # Test missing project ID
        result = self.custom_fields.validate_custom_field("", "Priority", "High")
        result_data = json.loads(result)
        assert result_data["status"] == "error"
        assert "Project ID and field name are required" in result_data["error"]
        
        # Test missing field name
        result = self.custom_fields.validate_custom_field("DEMO", "", "High")
        result_data = json.loads(result)
        assert result_data["status"] == "error"
        assert "Project ID and field name are required" in result_data["error"]

    def test_validate_custom_field_api_error(self):
        """Test validate_custom_field when API call fails."""
        # Arrange
        project_id = "DEMO"
        field_name = "Priority"
        field_value = "Invalid"
        
        self.mock_issues_api.validate_custom_field_value.side_effect = Exception("Validation error")
        
        # Act
        result = self.custom_fields.validate_custom_field(project_id, field_name, field_value)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["valid"] is False
        assert "Validation error" in result_data["error"]
        assert result_data["field"] == field_name
        assert result_data["value"] == field_value

    def test_get_available_custom_field_values_success(self):
        """Test successful get available custom field values."""
        # Arrange
        project_id = "DEMO"
        field_name = "Priority"
        mock_allowed_values = ["Critical", "Major", "Normal", "Minor"]
        
        self.mock_projects_api.get_custom_field_allowed_values.return_value = mock_allowed_values
        
        # Act
        result = self.custom_fields.get_available_custom_field_values(project_id, field_name)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "success"
        assert result_data["project_id"] == project_id
        assert result_data["field_name"] == field_name
        assert result_data["allowed_values"] == mock_allowed_values
        assert result_data["value_count"] == 4
        
        # Verify API call
        self.mock_projects_api.get_custom_field_allowed_values.assert_called_once_with(
            project_id, field_name
        )

    def test_get_available_custom_field_values_missing_parameters(self):
        """Test get_available_custom_field_values with missing parameters."""
        # Test missing project ID
        result = self.custom_fields.get_available_custom_field_values("", "Priority")
        result_data = json.loads(result)
        assert result_data["status"] == "error"
        assert "Project ID and field name are required" in result_data["error"]
        
        # Test missing field name
        result = self.custom_fields.get_available_custom_field_values("DEMO", "")
        result_data = json.loads(result)
        assert result_data["status"] == "error"
        assert "Project ID and field name are required" in result_data["error"]

    def test_get_available_custom_field_values_api_error(self):
        """Test get_available_custom_field_values when API call fails."""
        # Arrange
        project_id = "DEMO"
        field_name = "Priority"
        
        self.mock_projects_api.get_custom_field_allowed_values.side_effect = Exception("Field not found")
        
        # Act
        result = self.custom_fields.get_available_custom_field_values(project_id, field_name)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "error"
        assert "Field not found" in result_data["error"]
        assert result_data["project_id"] == project_id
        assert result_data["field_name"] == field_name

    def test_get_tool_definitions(self):
        """Test tool definitions for custom field functions."""
        # Act
        definitions = self.custom_fields.get_tool_definitions()
        
        # Assert
        expected_functions = [
            "update_custom_fields",
            "batch_update_custom_fields",
            "get_custom_fields",
            "validate_custom_field",
            "get_available_custom_field_values"
        ]
        
        for func_name in expected_functions:
            assert func_name in definitions
            assert "description" in definitions[func_name]
            assert "parameter_descriptions" in definitions[func_name]
        
        # Check specific parameter descriptions
        update_def = definitions["update_custom_fields"]
        assert "issue_id" in update_def["parameter_descriptions"]
        assert "custom_fields" in update_def["parameter_descriptions"]
        assert "validate" in update_def["parameter_descriptions"]
        
        batch_def = definitions["batch_update_custom_fields"]
        assert "updates" in batch_def["parameter_descriptions"]
        
        get_def = definitions["get_custom_fields"]
        assert "issue_id" in get_def["parameter_descriptions"]
        
        validate_def = definitions["validate_custom_field"]
        assert "project_id" in validate_def["parameter_descriptions"]
        assert "field_name" in validate_def["parameter_descriptions"]
        assert "field_value" in validate_def["parameter_descriptions"]
        
        available_def = definitions["get_available_custom_field_values"]
        assert "project_id" in available_def["parameter_descriptions"]
        assert "field_name" in available_def["parameter_descriptions"]

    def test_update_custom_fields_with_model_dump_response(self):
        """Test update_custom_fields when response has model_dump method."""
        # Arrange
        issue_id = "DEMO-123"
        custom_fields_input = {"Priority": "Critical"}
        
        mock_updated_issue = Mock()
        mock_updated_issue.model_dump.return_value = {"id": "3-123", "summary": "Test"}
        
        self.mock_issues_api.update_issue_custom_fields.return_value = mock_updated_issue
        
        # Act
        result = self.custom_fields.update_custom_fields(
            issue_id=issue_id,
            custom_fields=custom_fields_input
        )
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "success"
        assert result_data["issue_data"] == {"id": "3-123", "summary": "Test"}
        mock_updated_issue.model_dump.assert_called_once()

    def test_update_custom_fields_without_validation(self):
        """Test update_custom_fields with validation disabled."""
        # Arrange
        issue_id = "DEMO-123"
        custom_fields_input = {"Priority": "Critical"}
        mock_updated_issue = {"id": "3-123"}
        
        self.mock_issues_api.update_issue_custom_fields.return_value = mock_updated_issue
        
        # Act
        result = self.custom_fields.update_custom_fields(
            issue_id=issue_id,
            custom_fields=custom_fields_input,
            validate=False
        )
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "success"
        
        # Verify API call with validation=False
        self.mock_issues_api.update_issue_custom_fields.assert_called_once_with(
            issue_id=issue_id,
            custom_fields=custom_fields_input,
            validate=False
        ) 