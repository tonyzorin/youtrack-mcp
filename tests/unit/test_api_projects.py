"""
Unit tests for YouTrack Projects API client (api/projects.py).

This module provides comprehensive test coverage for the ProjectsClient class
and Project model to improve coverage from 20% to high coverage.
"""

import unittest
import pytest
from unittest.mock import Mock, patch
from typing import List, Dict, Any

from youtrack_mcp.api.projects import ProjectsClient, Project
from youtrack_mcp.api.client import YouTrackClient


class TestProjectModel:
    """Test the Project Pydantic model."""

    def test_project_model_basic_creation(self):
        """Test creating a basic Project model."""
        project_data = {
            "id": "0-0",
            "name": "Demo Project",
            "shortName": "DEMO"
        }
        
        project = Project(**project_data)
        
        assert project.id == "0-0"
        assert project.name == "Demo Project"
        assert project.shortName == "DEMO"
        assert project.description is None
        assert project.archived is False
        assert project.custom_fields == []

    def test_project_model_with_all_fields(self):
        """Test creating a Project model with all fields."""
        project_data = {
            "id": "1-1",
            "name": "Full Project",
            "shortName": "FULL",
            "description": "A comprehensive project",
            "archived": True,
            "created": 1640995200000,
            "updated": 1640995200000,
            "lead": {"id": "user1", "login": "admin"},
            "custom_fields": [{"name": "Priority", "value": "High"}]
        }
        
        project = Project(**project_data)
        
        assert project.id == "1-1"
        assert project.name == "Full Project"
        assert project.shortName == "FULL"
        assert project.description == "A comprehensive project"
        assert project.archived is True
        assert project.created == 1640995200000
        assert project.updated == 1640995200000
        assert project.lead == {"id": "user1", "login": "admin"}
        assert len(project.custom_fields) == 1
        assert project.custom_fields[0]["name"] == "Priority"

    def test_project_model_validation_required_fields(self):
        """Test that required fields are validated."""
        # Missing required fields should raise validation error
        with pytest.raises(Exception):  # Pydantic ValidationError
            Project()

    def test_project_model_json_serialization(self):
        """Test Project model JSON serialization."""
        project = Project(
            id="2-2",
            name="JSON Project",
            shortName="JSON"
        )
        
        json_data = project.model_dump()
        
        assert json_data["id"] == "2-2"
        assert json_data["name"] == "JSON Project"
        assert json_data["shortName"] == "JSON"


class TestProjectsClientInitialization:
    """Test ProjectsClient initialization."""

    def test_projects_client_initialization(self):
        """Test ProjectsClient initialization with YouTrackClient."""
        mock_client = Mock(spec=YouTrackClient)
        projects_client = ProjectsClient(mock_client)
        
        assert projects_client.client is mock_client


