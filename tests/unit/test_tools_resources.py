"""Tests for the resources tools module."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from youtrack_mcp.tools.resources import (
    ResourcesTools,
    URI_TEMPLATES,
    YOUTRACK_URI_SCHEME,
)
from youtrack_mcp.api.client import YouTrackAPIError


class TestResourcesToolsInitialization:
    """Test resources tools initialization."""

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    def test_initialization_success(self, mock_projects_client_class, mock_issues_client_class, mock_client_class):
        """Test successful initialization."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        tools = ResourcesTools()

        assert tools.client == mock_client
        assert tools.issues_api == mock_issues_api
        assert tools.projects_api == mock_projects_api
        assert isinstance(tools.subscriptions, set)
        assert len(tools.subscriptions) == 0

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    def test_empty_subscriptions_on_init(self, mock_projects_client_class, mock_issues_client_class, mock_client_class):
        """Test that subscriptions start empty."""
        mock_client_class.return_value = Mock()
        mock_issues_client_class.return_value = Mock()
        mock_projects_client_class.return_value = Mock()

        tools = ResourcesTools()
        assert len(tools.subscriptions) == 0


class TestResourcesToolsListResources:
    """Test list_resources method."""

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_list_resources_success(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test successful resource listing."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        # Mock projects response - using dictionaries instead of Mock objects
        mock_projects_api.get_projects.return_value = [
            {"id": "0-0", "name": "Demo Project"},
            {"id": "0-1", "name": "Test Project"}
        ]

        tools = ResourcesTools()
        result = tools.list_resources()

        result_data = json.loads(result)
        assert "resources" in result_data
        assert "resourceTemplates" in result_data
        
        # Check that dynamic projects were added
        resources = result_data["resources"]
        project_resources = [r for r in resources if r["name"].startswith("Project:")]
        assert len(project_resources) >= 2

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_list_resources_project_error(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test resource listing when project fetching fails."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        # Mock projects to raise an exception
        mock_projects_api.get_projects.side_effect = Exception("API Error")

        tools = ResourcesTools()
        result = tools.list_resources()

        result_data = json.loads(result)
        assert "resources" in result_data
        assert "resourceTemplates" in result_data

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_list_resources_exception_handling(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test resource listing exception handling."""
        mock_client_class.side_effect = Exception("Client error")

        with pytest.raises(Exception):
            ResourcesTools()


class TestResourcesToolsReadResource:
    """Test read_resource method."""

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_all_projects(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test reading all projects resource."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        # Mock projects response with proper dictionaries
        mock_projects_api.get_projects.return_value = [
            {"id": "0-0", "name": "Demo Project"},
            {"id": "0-1", "name": "Test Project"}
        ]

        tools = ResourcesTools()
        result = tools.read_resource("youtrack://projects")

        result_data = json.loads(result)
        assert "contents" in result_data
        assert len(result_data["contents"]) == 1
        
        content = result_data["contents"][0]
        assert content["uri"] == URI_TEMPLATES["projects"]
        
        # Parse the text content
        projects_data = json.loads(content["text"])
        assert len(projects_data) == 2

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_specific_project(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test reading specific project resource."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        # Mock projects response with proper dictionary
        mock_projects_api.get_project.return_value = {
            "id": "0-0",
            "name": "Demo Project",
            "shortName": "DEMO"
        }

        tools = ResourcesTools()
        result = tools.read_resource("youtrack:///projects/0-0")

        result_data = json.loads(result)
        content = result_data["contents"][0]
        project_data = json.loads(content["text"])
        assert project_data["id"] == "0-0"
        assert project_data["name"] == "Demo Project"

        mock_projects_api.get_project.assert_called_once_with("0-0")

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_specific_issue(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test reading specific issue resource."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        # Mock issues response with proper dictionary
        mock_issues_api.get_issue.return_value = {
            "id": "2-123",
            "idReadable": "DEMO-123",
            "summary": "Test Issue"
        }

        tools = ResourcesTools()
        result = tools.read_resource("youtrack:///issues/DEMO-123")

        result_data = json.loads(result)
        content = result_data["contents"][0]
        issue_data = json.loads(content["text"])
        assert issue_data["id"] == "2-123"
        assert issue_data["summary"] == "Test Issue"

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_project_issues(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test reading project issues resource."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        # Mock projects response with proper dictionaries
        mock_projects_api.get_project_issues.return_value = [
            {"id": "2-123", "summary": "Project Issue"}
        ]

        tools = ResourcesTools()
        result = tools.read_resource("youtrack:///projects/DEMO/issues")

        result_data = json.loads(result)
        content = result_data["contents"][0]
        issues_data = json.loads(content["text"])
        assert len(issues_data) == 1
        assert issues_data[0]["summary"] == "Project Issue"

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_issue_comments(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test reading issue comments resource."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        # Mock comments response with proper dictionaries
        mock_client.get.return_value = [
            {"id": "comment-1", "text": "First comment"},
            {"id": "comment-2", "text": "Second comment"}
        ]

        tools = ResourcesTools()
        result = tools.read_resource("youtrack:///issues/DEMO-123/comments")

        result_data = json.loads(result)
        content = result_data["contents"][0]
        comments_data = json.loads(content["text"])
        assert len(comments_data) == 2
        assert comments_data[0]["text"] == "First comment"

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_search(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test reading search resource."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        # Mock search results with proper dictionaries - search uses client.get directly
        mock_client.get.return_value = [
            {"id": "2-123", "summary": "Search Result"}
        ]

        tools = ResourcesTools()
        result = tools.read_resource("youtrack:///search?query=project:%20DEMO")

        result_data = json.loads(result)
        content = result_data["contents"][0]
        search_data = json.loads(content["text"])
        assert len(search_data) == 1
        assert search_data[0]["summary"] == "Search Result"

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_invalid_uri(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test reading invalid URI."""
        mock_client_class.return_value = Mock()
        mock_issues_client_class.return_value = Mock()
        mock_projects_client_class.return_value = Mock()

        tools = ResourcesTools()
        result = tools.read_resource("http://invalid")

        result_data = json.loads(result)
        assert "error" in result_data
        assert "Invalid URI scheme" in result_data["error"]

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_unknown_pattern(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test reading unknown URI pattern."""
        mock_client_class.return_value = Mock()
        mock_issues_client_class.return_value = Mock()
        mock_projects_client_class.return_value = Mock()

        tools = ResourcesTools()
        result = tools.read_resource("youtrack://unknown/pattern")

        result_data = json.loads(result)
        assert "error" in result_data
        assert "Unknown resource URI" in result_data["error"]


class TestResourcesToolsSubscriptions:
    """Test resource subscription methods."""

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_subscribe_resource_success(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test successful resource subscription."""
        mock_client_class.return_value = Mock()
        mock_issues_client_class.return_value = Mock()
        mock_projects_client_class.return_value = Mock()

        tools = ResourcesTools()
        result = tools.subscribe_resource("youtrack://projects")

        result_data = json.loads(result)
        assert result_data["subscribed"] is True
        assert result_data["uri"] == "youtrack://projects"
        assert "youtrack://projects" in tools.subscriptions

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_subscribe_resource_already_subscribed(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test subscribing to already subscribed resource."""
        mock_client_class.return_value = Mock()
        mock_issues_client_class.return_value = Mock()
        mock_projects_client_class.return_value = Mock()

        tools = ResourcesTools()
        tools.subscriptions.add("youtrack://projects")

        result = tools.subscribe_resource("youtrack://projects")

        result_data = json.loads(result)
        assert result_data["subscribed"] is True
        assert result_data["uri"] == "youtrack://projects"

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_unsubscribe_resource_success(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test successful resource unsubscription."""
        mock_client_class.return_value = Mock()
        mock_issues_client_class.return_value = Mock()
        mock_projects_client_class.return_value = Mock()

        tools = ResourcesTools()
        tools.subscriptions.add("youtrack://projects")

        result = tools.unsubscribe_resource("youtrack://projects")

        result_data = json.loads(result)
        assert result_data["unsubscribed"] is True
        assert result_data["uri"] == "youtrack://projects"
        assert "youtrack://projects" not in tools.subscriptions

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_unsubscribe_resource_not_subscribed(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test unsubscribing from non-subscribed resource."""
        mock_client_class.return_value = Mock()
        mock_issues_client_class.return_value = Mock()
        mock_projects_client_class.return_value = Mock()

        tools = ResourcesTools()
        result = tools.unsubscribe_resource("youtrack://projects")

        result_data = json.loads(result)
        assert result_data["unsubscribed"] is True
        assert result_data["uri"] == "youtrack://projects"


class TestResourcesToolsConstants:
    """Test resources constants and templates."""

    def test_uri_templates_structure(self):
        """Test URI templates structure."""
        assert isinstance(URI_TEMPLATES, dict)
        assert "projects" in URI_TEMPLATES
        assert "project" in URI_TEMPLATES
        assert "issues" in URI_TEMPLATES
        assert "issue" in URI_TEMPLATES

    def test_youtrack_uri_scheme(self):
        """Test YouTrack URI scheme."""
        assert YOUTRACK_URI_SCHEME == "youtrack"

    def test_uri_template_format(self):
        """Test URI template format strings."""
        assert "{project_id}" in URI_TEMPLATES["project"]
        assert "{issue_id}" in URI_TEMPLATES["issue"]
        assert "{user_id}" in URI_TEMPLATES["user"]
        assert "{query}" in URI_TEMPLATES["search"]


class TestResourcesToolsGetAllUsers:
    """Test get_all_users method."""

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_get_all_users_success(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test successful get_all_users."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        # Mock users response
        mock_client.get.return_value = [
            {"id": "user-1", "login": "admin", "fullName": "Administrator"},
            {"id": "user-2", "login": "tester", "fullName": "Test User"}
        ]

        tools = ResourcesTools()
        result = tools.get_all_users()

        result_data = json.loads(result)
        assert "contents" in result_data
        content = result_data["contents"][0]
        users_data = json.loads(content["text"])
        assert len(users_data) == 2
        assert users_data[0]["login"] == "admin"

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_get_all_users_error(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test get_all_users with error."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        # Mock users to raise an exception
        mock_client.get.side_effect = Exception("API Error")

        tools = ResourcesTools()
        result = tools.get_all_users()

        result_data = json.loads(result)
        assert "error" in result_data


class TestResourcesToolsGetUser:
    """Test get_user method."""

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_get_user_success(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test successful get_user."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        # Mock user response
        mock_client.get.return_value = {
            "id": "user-1",
            "login": "admin",
            "fullName": "Administrator"
        }

        tools = ResourcesTools()
        result = tools.get_user("admin")

        result_data = json.loads(result)
        assert "contents" in result_data
        content = result_data["contents"][0]
        user_data = json.loads(content["text"])
        assert user_data["login"] == "admin"

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_get_user_error(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test get_user with error."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        # Mock user to raise an exception
        mock_client.get.side_effect = Exception("User not found")

        tools = ResourcesTools()
        result = tools.get_user("nonexistent")

        result_data = json.loads(result)
        assert "error" in result_data


class TestResourcesToolsHelperMethods:
    """Test helper methods."""

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_search_issues(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test search_issues method."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        # Mock search results with proper dictionaries - search_issues uses client.get directly
        mock_client.get.return_value = [
            {"id": "2-123", "summary": "Search Result"}
        ]

        tools = ResourcesTools()
        result = tools.search_issues("project: DEMO")

        result_data = json.loads(result)
        content = result_data["contents"][0]
        search_data = json.loads(content["text"])
        assert len(search_data) == 1
        assert search_data[0]["summary"] == "Search Result"


class TestResourcesToolsClose:
    """Test close method."""

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_close_with_close_method(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test close method when client has close method."""
        mock_client = Mock()
        mock_client.close = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        tools = ResourcesTools()
        # Add some subscriptions to test they get cleared
        tools.subscriptions.add("test-uri")
        
        tools.close()

        # The close method should clear subscriptions, not call client.close()
        assert len(tools.subscriptions) == 0

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_close_without_close_method(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test close method when client has no close method."""
        mock_client = Mock()
        del mock_client.close  # Remove close method
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        tools = ResourcesTools()
        # Should not raise an exception
        tools.close()


class TestResourcesToolsIntegration:
    """Test integration scenarios."""

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
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
        assert subscribe_data["subscribed"] is True
        assert subscribe_data["uri"] == "youtrack://projects"


class TestResourcesToolsErrorHandling:
    """Test error handling scenarios."""

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_read_resource_api_error(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test read resource with API error."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api

        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api

        # Mock to raise API error when trying to access specific issue
        mock_issues_api.get_issue.side_effect = YouTrackAPIError("Access denied")

        tools = ResourcesTools()
        result = tools.read_resource("youtrack://issues/DEMO-123")

        result_data = json.loads(result)
        assert "error" in result_data

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_subscription_error_handling(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test subscription error handling."""
        mock_client_class.return_value = Mock()
        mock_issues_client_class.return_value = Mock()
        mock_projects_client_class.return_value = Mock()

        tools = ResourcesTools()

        # Test subscribe with exception handling
        result = tools.subscribe_resource("youtrack://projects")
        result_data = json.loads(result)
        assert "subscribed" in result_data

        # Test unsubscribe with exception handling
        result = tools.unsubscribe_resource("youtrack://projects")
        result_data = json.loads(result)
        assert "unsubscribed" in result_data


class TestResourcesToolsGetToolDefinitions:
    """Test get_tool_definitions method."""

    @patch.dict('os.environ', {
        'YOUTRACK_URL': 'https://test.youtrack.cloud',
        'YOUTRACK_API_TOKEN': 'test-token'
    })
    @patch('youtrack_mcp.tools.resources.ProjectsClient')
    @patch('youtrack_mcp.tools.resources.IssuesClient')
    @patch('youtrack_mcp.tools.resources.YouTrackClient')
    def test_get_tool_definitions(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test get_tool_definitions method."""
        mock_client_class.return_value = Mock()
        mock_issues_client_class.return_value = Mock()
        mock_projects_client_class.return_value = Mock()

        tools = ResourcesTools()
        definitions = tools.get_tool_definitions()

        assert isinstance(definitions, dict)
        assert "list_resources" in definitions
        assert "read_resource" in definitions
        assert "subscribe_resource" in definitions
        assert "unsubscribe_resource" in definitions

        # Check structure of a definition
        list_def = definitions["list_resources"]
        assert "description" in list_def
        assert "parameter_descriptions" in list_def 