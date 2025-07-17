"""
Unit tests for YouTrack Issue Tools.
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from youtrack_mcp.tools.issues import IssueTools
from youtrack_mcp.api.client import YouTrackAPIError


class TestIssueToolsInitialization:
    """Test IssueTools initialization."""
    
    def test_issue_tools_initialization(self):
        """Test that IssueTools initializes correctly."""
        tools = IssueTools()
        assert tools.client is not None
        assert tools.issues_api is not None


class TestIssueToolsGetIssue:
    """Test get_issue method."""
    
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_get_issue_success(self, mock_client_class):
        """Test successful issue retrieval."""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issue_data = {
            "id": "2-123",
            "idReadable": "DEMO-123",
            "summary": "Test Issue",
            "description": "Test Description",
            "created": 1640995200000,
            "updated": 1640995200000,
            "project": {"id": "0-0", "name": "Demo", "shortName": "DEMO"},
            "reporter": {"id": "1-1", "login": "admin", "name": "Admin User"},
            "assignee": {"id": "1-2", "login": "user", "name": "Test User"}
        }
        
        mock_client.get.return_value = mock_issue_data
        
        # Test
        tools = IssueTools()
        result = tools.get_issue("DEMO-123")
        
        # Verify
        result_data = json.loads(result)
        assert result_data["id"] == "2-123"
        assert result_data["summary"] == "Test Issue"
        assert "created" in result_data
        
        # Verify API call
        expected_fields = "id,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value)"
        mock_client.get.assert_called_once_with(f"issues/DEMO-123?fields={expected_fields}")
    
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_get_issue_minimal_response(self, mock_client_class):
        """Test handling of minimal issue response."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_minimal_issue = {
            "$type": "Issue",
            "id": "2-123"
        }
        
        mock_client.get.return_value = mock_minimal_issue
        
        tools = IssueTools()
        result = tools.get_issue("DEMO-123")
        
        result_data = json.loads(result)
        assert result_data["id"] == "2-123"
        assert result_data["summary"] == "Issue DEMO-123"  # Default summary added
    
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_get_issue_api_error(self, mock_client_class):
        """Test handling of API error."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_client.get.side_effect = YouTrackAPIError("Issue not found")
        
        tools = IssueTools()
        result = tools.get_issue("NONEXISTENT-123")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Issue not found" in result_data["error"]


class TestIssueToolsSearchIssues:
    """Test search_issues method."""
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_search_issues_success(self, mock_client_class, mock_issues_client_class):
        """Test successful issue search."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues = [
            {"id": "2-123", "summary": "First Issue"},
            {"id": "2-124", "summary": "Second Issue"}
        ]
        mock_issues_api.search_issues.return_value = mock_issues
        
        tools = IssueTools()
        result = tools.search_issues("project: DEMO")
        
        result_data = json.loads(result)
        assert len(result_data) == 2
        assert result_data[0]["id"] == "2-123"
        assert result_data[1]["id"] == "2-124"
        
        mock_issues_api.search_issues.assert_called_once_with(query="project: DEMO", limit=10)
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_search_issues_with_limit(self, mock_client_class, mock_issues_client_class):
        """Test issue search with custom limit."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.search_issues.return_value = []
        
        tools = IssueTools()
        result = tools.search_issues("project: DEMO", limit=25)
        
        mock_issues_api.search_issues.assert_called_once_with(query="project: DEMO", limit=25)
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_search_issues_empty_query(self, mock_client_class, mock_issues_client_class):
        """Test issue search with empty query."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        tools = IssueTools()
        result = tools.search_issues("")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Query is required" in result_data["error"]
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_search_issues_api_error(self, mock_client_class, mock_issues_client_class):
        """Test handling of API error in search."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.search_issues.side_effect = YouTrackAPIError("Search failed")
        
        tools = IssueTools()
        result = tools.search_issues("invalid query")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Search failed" in result_data["error"]


class TestIssueToolsCreateIssue:
    """Test create_issue method."""
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_create_issue_success(self, mock_client_class, mock_issues_client_class):
        """Test successful issue creation."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_created_issue = {
            "id": "2-125",
            "idReadable": "DEMO-125",
            "summary": "New Test Issue",
            "description": "New test description"
        }
        mock_issues_api.create_issue.return_value = mock_created_issue
        
        tools = IssueTools()
        result = tools.create_issue("DEMO", "New Test Issue", "New test description")
        
        result_data = json.loads(result)
        assert result_data["id"] == "2-125"
        assert result_data["summary"] == "New Test Issue"
        
        mock_issues_api.create_issue.assert_called_once_with(
            project="DEMO",
            summary="New Test Issue", 
            description="New test description"
        )
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_create_issue_without_description(self, mock_client_class, mock_issues_client_class):
        """Test issue creation without description."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_created_issue = {
            "id": "2-126",
            "summary": "Issue without description"
        }
        mock_issues_api.create_issue.return_value = mock_created_issue
        
        tools = IssueTools()
        result = tools.create_issue("DEMO", "Issue without description")
        
        result_data = json.loads(result)
        assert result_data["id"] == "2-126"
        
        mock_issues_api.create_issue.assert_called_once_with(
            project="DEMO",
            summary="Issue without description",
            description=None
        )
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_create_issue_missing_project(self, mock_client_class, mock_issues_client_class):
        """Test create issue with missing project."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = IssueTools()
        result = tools.create_issue("", "Test Issue")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Project is required" in result_data["error"]
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_create_issue_missing_summary(self, mock_client_class, mock_issues_client_class):
        """Test create issue with missing summary."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = IssueTools()
        result = tools.create_issue("DEMO", "")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Summary is required" in result_data["error"]
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_create_issue_api_error(self, mock_client_class, mock_issues_client_class):
        """Test handling of API error in create issue."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.create_issue.side_effect = YouTrackAPIError("Project not found")
        
        tools = IssueTools()
        result = tools.create_issue("NONEXISTENT", "Test Issue")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Project not found" in result_data["error"]


