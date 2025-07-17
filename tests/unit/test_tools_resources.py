"""
Unit tests for YouTrack Resources Tools.
"""
import json
import pytest
from unittest.mock import Mock, patch

from youtrack_mcp.tools.resources import ResourcesTools, YOUTRACK_URI_SCHEME, URI_TEMPLATES
from youtrack_mcp.api.client import YouTrackAPIError


class TestResourcesToolsInitialization:
    """Test ResourcesTools initialization."""
    
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_resources_tools_initialization(self, mock_client_class):
        """Test that ResourcesTools initializes correctly."""
        # Mock the client instance
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = ResourcesTools()
        assert tools.client is not None
        assert tools.issues_api is not None
        assert tools.projects_api is not None
        assert tools.subscriptions == set()
        mock_client_class.assert_called_once()


class TestResourcesToolsConstants:
    """Test URI constants and templates."""
    
    def test_uri_scheme_constant(self):
        """Test that URI scheme is defined correctly."""
        assert YOUTRACK_URI_SCHEME == "youtrack"
    
    def test_uri_templates_structure(self):
        """Test that URI templates are properly structured."""
        assert isinstance(URI_TEMPLATES, dict)
        
        expected_templates = [
            "projects", "project", "project_issues", "issues", "issue",
            "issue_comments", "users", "user", "search"
        ]
        
        for template_name in expected_templates:
            assert template_name in URI_TEMPLATES
            assert URI_TEMPLATES[template_name].startswith(YOUTRACK_URI_SCHEME)


class TestResourcesToolsListResources:
    """Test list_resources method."""
    
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_list_resources_success(self, mock_client_class, mock_projects_client_class):
        """Test successful resource listing."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock projects
        mock_projects_api.get_projects.return_value = [
            {"id": "0-0", "name": "Demo Project", "shortName": "DEMO"}
        ]
        
        tools = ResourcesTools()
        result = tools.list_resources()
        
        result_data = json.loads(result)
        resources = result_data["resources"]
        
        # Should contain static resources
        resource_names = [r["name"] for r in resources]
        assert "All Projects" in resource_names
        assert "All Issues" in resource_names
        assert "All Users" in resource_names
        
        # Should contain dynamic project resources
        project_resources = [r for r in resources if "Demo Project" in r["name"]]
        assert len(project_resources) > 0
    
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_list_resources_projects_api_error(self, mock_client_class, mock_projects_client_class):
        """Test resource listing when projects API fails."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        mock_projects_api.get_projects.side_effect = YouTrackAPIError("Access denied")
        
        tools = ResourcesTools()
        result = tools.list_resources()
        
        result_data = json.loads(result)
        resources = result_data["resources"]
        
        # Should still contain static resources even if projects fail
        resource_names = [r["name"] for r in resources]
        assert "All Projects" in resource_names
        assert "All Issues" in resource_names
        assert "All Users" in resource_names


