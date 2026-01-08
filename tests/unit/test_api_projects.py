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
    """Test getting projects list with pagination."""

    def test_get_projects_basic(self):
        """Test getting basic projects list with pagination."""
        mock_client = Mock(spec=YouTrackClient)
        # Simulate single page of results (less than page_size)
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

        # Verify API call includes pagination parameters
        mock_client.get.assert_called_once_with(
            "admin/projects",
            params={
                "fields": "id,name,shortName,description,archived,created,updated,lead(id,name,login)",
                "$top": 100,
                "$skip": 0,
                "$filter": "archived eq false"
            }
        )

    def test_get_projects_pagination_multiple_pages(self):
        """Test fetching projects across multiple pages."""
        mock_client = Mock(spec=YouTrackClient)

        # Create 150 projects (more than default page_size of 100)
        page1_projects = [
            {"id": f"{i}-{i}", "name": f"Project {i}", "shortName": f"P{i}", "archived": False}
            for i in range(100)
        ]
        page2_projects = [
            {"id": f"{i}-{i}", "name": f"Project {i}", "shortName": f"P{i}", "archived": False}
            for i in range(100, 150)
        ]

        # Simulate paginated responses
        mock_client.get.side_effect = [page1_projects, page2_projects]

        projects_client = ProjectsClient(mock_client)
        projects = projects_client.get_projects()

        # Should have all 150 projects
        assert len(projects) == 150

        # Verify pagination calls
        assert mock_client.get.call_count == 2

        # Verify first call (skip=0)
        first_call = mock_client.get.call_args_list[0]
        assert first_call[1]["params"]["$skip"] == 0
        assert first_call[1]["params"]["$top"] == 100

        # Verify second call (skip=100)
        second_call = mock_client.get.call_args_list[1]
        assert second_call[1]["params"]["$skip"] == 100
        assert second_call[1]["params"]["$top"] == 100

    def test_get_projects_pagination_exact_page_boundary(self):
        """Test pagination when results are exactly at page boundary."""
        mock_client = Mock(spec=YouTrackClient)

        # Create exactly 100 projects (equal to page_size)
        page1_projects = [
            {"id": f"{i}-{i}", "name": f"Project {i}", "shortName": f"P{i}", "archived": False}
            for i in range(100)
        ]

        # Simulate paginated responses - second page is empty
        mock_client.get.side_effect = [page1_projects, []]

        projects_client = ProjectsClient(mock_client)
        projects = projects_client.get_projects()

        # Should have all 100 projects
        assert len(projects) == 100

        # Should make two calls (first page full, second empty)
        assert mock_client.get.call_count == 2

    def test_get_projects_custom_page_size(self):
        """Test fetching projects with custom page size."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = [
            {"id": "0-0", "name": "Project 1", "shortName": "P1", "archived": False}
        ]

        projects_client = ProjectsClient(mock_client)
        projects = projects_client.get_projects(page_size=50)

        # Verify custom page size was used
        mock_client.get.assert_called_once_with(
            "admin/projects",
            params={
                "fields": "id,name,shortName,description,archived,created,updated,lead(id,name,login)",
                "$top": 50,
                "$skip": 0,
                "$filter": "archived eq false"
            }
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
        call_params = mock_client.get.call_args[1]["params"]
        assert "$filter" not in call_params

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


class TestProjectsClientGetProjectByName:
    """Test get_project_by_name with direct lookup and fallback."""

    def test_get_project_by_name_direct_lookup_success(self):
        """Test successful direct lookup by shortName."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = {
            "id": "0-0",
            "name": "Demo Project",
            "shortName": "DEMO",
            "description": "Test project"
        }

        projects_client = ProjectsClient(mock_client)
        project = projects_client.get_project_by_name("DEMO")

        assert project is not None
        assert project.id == "0-0"
        assert project.shortName == "DEMO"

        # Should only make one direct lookup call
        mock_client.get.assert_called_once_with(
            "admin/projects/DEMO",
            params={"fields": "id,name,shortName,description,archived,created,updated,lead(id,name,login)"}
        )

    def test_get_project_by_name_fallback_to_pagination(self):
        """Test fallback to paginated search when direct lookup fails."""
        mock_client = Mock(spec=YouTrackClient)

        # First call (direct lookup) fails, then pagination succeeds
        mock_client.get.side_effect = [
            Exception("Project not found"),  # Direct lookup fails
            [  # Pagination returns projects
                {"id": "0-0", "name": "Demo Project", "shortName": "DEMO", "archived": False},
                {"id": "1-1", "name": "Test Project", "shortName": "TEST", "archived": False}
            ]
        ]

        projects_client = ProjectsClient(mock_client)
        project = projects_client.get_project_by_name("DEMO")

        assert project is not None
        assert project.shortName == "DEMO"

        # Should make two calls: direct lookup + pagination
        assert mock_client.get.call_count == 2

    def test_get_project_by_name_match_by_full_name(self):
        """Test matching project by full name (case-insensitive)."""
        mock_client = Mock(spec=YouTrackClient)

        mock_client.get.side_effect = [
            Exception("Project not found"),  # Direct lookup fails (name has spaces)
            [  # Pagination returns projects
                {"id": "0-0", "name": "Demo Project", "shortName": "DEMO", "archived": False},
                {"id": "1-1", "name": "Test Project", "shortName": "TEST", "archived": False}
            ]
        ]

        projects_client = ProjectsClient(mock_client)
        project = projects_client.get_project_by_name("demo project")  # lowercase

        assert project is not None
        assert project.name == "Demo Project"
        assert project.shortName == "DEMO"

    def test_get_project_by_name_match_by_partial_name(self):
        """Test matching project by partial name."""
        mock_client = Mock(spec=YouTrackClient)

        mock_client.get.side_effect = [
            Exception("Project not found"),  # Direct lookup fails
            [  # Pagination returns projects
                {"id": "0-0", "name": "My Demo Project", "shortName": "DEMO", "archived": False},
                {"id": "1-1", "name": "Test Project", "shortName": "TEST", "archived": False}
            ]
        ]

        projects_client = ProjectsClient(mock_client)
        project = projects_client.get_project_by_name("Demo")  # Partial match

        assert project is not None
        assert project.name == "My Demo Project"

    def test_get_project_by_name_not_found(self):
        """Test when project is not found anywhere."""
        mock_client = Mock(spec=YouTrackClient)

        mock_client.get.side_effect = [
            Exception("Project not found"),  # Direct lookup fails
            []  # No projects in paginated result
        ]

        projects_client = ProjectsClient(mock_client)
        project = projects_client.get_project_by_name("NONEXISTENT")

        assert project is None

    def test_get_project_by_name_prefers_shortname_match(self):
        """Test that shortName match takes priority over full name match."""
        mock_client = Mock(spec=YouTrackClient)

        mock_client.get.side_effect = [
            Exception("Project not found"),  # Direct lookup fails
            [
                {"id": "0-0", "name": "Some Project Named TEST", "shortName": "OTHER", "archived": False},
                {"id": "1-1", "name": "Different Project", "shortName": "TEST", "archived": False}
            ]
        ]

        projects_client = ProjectsClient(mock_client)
        project = projects_client.get_project_by_name("TEST")

        # Should match by shortName, not by name containing "TEST"
        assert project is not None
        assert project.shortName == "TEST"
        assert project.id == "1-1"

    def test_get_project_by_name_pagination_multiple_pages(self):
        """Test project search across multiple pagination pages."""
        mock_client = Mock(spec=YouTrackClient)

        # Create 150 projects, target project is on page 2
        page1_projects = [
            {"id": f"{i}-{i}", "name": f"Project {i}", "shortName": f"P{i}", "archived": False}
            for i in range(100)
        ]
        page2_projects = [
            {"id": f"{i}-{i}", "name": f"Project {i}", "shortName": f"P{i}", "archived": False}
            for i in range(100, 120)
        ]
        # Add target project at the end of page 2
        page2_projects.append(
            {"id": "target-id", "name": "Target Project", "shortName": "TARGET", "archived": False}
        )

        mock_client.get.side_effect = [
            Exception("Project not found"),  # Direct lookup fails
            page1_projects,  # First page
            page2_projects   # Second page with target
        ]

        projects_client = ProjectsClient(mock_client)
        project = projects_client.get_project_by_name("TARGET")

        assert project is not None
        assert project.shortName == "TARGET"
        assert project.id == "target-id"


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
            "id": "bundle-123",
            "name": "Priority Bundle",
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
            {
                "field": {
                    "id": "priority-field-id",
                    "name": "Priority",
                    "fieldType": {
                        "$type": "EnumBundle",
                        "valueType": "enum",
                        "id": "enum-bundle-123"
                    }
                },
                "canBeEmpty": False,
                "autoAttached": False
            },
            {
                "field": {
                    "id": "assignee-field-id", 
                    "name": "Assignee",
                    "fieldType": {
                        "$type": "UserBundle",
                        "valueType": "user",
                        "id": "user-bundle-456"
                    }
                },
                "canBeEmpty": True,
                "autoAttached": False
            },
            {
                "field": {
                    "id": "state-field-id",
                    "name": "State", 
                    "fieldType": {
                        "$type": "StateBundle",
                        "valueType": "state",
                        "id": "state-bundle-789"
                    }
                },
                "canBeEmpty": False,
                "autoAttached": True
            }
        ]
        
        # Mock the API call with the detailed fields response
        self.mock_client.get.return_value = mock_fields

        result = self.projects_client.get_all_custom_fields_schemas("0-0")

        self.assertEqual(len(result), 3)
        self.assertIn("Priority", result)
        self.assertIn("Assignee", result)
        self.assertIn("State", result)
        
        # Check that the field types match what our implementation returns (valueType)
        self.assertEqual(result["Priority"]["type"], "enum")
        self.assertEqual(result["Assignee"]["type"], "user")
        self.assertEqual(result["State"]["type"], "state")
        
        # Check additional schema properties
        self.assertEqual(result["Priority"]["required"], True)  # canBeEmpty: False means required
        self.assertEqual(result["Assignee"]["required"], False)  # canBeEmpty: True means not required
        self.assertEqual(result["State"]["auto_attach"], True)

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
        # Mock the allowed values that the validation logic actually calls
        self.projects_client.get_custom_field_allowed_values = Mock(return_value=[
            {"name": "High"}, {"name": "Medium"}, {"name": "Low"}
        ])

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
        # Mock the allowed values that the validation logic actually calls
        self.projects_client.get_custom_field_allowed_values = Mock(return_value=[
            {"name": "High"}, {"name": "Medium"}, {"name": "Low"}
        ])

        result = self.projects_client.validate_custom_field_for_project("0-0", "Priority", "VeryHigh")

        self.assertFalse(result["valid"])
        self.assertIn("Invalid enum value", result["error"])
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
        # Mock the allowed values that the validation logic actually calls
        self.projects_client.get_custom_field_allowed_values = Mock(return_value=[
            {"name": "High"}, {"name": "Medium"}, {"name": "Low"}
        ])

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
        # Mock the allowed values that the validation logic actually calls
        self.projects_client.get_custom_field_allowed_values = Mock(return_value=[
            {"login": "john.doe", "name": "John Doe", "id": "user-1"},
            {"login": "jane.smith", "name": "Jane Smith", "id": "user-2"}
        ])

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
        # Mock the allowed values that the validation logic actually calls
        self.projects_client.get_custom_field_allowed_values = Mock(return_value=[
            {"name": "single-value"}, {"name": "other-tag"}
        ])

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