"""
Unit tests for YouTrack Project Tools.
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from youtrack_mcp.tools.projects import ProjectTools
from youtrack_mcp.api.client import YouTrackAPIError


class TestProjectToolsInitialization:
    """Test ProjectTools initialization."""
    
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_project_tools_initialization(self, mock_client_class):
        """Test that ProjectTools initializes correctly."""
        # Mock the client instance
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = ProjectTools()
        assert tools.client is not None
        assert tools.projects_api is not None
        mock_client_class.assert_called_once()
        assert tools.issues_api is not None


class TestProjectToolsGetProjects:
    """Test get_projects method."""
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_projects_success(self, mock_client_class, mock_projects_client_class):
        """Test successful projects retrieval."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock projects with Pydantic model behavior
        mock_project = Mock()
        mock_project.model_dump.return_value = {
            "id": "0-0",
            "name": "Demo Project",
            "shortName": "DEMO"
        }
        
        mock_projects_api.get_projects.return_value = [mock_project]
        
        tools = ProjectTools()
        result = tools.get_projects()
        
        result_data = json.loads(result)
        assert len(result_data) == 1
        assert result_data[0]["id"] == "0-0"
        assert result_data[0]["name"] == "Demo Project"
        
        mock_projects_api.get_projects.assert_called_once_with(include_archived=False)
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_projects_include_archived(self, mock_client_class, mock_projects_client_class):
        """Test projects retrieval including archived."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        mock_projects_api.get_projects.return_value = []
        
        tools = ProjectTools()
        result = tools.get_projects(include_archived=True)
        
        mock_projects_api.get_projects.assert_called_once_with(include_archived=True)
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_projects_dict_response(self, mock_client_class, mock_projects_client_class):
        """Test handling of dictionary response."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        mock_projects_api.get_projects.return_value = [
            {"id": "0-0", "name": "Demo Project", "shortName": "DEMO"}
        ]
        
        tools = ProjectTools()
        result = tools.get_projects()
        
        result_data = json.loads(result)
        assert len(result_data) == 1
        assert result_data[0]["id"] == "0-0"
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_projects_api_error(self, mock_client_class, mock_projects_client_class):
        """Test handling of API error."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        mock_projects_api.get_projects.side_effect = YouTrackAPIError("Access denied")
        
        tools = ProjectTools()
        result = tools.get_projects()
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Access denied" in result_data["error"]


class TestProjectToolsGetProject:
    """Test get_project method."""
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_success(self, mock_client_class, mock_projects_client_class):
        """Test successful project retrieval."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        mock_project = Mock()
        mock_project.model_dump.return_value = {
            "id": "0-0",
            "name": "Demo Project",
            "shortName": "DEMO"
        }
        
        mock_projects_api.get_project.return_value = mock_project
        
        tools = ProjectTools()
        result = tools.get_project("0-0")
        
        result_data = json.loads(result)
        assert result_data["id"] == "0-0"
        assert result_data["name"] == "Demo Project"
        
        mock_projects_api.get_project.assert_called_once_with("0-0")
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_missing_id(self, mock_client_class, mock_projects_client_class):
        """Test get project with missing ID."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = ProjectTools()
        result = tools.get_project("")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Project ID is required" in result_data["error"]
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_not_found(self, mock_client_class, mock_projects_client_class):
        """Test handling of project not found."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        mock_projects_api.get_project.side_effect = YouTrackAPIError("Project not found")
        
        tools = ProjectTools()
        result = tools.get_project("NONEXISTENT")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Project not found" in result_data["error"]


class TestProjectToolsGetProjectByName:
    """Test get_project_by_name method."""
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_by_name_success(self, mock_client_class, mock_projects_client_class):
        """Test successful project retrieval by name."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        mock_project = Mock()
        mock_project.model_dump.return_value = {
            "id": "0-0",
            "name": "Demo Project",
            "shortName": "DEMO"
        }
        
        mock_projects_api.get_project_by_name.return_value = mock_project
        
        tools = ProjectTools()
        result = tools.get_project_by_name("DEMO")
        
        result_data = json.loads(result)
        assert result_data["shortName"] == "DEMO"
        
        mock_projects_api.get_project_by_name.assert_called_once_with("DEMO")
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_by_name_missing_name(self, mock_client_class, mock_projects_client_class):
        """Test get project by name with missing name."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        # Mock API to return None for empty name (no project found)
        mock_projects_api.get_project_by_name.return_value = None
        
        tools = ProjectTools()
        result = tools.get_project_by_name("")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Project '' not found" in result_data["error"]


