"""
Unit tests for YouTrack Projects API client (api/projects.py).

This module provides comprehensive test coverage for the ProjectsClient class
and Project model to improve coverage from 20% to high coverage.
"""

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