class TestResourcesToolsReadResource:
    """Test read_resource method."""
    
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_projects(self, mock_client_class, mock_projects_client_class):
        """Test reading projects resource."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        mock_projects_api.get_projects.return_value = [
            {"id": "0-0", "name": "Demo Project"}
        ]
        
        tools = ResourcesTools()
        result = tools.read_resource("youtrack://projects")
        
        result_data = json.loads(result)
        assert "contents" in result_data
        assert len(result_data["contents"]) == 1
        
        content = result_data["contents"][0]
        assert content["mimeType"] == "application/json"
        
        projects_data = json.loads(content["text"])
        assert len(projects_data) == 1
        assert projects_data[0]["id"] == "0-0"
    
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_issues(self, mock_client_class, mock_issues_client_class):
        """Test reading issues resource."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.search_issues.return_value = [
            {"id": "2-123", "summary": "Test Issue"}
        ]
        
        tools = ResourcesTools()
        result = tools.read_resource("youtrack://issues")
        
        result_data = json.loads(result)
        assert "contents" in result_data
        
        content = result_data["contents"][0]
        issues_data = json.loads(content["text"])
        assert len(issues_data) == 1
        assert issues_data[0]["id"] == "2-123"
    
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_specific_project(self, mock_client_class):
        """Test reading specific project resource."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_client.get.return_value = {
            "id": "0-0",
            "name": "Demo Project",
            "shortName": "DEMO"
        }
        
        tools = ResourcesTools()
        result = tools.read_resource("youtrack://projects/0-0")
        
        result_data = json.loads(result)
        content = result_data["contents"][0]
        project_data = json.loads(content["text"])
        assert project_data["id"] == "0-0"
        assert project_data["name"] == "Demo Project"
        
        mock_client.get.assert_called_once_with("admin/projects/0-0")
    
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_specific_issue(self, mock_client_class):
        """Test reading specific issue resource."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_client.get.return_value = {
            "id": "2-123",
            "idReadable": "DEMO-123",
            "summary": "Test Issue"
        }
        
        tools = ResourcesTools()
        result = tools.read_resource("youtrack://issues/DEMO-123")
        
        result_data = json.loads(result)
        content = result_data["contents"][0]
        issue_data = json.loads(content["text"])
        assert issue_data["id"] == "2-123"
        assert issue_data["summary"] == "Test Issue"
    
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_project_issues(self, mock_client_class, mock_projects_client_class):
        """Test reading project issues resource."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        mock_projects_api.get_project_issues.return_value = [
            {"id": "2-123", "summary": "Project Issue"}
        ]
        
        tools = ResourcesTools()
        result = tools.read_resource("youtrack://projects/DEMO/issues")
        
        result_data = json.loads(result)
        content = result_data["contents"][0]
        issues_data = json.loads(content["text"])
        assert len(issues_data) == 1
        assert issues_data[0]["id"] == "2-123"
        
        mock_projects_api.get_project_issues.assert_called_once_with("DEMO", 50)
    
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_issue_comments(self, mock_client_class):
        """Test reading issue comments resource."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_client.get.return_value = [
            {"id": "comment-1", "text": "First comment"},
            {"id": "comment-2", "text": "Second comment"}
        ]
        
        tools = ResourcesTools()
        result = tools.read_resource("youtrack://issues/DEMO-123/comments")
        
        result_data = json.loads(result)
        content = result_data["contents"][0]
        comments_data = json.loads(content["text"])
        assert len(comments_data) == 2
        assert comments_data[0]["text"] == "First comment"
        
        mock_client.get.assert_called_once_with("issues/DEMO-123/comments")
    
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_search(self, mock_client_class):
        """Test reading search resource."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = ResourcesTools()
        result = tools.read_resource("youtrack://search?query=project:%20DEMO")
        
        result_data = json.loads(result)
        content = result_data["contents"][0]
        assert "search" in content["text"].lower()
    
    def test_read_resource_invalid_uri(self):
        """Test reading invalid URI."""
        tools = ResourcesTools()
        result = tools.read_resource("invalid://uri")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Invalid URI scheme" in result_data["error"]
    
    def test_read_resource_unknown_pattern(self):
        """Test reading unknown URI pattern."""
        tools = ResourcesTools()
        result = tools.read_resource("youtrack://unknown/path")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Unknown resource" in result_data["error"]


class TestResourcesToolsSubscriptions:
    """Test subscription methods."""
    
    def test_subscribe_resource_success(self):
        """Test successful resource subscription."""
        tools = ResourcesTools()
        result = tools.subscribe_resource("youtrack://projects")
        
        result_data = json.loads(result)
        assert result_data["success"] is True
        assert "youtrack://projects" in tools.subscriptions
    
    def test_subscribe_resource_already_subscribed(self):
        """Test subscribing to already subscribed resource."""
        tools = ResourcesTools()
        tools.subscriptions.add("youtrack://projects")
        
        result = tools.subscribe_resource("youtrack://projects")
        
        result_data = json.loads(result)
        assert result_data["success"] is True
        assert "already subscribed" in result_data["message"]
    
    def test_unsubscribe_resource_success(self):
        """Test successful resource unsubscription."""
        tools = ResourcesTools()
        tools.subscriptions.add("youtrack://projects")
        
        result = tools.unsubscribe_resource("youtrack://projects")
        
        result_data = json.loads(result)
        assert result_data["success"] is True
        assert "youtrack://projects" not in tools.subscriptions
    
    def test_unsubscribe_resource_not_subscribed(self):
        """Test unsubscribing from non-subscribed resource."""
        tools = ResourcesTools()
        
        result = tools.unsubscribe_resource("youtrack://projects")
        
        result_data = json.loads(result)
        assert result_data["success"] is True
        assert "not subscribed" in result_data["message"]


class TestResourcesToolsHelperMethods:
    """Test helper methods."""
    
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_get_all_issues(self, mock_client_class, mock_issues_client_class):
        """Test get_all_issues method."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.search_issues.return_value = [
            {"id": "2-123", "summary": "Issue 1"},
            {"id": "2-124", "summary": "Issue 2"}
        ]
        
        tools = ResourcesTools()
        result = tools.get_all_issues()
        
        result_data = json.loads(result)
        content = result_data["contents"][0]
        issues_data = json.loads(content["text"])
        assert len(issues_data) == 2
        
        mock_issues_api.search_issues.assert_called_once_with(limit=100)
    
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_get_issue(self, mock_client_class):
        """Test get_issue method."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_client.get.return_value = {
            "id": "2-123",
            "summary": "Test Issue"
        }
        
        tools = ResourcesTools()
        result = tools.get_issue("DEMO-123")
        
        result_data = json.loads(result)
        content = result_data["contents"][0]
        issue_data = json.loads(content["text"])
        assert issue_data["id"] == "2-123"
    
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_get_issue_comments(self, mock_client_class):
        """Test get_issue_comments method."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_client.get.return_value = [
            {"id": "comment-1", "text": "Test comment"}
        ]
        
        tools = ResourcesTools()
        result = tools.get_issue_comments("DEMO-123")
        
        result_data = json.loads(result)
        content = result_data["contents"][0]
        comments_data = json.loads(content["text"])
        assert len(comments_data) == 1
        assert comments_data[0]["text"] == "Test comment"
    
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_get_all_projects(self, mock_client_class, mock_projects_client_class):
        """Test get_all_projects method."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        mock_projects_api.get_projects.return_value = [
            {"id": "0-0", "name": "Demo Project"}
        ]
        
        tools = ResourcesTools()
        result = tools.get_all_projects()
        
        result_data = json.loads(result)
        content = result_data["contents"][0]
        projects_data = json.loads(content["text"])
        assert len(projects_data) == 1
        assert projects_data[0]["id"] == "0-0"
    
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_get_project(self, mock_client_class):
        """Test get_project method."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_client.get.return_value = {
            "id": "0-0",
            "name": "Demo Project"
        }
        
        tools = ResourcesTools()
        result = tools.get_project("0-0")
        
        result_data = json.loads(result)
        content = result_data["contents"][0]
        project_data = json.loads(content["text"])
        assert project_data["id"] == "0-0"
    
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_get_project_issues(self, mock_client_class, mock_projects_client_class):
        """Test get_project_issues method."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        mock_projects_api.get_project_issues.return_value = [
            {"id": "2-123", "summary": "Project Issue"}
        ]
        
        tools = ResourcesTools()
        result = tools.get_project_issues("DEMO")
        
        result_data = json.loads(result)
        content = result_data["contents"][0]
        issues_data = json.loads(content["text"])
        assert len(issues_data) == 1
    
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_get_all_users(self, mock_client_class):
        """Test get_all_users method."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_client.get.return_value = [
            {"id": "1-1", "login": "admin", "name": "Administrator"}
        ]
        
        tools = ResourcesTools()
        result = tools.get_all_users()
        
        result_data = json.loads(result)
        content = result_data["contents"][0]
        users_data = json.loads(content["text"])
        assert len(users_data) == 1
        assert users_data[0]["login"] == "admin"
    
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_get_user(self, mock_client_class):
        """Test get_user method."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_client.get.return_value = {
            "id": "1-1",
            "login": "admin",
            "name": "Administrator"
        }
        
        tools = ResourcesTools()
        result = tools.get_user("1-1")
        
        result_data = json.loads(result)
        content = result_data["contents"][0]
        user_data = json.loads(content["text"])
        assert user_data["login"] == "admin"
    
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_search_issues(self, mock_client_class, mock_issues_client_class):
        """Test search_issues method."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.search_issues.return_value = [
            {"id": "2-123", "summary": "Search Result"}
        ]
        
        tools = ResourcesTools()
        result = tools.search_issues("project: DEMO")
        
        result_data = json.loads(result)
        content = result_data["contents"][0]
        issues_data = json.loads(content["text"])
        assert len(issues_data) == 1
        assert issues_data[0]["summary"] == "Search Result"