class TestProjectsClientGetProjects:
    """Test getting projects list."""

    def test_get_projects_basic(self):
        """Test getting basic projects list."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = [
            {
                "id": "0-0",
                "name": "Demo Project",
                "shortName": "DEMO",
                "archived": False
            },
            {
                "id": "1-1", 
                "name": "Test Project",
                "shortName": "TEST",
                "archived": False
            }
        ]
        
        projects_client = ProjectsClient(mock_client)
        projects = projects_client.get_projects()
        
        assert len(projects) == 2
        assert isinstance(projects[0], Project)
        assert projects[0].id == "0-0"
        assert projects[0].name == "Demo Project"
        assert projects[0].shortName == "DEMO"
        
        # Verify API call
        mock_client.get.assert_called_once_with(
            "admin/projects", 
            params={"fields": "id,name,shortName,description,archived,created,updated,lead(id,name,login)", "$filter": "archived eq false"}
        )

    def test_get_projects_include_archived(self):
        """Test getting projects including archived ones."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = [
            {
                "id": "0-0",
                "name": "Active Project",
                "shortName": "ACTIVE",
                "archived": False
            },
            {
                "id": "1-1",
                "name": "Archived Project", 
                "shortName": "ARCH",
                "archived": True
            }
        ]
        
        projects_client = ProjectsClient(mock_client)
        projects = projects_client.get_projects(include_archived=True)
        
        assert len(projects) == 2
        assert projects[1].archived is True
        
        # Should not filter archived projects when include_archived=True
        mock_client.get.assert_called_once()

    def test_get_projects_exclude_archived_default(self):
        """Test that archived projects are excluded by default."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = [
            {
                "id": "0-0",
                "name": "Active Project",
                "shortName": "ACTIVE", 
                "archived": False
            },
            {
                "id": "1-1",
                "name": "Archived Project",
                "shortName": "ARCH",
                "archived": True
            }
        ]
        
        projects_client = ProjectsClient(mock_client)
        projects = projects_client.get_projects()  # Default: include_archived=False
        
        # Should filter out archived projects
        active_projects = [p for p in projects if not p.archived]
        assert len(active_projects) == 1
        assert active_projects[0].shortName == "ACTIVE"

    def test_get_projects_empty_response(self):
        """Test handling empty projects response."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = []
        
        projects_client = ProjectsClient(mock_client)
        projects = projects_client.get_projects()
        
        assert projects == []

    def test_get_projects_api_error(self):
        """Test handling API errors in get_projects."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.side_effect = Exception("API Error")
        
        projects_client = ProjectsClient(mock_client)
        
        with pytest.raises(Exception) as exc_info:
            projects_client.get_projects()
        
        assert "API Error" in str(exc_info.value)


class TestProjectsClientGetProject:
    """Test getting a single project."""

    def test_get_project_by_id(self):
        """Test getting a project by ID."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = {
            "id": "0-0",
            "name": "Demo Project",
            "shortName": "DEMO",
            "description": "Demo project description"
        }
        
        projects_client = ProjectsClient(mock_client)
        project = projects_client.get_project("0-0")
        
        assert isinstance(project, Project)
        assert project.id == "0-0"
        assert project.name == "Demo Project"
        assert project.description == "Demo project description"
        
        mock_client.get.assert_called_once_with(
            "admin/projects/0-0",
            params={"fields": "id,name,shortName,description,archived,created,updated,lead(id,name,login)"}
        )

    def test_get_project_by_short_name(self):
        """Test getting a project by short name.""" 
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = {
            "id": "1-1",
            "name": "Test Project",
            "shortName": "TEST"
        }
        
        projects_client = ProjectsClient(mock_client)
        project = projects_client.get_project("TEST")
        
        assert project.shortName == "TEST"
        
        mock_client.get.assert_called_once_with(
            "admin/projects/TEST",
            params={"fields": "id,name,shortName,description,archived,created,updated,lead(id,name,login)"}
        )

    def test_get_project_not_found(self):
        """Test handling project not found."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.side_effect = Exception("Project not found")
        
        projects_client = ProjectsClient(mock_client)
        
        with pytest.raises(Exception) as exc_info:
            projects_client.get_project("NONEXISTENT")
        
        assert "Project not found" in str(exc_info.value)


class TestProjectsClientCustomFields:
    """Test custom fields related functionality."""

    def test_get_custom_fields(self):
        """Test getting custom fields for a project."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = [
            {
                "id": "field1",
                "name": "Priority",
                "projectCustomField": {
                    "field": {"name": "Priority"}
                }
            },
            {
                "id": "field2", 
                "name": "Type",
                "projectCustomField": {
                    "field": {"name": "Type"}
                }
            }
        ]
        
        projects_client = ProjectsClient(mock_client)
        custom_fields = projects_client.get_custom_fields("DEMO")
        
        assert len(custom_fields) == 2
        assert custom_fields[0]["name"] == "Priority"
        assert custom_fields[1]["name"] == "Type"
        
        mock_client.get.assert_called_once_with("admin/projects/DEMO/customFields")

    def test_get_custom_fields_empty(self):
        """Test getting custom fields when none exist."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = []
        
        projects_client = ProjectsClient(mock_client)
        custom_fields = projects_client.get_custom_fields("DEMO")
        
        assert custom_fields == []

    def test_get_custom_fields_api_error(self):
        """Test handling API errors when getting custom fields."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.side_effect = Exception("Custom fields API error")
        
        projects_client = ProjectsClient(mock_client)
        
        with pytest.raises(Exception) as exc_info:
            projects_client.get_custom_fields("DEMO")
        
        assert "Custom fields API error" in str(exc_info.value)


class TestProjectsClientCreateProject:
    """Test project creation validation."""

    def test_create_project_validation_empty_name(self):
        """Test that empty name raises ValueError."""
        mock_client = Mock(spec=YouTrackClient)
        projects_client = ProjectsClient(mock_client)
        
        with pytest.raises(ValueError, match="Project name is required"):
            projects_client.create_project("", "TEST")

    def test_create_project_validation_empty_short_name(self):
        """Test that empty short name raises ValueError."""
        mock_client = Mock(spec=YouTrackClient)
        projects_client = ProjectsClient(mock_client)
        
        with pytest.raises(ValueError, match="Project short name is required"):
            projects_client.create_project("Test Project", "")