class TestProjectToolsGetProjectIssues:
    """Test get_project_issues method."""
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_issues_success(self, mock_client_class, mock_projects_client_class):
        """Test successful project issues retrieval."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        mock_issues = [
            {"id": "2-123", "summary": "Issue 1"},
            {"id": "2-124", "summary": "Issue 2"}
        ]
        
        mock_projects_api.get_project_issues.return_value = mock_issues
        
        tools = ProjectTools()
        result = tools.get_project_issues("DEMO")
        
        result_data = json.loads(result)
        assert len(result_data) == 2
        assert result_data[0]["id"] == "2-123"
        
        mock_projects_api.get_project_issues.assert_called_once_with("DEMO", 50)
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_issues_with_limit(self, mock_client_class, mock_projects_client_class):
        """Test project issues retrieval with custom limit."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Return a non-empty list so the first call succeeds and doesn't trigger fallback
        mock_issues = [{"id": "2-125", "summary": "Test Issue"}]
        mock_projects_api.get_project_issues.return_value = mock_issues
        
        tools = ProjectTools()
        result = tools.get_project_issues("DEMO", limit=25)
        
        result_data = json.loads(result)
        assert len(result_data) == 1
        assert result_data[0]["id"] == "2-125"
        
        mock_projects_api.get_project_issues.assert_called_once_with("DEMO", 25)
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_issues_missing_project(self, mock_client_class, mock_projects_client_class):
        """Test get project issues with missing project ID."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = ProjectTools()
        result = tools.get_project_issues("")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Project ID is required" in result_data["error"]
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_issues_fallback_to_name_search(self, mock_client_class, mock_projects_client_class):
        """Test fallback to project name search when direct ID fails."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # First call fails with "Project not found"
        mock_projects_api.get_project_issues.side_effect = [
            Exception("Project not found: DEMO"),
            [{"id": "2-123", "summary": "Issue 1"}]
        ]
        
        # Mock project lookup by name
        mock_project = Mock()
        mock_project.id = "0-0"
        mock_projects_api.get_project_by_name.return_value = mock_project
        
        tools = ProjectTools()
        result = tools.get_project_issues("DEMO")
        
        result_data = json.loads(result)
        assert len(result_data) == 1
        assert result_data[0]["id"] == "2-123"
        
        # Verify the fallback logic was used
        assert mock_projects_api.get_project_issues.call_count == 2
        mock_projects_api.get_project_by_name.assert_called_once_with("DEMO")


class TestProjectToolsGetCustomFields:
    """Test get_custom_fields method."""
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_custom_fields_success(self, mock_client_class, mock_projects_client_class):
        """Test successful custom fields retrieval."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        mock_fields = [
            {"name": "Priority", "type": "enum"},
            {"name": "Assignee", "type": "user"}
        ]
        
        mock_projects_api.get_custom_fields.return_value = mock_fields
        
        tools = ProjectTools()
        result = tools.get_custom_fields("DEMO")
        
        result_data = json.loads(result)
        assert len(result_data) == 2
        assert result_data[0]["name"] == "Priority"
        
        mock_projects_api.get_custom_fields.assert_called_once_with("DEMO")
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_custom_fields_missing_project(self, mock_client_class, mock_projects_client_class):
        """Test get custom fields with missing project ID."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = ProjectTools()
        result = tools.get_custom_fields("")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Project ID is required" in result_data["error"]