class TestIssueToolsAddComment:
    """Test add_comment method."""
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_add_comment_success(self, mock_client_class, mock_issues_client_class):
        """Test successful comment addition."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_comment = {
            "id": "comment-123",
            "text": "This is a test comment",
            "author": {"login": "admin"}
        }
        mock_issues_api.add_comment.return_value = mock_comment
        
        tools = IssueTools()
        result = tools.add_comment("DEMO-123", "This is a test comment")
        
        result_data = json.loads(result)
        assert result_data["id"] == "comment-123"
        assert result_data["text"] == "This is a test comment"
        
        mock_issues_api.add_comment.assert_called_once_with(
            issue_id="DEMO-123",
            text="This is a test comment"
        )
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_add_comment_missing_issue_id(self, mock_client_class, mock_issues_client_class):
        """Test add comment with missing issue ID."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = IssueTools()
        result = tools.add_comment("", "Test comment")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Issue ID is required" in result_data["error"]
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_add_comment_missing_text(self, mock_client_class, mock_issues_client_class):
        """Test add comment with missing text."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = IssueTools()
        result = tools.add_comment("DEMO-123", "")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Comment text is required" in result_data["error"]
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_add_comment_api_error(self, mock_client_class, mock_issues_client_class):
        """Test handling of API error in add comment."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.add_comment.side_effect = YouTrackAPIError("Issue not found")
        
        tools = IssueTools()
        result = tools.add_comment("NONEXISTENT-123", "Test comment")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Issue not found" in result_data["error"]


class TestIssueToolsClose:
    """Test close method."""
    
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_close_with_close_method(self, mock_client_class):
        """Test close method when client has close method."""
        mock_client = Mock()
        mock_client.close = Mock()
        mock_client_class.return_value = mock_client
        
        tools = IssueTools()
        tools.close()
        
        mock_client.close.assert_called_once()
    
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_close_without_close_method(self, mock_client_class):
        """Test close method when client doesn't have close method."""
        mock_client = Mock()
        del mock_client.close  # Remove close method
        mock_client_class.return_value = mock_client
        
        tools = IssueTools()
        # Should not raise an exception
        tools.close()


class TestIssueToolsDefinitions:
    """Test tool definitions."""
    
    def test_get_tool_definitions(self):
        """Test that tool definitions are properly structured."""
        tools = IssueTools()
        definitions = tools.get_tool_definitions()
        
        assert isinstance(definitions, dict)
        assert "get_issue" in definitions
        assert "search_issues" in definitions  
        assert "create_issue" in definitions
        assert "add_comment" in definitions
        
        # Check structure of get_issue definition
        get_issue_def = definitions["get_issue"]
        assert "description" in get_issue_def
        assert "parameter_descriptions" in get_issue_def
        assert "issue_id" in get_issue_def["parameter_descriptions"]
        
        # Check structure of create_issue definition
        create_issue_def = definitions["create_issue"]
        assert "description" in create_issue_def
        assert "parameter_descriptions" in create_issue_def
        assert "project" in create_issue_def["parameter_descriptions"]
        assert "summary" in create_issue_def["parameter_descriptions"]


class TestIssueToolsIntegration:
    """Integration tests for IssueTools."""
    
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_tools_integration_scenario(self, mock_client_class):
        """Test a complete workflow scenario."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock get issue call for validation
        mock_client.get.return_value = {
            "id": "2-123",
            "summary": "Test Issue"
        }
        
        tools = IssueTools()
        
        # Test getting an issue
        result = tools.get_issue("DEMO-123")
        result_data = json.loads(result)
        assert result_data["id"] == "2-123"
        
        # Verify the tools can be closed
        tools.close() 