class TestResourcesToolsClose:
    """Test close method."""
    
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_close_with_close_method(self, mock_client_class):
        """Test close method when client has close method."""
        mock_client = Mock()
        mock_client.close = Mock()
        mock_client_class.return_value = mock_client
        
        tools = ResourcesTools()
        tools.close()
        
        mock_client.close.assert_called_once()


class TestResourcesToolsDefinitions:
    """Test tool definitions."""
    
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_get_tool_definitions(self, mock_client_class):
        """Test that tool definitions are properly structured."""
        # Mock the client instance
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = ResourcesTools()
        definitions = tools.get_tool_definitions()
        
        assert isinstance(definitions, dict)
        
        expected_tools = [
            "list_resources", "read_resource", "subscribe_resource",
            "unsubscribe_resource", "get_all_issues", "get_issue",
            "get_issue_comments", "get_all_projects", "get_project",
            "get_project_issues", "get_all_users", "get_user", "search_issues"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in definitions
            assert "description" in definitions[tool_name]
            assert "parameter_descriptions" in definitions[tool_name]
        
        # Check specific tool structure
        read_resource_def = definitions["read_resource"]
        assert "uri" in read_resource_def["parameter_descriptions"]
        
        subscribe_def = definitions["subscribe_resource"]
        assert "uri" in subscribe_def["parameter_descriptions"]


class TestResourcesToolsIntegration:
    """Integration tests for ResourcesTools."""
    
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_complete_resources_workflow(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test a complete resources workflow scenario."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock data
        mock_projects_api.get_projects.return_value = [
            {"id": "0-0", "name": "Demo Project"}
        ]
        mock_issues_api.search_issues.return_value = [
            {"id": "2-123", "summary": "Test Issue"}
        ]
        
        tools = ResourcesTools()
        
        # Test resource listing
        list_result = tools.list_resources()
        list_data = json.loads(list_result)
        assert "resources" in list_data
        
        # Test resource reading
        read_result = tools.read_resource("youtrack://projects")
        read_data = json.loads(read_result)
        assert "contents" in read_data
        
        # Test subscription
        subscribe_result = tools.subscribe_resource("youtrack://projects")
        subscribe_data = json.loads(subscribe_result)
        assert subscribe_data["success"] is True
        
        # Test unsubscription
        unsubscribe_result = tools.unsubscribe_resource("youtrack://projects")
        unsubscribe_data = json.loads(unsubscribe_result)
        assert unsubscribe_data["success"] is True
        
        tools.close()


class TestResourcesToolsErrorHandling:
    """Test error handling scenarios."""
    
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_api_error(self, mock_client_class):
        """Test read resource with API error."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_client.get.side_effect = YouTrackAPIError("Access denied")
        
        tools = ResourcesTools()
        result = tools.read_resource("youtrack://issues/DEMO-123")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Access denied" in result_data["error"]
    
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_get_issue_comments_fallback(self, mock_client_class):
        """Test issue comments fallback to direct API call."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock initial failure, then success on direct call
        mock_client.get.side_effect = [
            Exception("Method not found"),
            [{"id": "comment-1", "text": "Fallback comment"}]
        ]
        
        tools = ResourcesTools()
        result = tools.get_issue_comments("DEMO-123")
        
        result_data = json.loads(result)
        content = result_data["contents"][0]
        comments_data = json.loads(content["text"])
        assert len(comments_data) == 1
        assert comments_data[0]["text"] == "Fallback comment"
        
        # Verify fallback was used
        assert mock_client.get.call_count == 2 