class TestProjectToolsCreateProject:
    """Test create_project method."""
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_create_project_success(self, mock_client_class, mock_projects_client_class):
        """Test successful project creation."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        mock_project = Mock()
        mock_project.model_dump.return_value = {
            "id": "0-1",
            "name": "New Project",
            "shortName": "NEW",
            "description": "A new project"
        }
        
        mock_projects_api.create_project.return_value = mock_project
        
        tools = ProjectTools()
        result = tools.create_project(
            name="New Project",
            short_name="NEW",
            lead_id="admin",
            description="A new project"
        )
        
        result_data = json.loads(result)
        assert result_data["name"] == "New Project"
        assert result_data["shortName"] == "NEW"
        
        mock_projects_api.create_project.assert_called_once_with(
            name="New Project",
            short_name="NEW",
            lead_id="admin",
            description="A new project"
        )
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_create_project_missing_name(self, mock_client_class, mock_projects_client_class):
        """Test create project with missing name."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = ProjectTools()
        result = tools.create_project(
            name="",
            short_name="NEW",
            lead_id="admin"
        )
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Project name is required" in result_data["error"]
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_create_project_missing_short_name(self, mock_client_class, mock_projects_client_class):
        """Test create project with missing short name."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = ProjectTools()
        result = tools.create_project(
            name="New Project",
            short_name="",
            lead_id="admin"
        )
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Project short name is required" in result_data["error"]
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_create_project_missing_lead_id(self, mock_client_class, mock_projects_client_class):
        """Test create project with missing lead ID."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = ProjectTools()
        result = tools.create_project(
            name="New Project",
            short_name="NEW",
            lead_id=""
        )
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Project leader ID is required" in result_data["error"]


class TestProjectToolsUpdateProject:
    """Test update_project method."""
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_update_project_success(self, mock_client_class, mock_projects_client_class):
        """Test successful project update."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock existing project
        mock_existing_project = Mock()
        mock_existing_project.name = "Old Project"
        mock_existing_project.id = "0-0"
        mock_existing_project.model_dump.return_value = {
            "id": "0-0",
            "name": "Old Project",
            "shortName": "DEMO"
        }
        
        # Mock updated project  
        mock_updated_project = Mock()
        mock_updated_project.name = "Updated Project"
        mock_updated_project.model_dump.return_value = {
            "id": "0-0",
            "name": "Updated Project",
            "shortName": "DEMO"
        }
        
        # Set up the call sequence: get_project twice (before and after update)
        mock_projects_api.get_project.side_effect = [mock_existing_project, mock_updated_project]
        
        # Mock the direct API call to succeed
        mock_client.post.return_value = None
        
        tools = ProjectTools()
        result = tools.update_project(
            project_id="0-0",
            name="Updated Project"
        )
        
        result_data = json.loads(result)
        assert result_data["name"] == "Updated Project"
        
        # Verify the API calls
        assert mock_projects_api.get_project.call_count == 2
        mock_client.post.assert_called_once_with(
            "admin/projects/0-0", 
            data={"name": "Updated Project"}
        )
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_update_project_missing_id(self, mock_client_class, mock_projects_client_class):
        """Test update project with missing project ID."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = ProjectTools()
        result = tools.update_project(project_id="", name="Updated Project")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Project ID is required" in result_data["error"]


class TestProjectToolsClose:
    """Test close method."""
    
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_close_with_close_method(self, mock_client_class):
        """Test close method when client has close method."""
        mock_client = Mock()
        mock_client.close = Mock()
        mock_client_class.return_value = mock_client
        
        tools = ProjectTools()
        tools.close()
        
        mock_client.close.assert_called_once()