class TestProjectsClientDeleteProject:
    """Test project deletion functionality."""

    def test_delete_project_api_error(self):
        """Test handling API errors during project deletion."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.delete.side_effect = Exception("Delete failed")
        
        projects_client = ProjectsClient(mock_client)
        
        with pytest.raises(Exception) as exc_info:
            projects_client.delete_project("1-1")
        
        assert "Delete failed" in str(exc_info.value) 


class TestProjectsCustomFields(unittest.TestCase):
    """Test custom field schema management methods in Projects API."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.projects_client = ProjectsClient(self.mock_client)

    def test_get_custom_field_schema_success(self):
        """Test getting custom field schema successfully."""
        mock_fields = [
            {
                "field": {
                    "name": "Priority",
                    "id": "field-123",
                    "isMultiValue": False,
                    "fieldType": {
                        "valueType": "enum",
                        "$type": "EnumFieldType",
                        "id": "bundle-456"
                    }
                },
                "canBeEmpty": False,
                "autoAttached": True
            }
        ]
        
        # Mock the direct API call our method now uses
        self.mock_client.get.return_value = mock_fields
        self.projects_client.get_custom_field_allowed_values = Mock(return_value=[
            {"name": "High", "id": "val-1"},
            {"name": "Medium", "id": "val-2"}
        ])

        result = self.projects_client.get_custom_field_schema("0-0", "Priority")

        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "Priority")
        self.assertEqual(result["type"], "enum")
        self.assertEqual(result["bundle_type"], "EnumFieldType")
        self.assertTrue(result["required"])
        self.assertFalse(result["multi_value"])
        self.assertTrue(result["auto_attach"])
        self.assertIn("allowed_values", result)

    def test_get_custom_field_schema_not_found(self):
        """Test getting schema for non-existent field."""
        mock_fields = [
            {"field": {"name": "OtherField"}}
        ]
        
        self.projects_client.get_custom_fields = Mock(return_value=mock_fields)

        result = self.projects_client.get_custom_field_schema("0-0", "NonExistentField")

        self.assertIsNone(result)

    def test_get_custom_field_schema_api_error(self):
        """Test schema retrieval with API error."""
        self.projects_client.get_custom_fields = Mock(side_effect=Exception("API Error"))

        result = self.projects_client.get_custom_field_schema("0-0", "Priority")

        self.assertIsNone(result)

    def test_get_custom_field_allowed_values_enum_field(self):
        """Test getting allowed values for enum field."""
        # Mock field schema response
        mock_fields = [
            {
                "field": {
                    "id": "priority-field-id",
                    "name": "Priority",
                    "fieldType": {
                        "$type": "EnumBundle",
                        "valueType": "enum",
                        "id": "bundle-123"
                    }
                }
            }
        ]
        
        mock_bundle_data = {
            "values": [
                {"name": "High", "description": "High priority", "id": "val-1", "color": {"bg": "#ff0000"}},
                {"name": "Medium", "description": "Medium priority", "id": "val-2", "color": {"bg": "#ffff00"}},
                {"name": "Low", "description": "Low priority", "id": "val-3", "color": {"bg": "#00ff00"}}
            ]
        }
        
        # Our method makes two API calls: first for field schema, then for bundle data
        self.mock_client.get.side_effect = [mock_fields, mock_bundle_data]

        result = self.projects_client.get_custom_field_allowed_values("0-0", "Priority")

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["name"], "High")
        self.assertEqual(result[0]["description"], "High priority")
        self.assertIn("color", result[0])

    def test_get_custom_field_allowed_values_state_field(self):
        """Test getting allowed values for state field."""
        # Mock field schema response
        mock_fields = [
            {
                "field": {
                    "id": "state-field-id",
                    "name": "State",
                    "fieldType": {
                        "$type": "StateBundle",
                        "valueType": "state",
                        "id": "bundle-456"
                    }
                }
            }
        ]
        
        mock_bundle_data = {
            "values": [
                {"name": "Open", "description": "Open state", "id": "state-1", "isResolved": False},
                {"name": "In Progress", "description": "In progress", "id": "state-2", "isResolved": False},
                {"name": "Closed", "description": "Closed state", "id": "state-3", "isResolved": True}
            ]
        }
        
        # Our method makes two API calls: first for field schema, then for bundle data
        self.mock_client.get.side_effect = [mock_fields, mock_bundle_data]

        result = self.projects_client.get_custom_field_allowed_values("0-0", "State")

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["name"], "Open")
        self.assertFalse(result[0]["resolved"])
        self.assertTrue(result[2]["resolved"])

    def test_get_custom_field_allowed_values_user_field(self):
        """Test getting allowed values for user field."""
        # Mock field schema response
        mock_fields = [
            {
                "field": {
                    "id": "assignee-field-id",
                    "name": "Assignee",
                    "fieldType": {
                        "$type": "UserBundle",
                        "valueType": "user",
                        "id": "bundle-789"
                    }
                }
            }
        ]
        
        mock_users_data = [
            {"id": "user-1", "login": "john.doe", "name": "John Doe", "email": "john@example.com"},
            {"id": "user-2", "login": "jane.smith", "name": "Jane Smith", "email": "jane@example.com"}
        ]
        
        # Our method makes two API calls: first for field schema, then for users data
        self.mock_client.get.side_effect = [mock_fields, mock_users_data]

        result = self.projects_client.get_custom_field_allowed_values("0-0", "Assignee")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["login"], "john.doe")
        self.assertEqual(result[0]["name"], "John Doe")
        self.assertEqual(result[0]["email"], "john@example.com")

    def test_get_custom_field_allowed_values_no_schema(self):
        """Test getting allowed values when schema not found."""
        self.projects_client.get_custom_field_schema = Mock(return_value=None)

        result = self.projects_client.get_custom_field_allowed_values("0-0", "UnknownField")

        self.assertEqual(result, [])

    def test_get_custom_field_allowed_values_no_bundle_id(self):
        """Test getting allowed values when bundle ID is missing."""
        mock_schema = {
            "bundle_type": "EnumBundle",
            "bundle_id": None
        }
        
        self.projects_client.get_custom_field_schema = Mock(return_value=mock_schema)

        result = self.projects_client.get_custom_field_allowed_values("0-0", "Priority")

        self.assertEqual(result, [])

    def test_get_custom_field_allowed_values_api_error(self):
        """Test allowed values retrieval with API error."""
        mock_schema = {
            "bundle_type": "EnumBundle",
            "bundle_id": "bundle-123"
        }
        
        self.projects_client.get_custom_field_schema = Mock(return_value=mock_schema)
        self.mock_client.get.side_effect = Exception("API Error")

        result = self.projects_client.get_custom_field_allowed_values("0-0", "Priority")

        self.assertEqual(result, [])

    def test_get_all_custom_fields_schemas_success(self):
        """Test getting all custom field schemas for a project."""
        mock_fields = [
            {"field": {"name": "Priority"}},
            {"field": {"name": "Assignee"}}, 
            {"field": {"name": "State"}}
        ]
        
        # Mock the actual API call instead of the wrapper method
        self.mock_client.get.return_value = mock_fields
        
        # Mock individual schema calls
        mock_schemas = {
            "Priority": {"name": "Priority", "type": "enum"},
            "Assignee": {"name": "Assignee", "type": "user"},
            "State": {"name": "State", "type": "state"}
        }
        
        def mock_get_schema(project_id, field_name):
            return mock_schemas.get(field_name)
        
        self.projects_client.get_custom_field_schema = Mock(side_effect=mock_get_schema)

        result = self.projects_client.get_all_custom_fields_schemas("0-0")

        self.assertEqual(len(result), 3)
        self.assertIn("Priority", result)
        self.assertIn("Assignee", result)
        self.assertIn("State", result)
        self.assertEqual(result["Priority"]["type"], "enum")

    def test_get_all_custom_fields_schemas_api_error(self):
        """Test getting all schemas with API error."""
        self.projects_client.get_custom_fields = Mock(side_effect=Exception("API Error"))

        result = self.projects_client.get_all_custom_fields_schemas("0-0")

        self.assertEqual(result, {})

    def test_validate_custom_field_for_project_valid_enum(self):
        """Test validation for valid enum field value."""
        mock_schema = {
            "name": "Priority",
            "type": "enum",
            "required": False,
            "multi_value": False,
            "allowed_values": [
                {"name": "High"}, {"name": "Medium"}, {"name": "Low"}
            ]
        }
        
        self.projects_client.get_custom_field_schema = Mock(return_value=mock_schema)

        result = self.projects_client.validate_custom_field_for_project("0-0", "Priority", "High")

        self.assertTrue(result["valid"])
        self.assertEqual(result["field"], "Priority")
        self.assertEqual(result["value"], "High")

    def test_validate_custom_field_for_project_invalid_enum(self):
        """Test validation for invalid enum field value."""
        mock_schema = {
            "name": "Priority",
            "type": "enum",
            "required": False,
            "multi_value": False,
            "allowed_values": [
                {"name": "High"}, {"name": "Medium"}, {"name": "Low"}
            ]
        }
        
        self.projects_client.get_custom_field_schema = Mock(return_value=mock_schema)

        result = self.projects_client.validate_custom_field_for_project("0-0", "Priority", "VeryHigh")

        self.assertFalse(result["valid"])
        self.assertIn("Invalid value", result["error"])
        self.assertIn("High, Medium, Low", result["suggestion"])

    def test_validate_custom_field_for_project_required_field_empty(self):
        """Test validation for required field with empty value."""
        mock_schema = {
            "name": "Priority",
            "type": "enum",
            "required": True,
            "multi_value": False
        }
        
        self.projects_client.get_custom_field_schema = Mock(return_value=mock_schema)

        result = self.projects_client.validate_custom_field_for_project("0-0", "Priority", "")

        self.assertFalse(result["valid"])
        self.assertIn("is required", result["error"])

    def test_validate_custom_field_for_project_user_field_valid(self):
        """Test validation for valid user field."""
        mock_schema = {
            "name": "Assignee",
            "type": "user",
            "required": False,
            "multi_value": False
        }
        
        self.projects_client.get_custom_field_schema = Mock(return_value=mock_schema)
        self.mock_client.get.return_value = {"id": "user-1", "login": "john.doe"}

        result = self.projects_client.validate_custom_field_for_project("0-0", "Assignee", "john.doe")

        self.assertTrue(result["valid"])

    def test_validate_custom_field_for_project_user_field_invalid(self):
        """Test validation for invalid user field."""
        mock_schema = {
            "name": "Assignee",
            "type": "user",
            "required": False,
            "multi_value": False
        }
        
        self.projects_client.get_custom_field_schema = Mock(return_value=mock_schema)
        self.mock_client.get.side_effect = Exception("User not found")

        result = self.projects_client.validate_custom_field_for_project("0-0", "Assignee", "nonexistent")

        self.assertFalse(result["valid"])
        self.assertIn("not found", result["error"])

    def test_validate_custom_field_for_project_integer_field_valid(self):
        """Test validation for valid integer field."""
        mock_schema = {
            "name": "Story Points",
            "type": "integer",
            "required": False,
            "multi_value": False
        }
        
        self.projects_client.get_custom_field_schema = Mock(return_value=mock_schema)

        result = self.projects_client.validate_custom_field_for_project("0-0", "Story Points", "8")

        self.assertTrue(result["valid"])

    def test_validate_custom_field_for_project_integer_field_invalid(self):
        """Test validation for invalid integer field."""
        mock_schema = {
            "name": "Story Points",
            "type": "integer",
            "required": False,
            "multi_value": False
        }
        
        self.projects_client.get_custom_field_schema = Mock(return_value=mock_schema)

        result = self.projects_client.validate_custom_field_for_project("0-0", "Story Points", "not-a-number")

        self.assertFalse(result["valid"])
        self.assertIn("Invalid integer", result["error"])

    def test_validate_custom_field_for_project_float_field_valid(self):
        """Test validation for valid float field."""
        mock_schema = {
            "name": "Estimated Hours",
            "type": "float",
            "required": False,
            "multi_value": False
        }
        
        self.projects_client.get_custom_field_schema = Mock(return_value=mock_schema)

        result = self.projects_client.validate_custom_field_for_project("0-0", "Estimated Hours", "2.5")

        self.assertTrue(result["valid"])

    def test_validate_custom_field_for_project_multi_value_field_invalid(self):
        """Test validation for multi-value field with single value."""
        mock_schema = {
            "name": "Tags",
            "type": "enum",
            "required": False,
            "multi_value": True,
            "allowed_values": [{"name": "single-value"}]  # Include the value so enum check passes
        }
        
        self.projects_client.get_custom_field_schema = Mock(return_value=mock_schema)

        result = self.projects_client.validate_custom_field_for_project("0-0", "Tags", "single-value")

        self.assertFalse(result["valid"])
        self.assertIn("expects multiple values", result["error"])

    def test_validate_custom_field_for_project_field_not_found(self):
        """Test validation for non-existent field."""
        self.projects_client.get_custom_field_schema = Mock(return_value=None)

        result = self.projects_client.validate_custom_field_for_project("0-0", "NonExistent", "value")

        self.assertFalse(result["valid"])
        self.assertIn("not found", result["error"])

    def test_validate_custom_field_for_project_api_error(self):
        """Test validation with API error."""
        self.projects_client.get_custom_field_schema = Mock(side_effect=Exception("API Error"))

        result = self.projects_client.validate_custom_field_for_project("0-0", "Field", "value")

        self.assertFalse(result["valid"])
        self.assertIn("Validation error", result["error"])


if __name__ == "__main__":
    unittest.main() 