class TestProjectToolsDefinitions:
    """Test tool definitions."""
    
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_tool_definitions(self, mock_client_class):
        """Test that tool definitions are properly structured."""
        # Mock the client instance
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = ProjectTools()
        definitions = tools.get_tool_definitions()
        
        assert isinstance(definitions, dict)
        
        expected_tools = [
            "get_projects", "get_project", "get_project_by_name",
            "get_project_issues", "get_custom_fields", "create_project",
            "update_project"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in definitions
            assert "description" in definitions[tool_name]
            assert "parameter_descriptions" in definitions[tool_name]
        
        # Check specific tool structure
        create_project_def = definitions["create_project"]
        param_descriptions = create_project_def["parameter_descriptions"]
        assert "name" in param_descriptions
        assert "short_name" in param_descriptions
        assert "lead_id" in param_descriptions


class TestProjectToolsIntegration:
    """Integration tests for ProjectTools."""
    
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_complete_workflow_scenario(self, mock_client_class, mock_projects_client_class):
        """Test a complete project workflow scenario."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock getting all projects
        mock_projects_api.get_projects.return_value = []
        
        # Mock creating a project
        mock_project = Mock()
        mock_project.model_dump.return_value = {
            "id": "0-1",
            "name": "Test Project",
            "shortName": "TEST"
        }
        mock_projects_api.create_project.return_value = mock_project
        
        tools = ProjectTools()
        
        # Test the workflow
        projects_result = tools.get_projects()
        create_result = tools.create_project("Test Project", "TEST", "admin")
        
        # Verify results
        projects_data = json.loads(projects_result)
        assert len(projects_data) == 0
        
        create_data = json.loads(create_result)
        assert create_data["name"] == "Test Project"
        
        # Verify API calls
        mock_projects_api.get_projects.assert_called_once()
        mock_projects_api.create_project.assert_called_once() 


class TestProjectToolsGetProjectDictResponse:
    """Test get_project with dict response (line 81)."""
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_dict_response(self, mock_client_class, mock_projects_client_class):
        """Test get_project when API returns dict instead of Pydantic model."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock response as plain dict (no model_dump method)
        mock_projects_api.get_project.return_value = {
            "id": "0-0",
            "name": "Demo Project",
            "shortName": "DEMO"
        }
        
        tools = ProjectTools()
        result = tools.get_project("0-0")
        
        parsed = json.loads(result)
        assert parsed["id"] == "0-0"
        assert parsed["name"] == "Demo Project"
        assert parsed["shortName"] == "DEMO"


class TestProjectToolsGetProjectByNameEdgeCases:
    """Test get_project_by_name edge cases (lines 106, 113-115)."""
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_by_name_dict_response(self, mock_client_class, mock_projects_client_class):
        """Test get_project_by_name when API returns dict (line 106)."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock response as plain dict (no model_dump method)
        mock_projects_api.get_project_by_name.return_value = {
            "id": "0-0",
            "name": "Demo Project",
            "shortName": "DEMO"
        }
        
        tools = ProjectTools()
        result = tools.get_project_by_name("Demo Project")
        
        parsed = json.loads(result)
        assert parsed["id"] == "0-0"
        assert parsed["name"] == "Demo Project"
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_by_name_not_found(self, mock_client_class, mock_projects_client_class):
        """Test get_project_by_name when project not found (lines 113-115)."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock no project found
        mock_projects_api.get_project_by_name.return_value = None
        
        tools = ProjectTools()
        result = tools.get_project_by_name("NonExistent")
        
        parsed = json.loads(result)
        assert "error" in parsed
        assert "Project 'NonExistent' not found" in parsed["error"]
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_by_name_api_error(self, mock_client_class, mock_projects_client_class):
        """Test get_project_by_name API error handling."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock API error
        mock_projects_api.get_project_by_name.side_effect = YouTrackAPIError("API Error")
        
        tools = ProjectTools()
        result = tools.get_project_by_name("Demo")
        
        parsed = json.loads(result)
        assert "error" in parsed
        assert "API Error" in parsed["error"]


class TestProjectToolsGetProjectIssuesAdvanced:
    """Test get_project_issues fallback scenarios (lines 147-150, 161-173)."""
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_issues_fallback_success(self, mock_client_class, mock_projects_client_class):
        """Test fallback to name search when direct lookup fails (lines 147-150, 161-173)."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # First call fails (direct project lookup)
        mock_projects_api.get_project_issues.side_effect = [
            YouTrackAPIError("Project not found"),  # First call fails
            [{"id": "DEMO-1", "summary": "Test issue"}]  # Second call succeeds
        ]
        
        # Fallback name search succeeds
        mock_project = Mock()
        mock_project.id = "0-0"
        mock_projects_api.get_project_by_name.return_value = mock_project
        
        tools = ProjectTools()
        result = tools.get_project_issues("Demo Project")
        
        parsed = json.loads(result)
        assert len(parsed) == 1
        assert parsed[0]["id"] == "DEMO-1"
        
        # Verify fallback was used
        assert mock_projects_api.get_project_issues.call_count == 2
        mock_projects_api.get_project_by_name.assert_called_once_with("Demo Project")
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_issues_fallback_project_not_found(self, mock_client_class, mock_projects_client_class):
        """Test fallback when project name search also fails."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # First call fails (direct project lookup)
        mock_projects_api.get_project_issues.side_effect = YouTrackAPIError("Project not found")
        
        # Fallback name search returns None
        mock_projects_api.get_project_by_name.return_value = None
        
        tools = ProjectTools()
        result = tools.get_project_issues("NonExistent")
        
        parsed = json.loads(result)
        assert "error" in parsed
        assert "Project not found: NonExistent" in parsed["error"]
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_project_issues_fallback_also_fails(self, mock_client_class, mock_projects_client_class):
        """Test when both direct and fallback approaches fail."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # First call fails (direct project lookup)
        mock_projects_api.get_project_issues.side_effect = YouTrackAPIError("Project not found")
        
        # Fallback name search also fails
        mock_projects_api.get_project_by_name.side_effect = YouTrackAPIError("Name search failed")
        
        tools = ProjectTools()
        result = tools.get_project_issues("Demo")
        
        parsed = json.loads(result)
        assert "error" in parsed
        assert "Name search failed" in parsed["error"]


class TestProjectToolsGetCustomFieldsEdgeCases:
    """Test get_custom_fields edge cases (lines 198, 202, 210, 215, 217-227)."""
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_custom_fields_none_response(self, mock_client_class, mock_projects_client_class):
        """Test get_custom_fields when API returns None (line 198)."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock None response - correct method name
        mock_projects_api.get_custom_fields.return_value = None
        
        tools = ProjectTools()
        result = tools.get_custom_fields("0-0")
        
        parsed = json.loads(result)
        assert parsed == []
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_custom_fields_dict_response(self, mock_client_class, mock_projects_client_class):
        """Test get_custom_fields when API returns dict (line 202)."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock dict response - correct method name
        mock_projects_api.get_custom_fields.return_value = {
            "fields": [{"name": "Priority", "type": "enum"}]
        }
        
        tools = ProjectTools()
        result = tools.get_custom_fields("0-0")
        
        parsed = json.loads(result)
        assert "fields" in parsed
        assert len(parsed["fields"]) == 1
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_custom_fields_iteration_error(self, mock_client_class, mock_projects_client_class):
        """Test get_custom_fields when iteration fails (lines 217-227)."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock response that causes iteration error - correct method name
        mock_response = Mock()
        mock_response.__iter__ = Mock(side_effect=TypeError("Not iterable"))
        mock_response.__str__ = Mock(return_value="Custom fields data")
        mock_projects_api.get_custom_fields.return_value = mock_response
        
        tools = ProjectTools()
        result = tools.get_custom_fields("0-0")
        
        parsed = json.loads(result)
        assert "custom_fields" in parsed
        assert parsed["custom_fields"] == "Custom fields data"
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_get_custom_fields_mixed_object_types(self, mock_client_class, mock_projects_client_class):
        """Test get_custom_fields with mixed object types in list (lines 210, 215)."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock response with mixed object types - correct method name
        mock_pydantic_field = Mock()
        mock_pydantic_field.model_dump.return_value = {"name": "Priority", "type": "enum"}
        
        dict_field = {"name": "State", "type": "state"}
        
        string_field = "Some other field"
        
        mock_projects_api.get_custom_fields.return_value = [
            mock_pydantic_field,
            dict_field,
            string_field
        ]
        
        tools = ProjectTools()
        result = tools.get_custom_fields("0-0")
        
        parsed = json.loads(result)
        assert len(parsed) == 3
        assert parsed[0] == {"name": "Priority", "type": "enum"}
        assert parsed[1] == {"name": "State", "type": "state"}
        assert parsed[2] == "Some other field"


class TestProjectToolsCreateProjectErrors:
    """Test create_project error handling (lines 277, 280-282)."""
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_create_project_api_error(self, mock_client_class, mock_projects_client_class):
        """Test create_project API error handling (lines 277, 280-282)."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock API error during creation
        mock_projects_api.create_project.side_effect = YouTrackAPIError("Creation failed")
        
        tools = ProjectTools()
        result = tools.create_project(
            name="Test Project",
            short_name="TEST",
            lead_id="admin"
        )
        
        parsed = json.loads(result)
        assert "error" in parsed
        assert "Creation failed" in parsed["error"]
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_create_project_general_exception(self, mock_client_class, mock_projects_client_class):
        """Test create_project general exception handling."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock general exception
        mock_projects_api.create_project.side_effect = Exception("Unexpected error")
        
        tools = ProjectTools()
        result = tools.create_project(
            name="Test Project",
            short_name="TEST",
            lead_id="admin"
        )
        
        parsed = json.loads(result)
        assert "error" in parsed
        assert "Unexpected error" in parsed["error"]


class TestProjectToolsUpdateProjectAdvanced:
    """Test update_project edge cases (lines 330, 332, 334, 336, 340-348, 358-359, 375-392)."""
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_update_project_missing_id_validation(self, mock_client_class, mock_projects_client_class):
        """Test update_project with missing project_id (lines 330, 332)."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        tools = ProjectTools()
        
        # Test with None project_id
        result = tools.update_project(project_id=None, name="New Name")
        parsed = json.loads(result)
        assert "error" in parsed
        assert "Project ID is required" in parsed["error"]
        
        # Test with empty string project_id
        result = tools.update_project(project_id="", name="New Name")
        parsed = json.loads(result)
        assert "error" in parsed
        assert "Project ID is required" in parsed["error"]
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_update_project_no_updates_validation(self, mock_client_class, mock_projects_client_class):
        """Test update_project with no update fields - returns current project (lines 334, 336)."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock existing project with Pydantic model behavior
        mock_project = Mock()
        mock_project.model_dump.return_value = {
            "id": "0-0",
            "name": "Demo Project",
            "shortName": "DEMO"
        }
        mock_projects_api.get_project.return_value = mock_project
        
        tools = ProjectTools()
        result = tools.update_project(project_id="0-0")
        
        parsed = json.loads(result)
        # Should return current project, not an error
        assert parsed["id"] == "0-0"
        assert parsed["name"] == "Demo Project"
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_update_project_get_project_fails(self, mock_client_class, mock_projects_client_class):
        """Test update_project when get_project fails (lines 340-348)."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock get_project failure
        mock_projects_api.get_project.side_effect = YouTrackAPIError("Project not found")
        
        tools = ProjectTools()
        result = tools.update_project(project_id="INVALID", name="New Name")
        
        parsed = json.loads(result)
        assert "error" in parsed
        assert "Project not found" in parsed["error"]
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_update_project_update_fails(self, mock_client_class, mock_projects_client_class):
        """Test update_project when update operation fails but continues anyway (lines 358-359)."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock successful get_project with proper attributes
        mock_project = Mock()
        mock_project.name = "Demo Project"
        mock_project.id = "0-0"
        mock_project.model_dump.return_value = {"id": "0-0", "name": "Demo"}
        mock_projects_api.get_project.return_value = mock_project
        
        # Mock update failure in the client.post call
        mock_client.post.side_effect = YouTrackAPIError("Update failed")
        
        tools = ProjectTools()
        result = tools.update_project(project_id="0-0", name="New Name")
        
        parsed = json.loads(result)
        # Implementation continues despite update failure and returns the project
        assert parsed["id"] == "0-0"
        assert parsed["name"] == "Demo"
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_update_project_general_exception(self, mock_client_class, mock_projects_client_class):
        """Test update_project general exception handling (lines 375-392)."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock general exception during entire process
        mock_projects_api.get_project.side_effect = Exception("Unexpected error")
        
        tools = ProjectTools()
        result = tools.update_project(project_id="0-0", name="New Name")
        
        parsed = json.loads(result)
        assert "error" in parsed
        assert "Unexpected error" in parsed["error"]
    
    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.projects.ProjectsClient')
    @patch('youtrack_mcp.tools.projects.YouTrackClient')
    def test_update_project_dict_response_handling(self, mock_client_class, mock_projects_client_class):
        """Test update_project with dict response from get_project."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock get_project returning dict (no model_dump) - this causes AttributeError on .name access
        mock_dict_response = {
            "id": "0-0",
            "name": "Demo Project",
            "shortName": "DEMO"
        }
        mock_projects_api.get_project.return_value = mock_dict_response
        
        tools = ProjectTools()
        result = tools.update_project(project_id="0-0", name="Updated Project")
        
        parsed = json.loads(result)
        # Should catch AttributeError and return error response
        assert "error" in parsed
        assert "'dict' object has no attribute 'name'" in parsed["error"] 