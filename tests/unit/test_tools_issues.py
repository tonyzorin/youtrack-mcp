"""
Unit tests for YouTrack Issue Tools.
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

# Skip this entire file - these tests are for the old monolithic IssueTools
# New modular tests are in tests/unit/tools/issues/
pytestmark = pytest.mark.skip(reason="Replaced by modular tests in tests/unit/tools/issues/")

from youtrack_mcp.tools.issues import IssueTools
from youtrack_mcp.api.client import YouTrackAPIError


class TestIssueToolsInitialization:
    """Test IssueTools initialization."""
    
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_issue_tools_initialization(self, mock_client_class):
        """Test that IssueTools initializes correctly."""
        # Mock the client instance
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = IssueTools()
        assert tools.client is not None
        assert tools.issues_api is not None
        mock_client_class.assert_called_once()


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
        
        tools = IssueTools()
        result = tools.get_issue("DEMO-123")
        
        result_data = json.loads(result)
        assert result_data["id"] == "2-123"
        assert result_data["idReadable"] == "DEMO-123"
        assert result_data["summary"] == "Test Issue"
        
        # Verify the API was called with correct parameters
        expected_fields = "id,idReadable,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value)"
        mock_client.get.assert_called_once_with(f"issues/DEMO-123?fields={expected_fields}")
    
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_get_issue_minimal_response(self, mock_client_class):
        """Test issue retrieval with minimal API response."""
        # Setup mock for minimal response
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock minimal response that needs enhancement
        mock_issue_data = {
            "$type": "Issue",
            "id": "2-123"
        }
        
        mock_client.get.return_value = mock_issue_data
        
        tools = IssueTools()
        result = tools.get_issue("DEMO-123")
        
        result_data = json.loads(result)
        assert result_data["id"] == "2-123"
        assert result_data["summary"] == "Issue DEMO-123"
    
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_get_issue_error(self, mock_client_class):
        """Test issue retrieval with error."""
        # Setup mock to raise exception
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
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        # Mock search results - search_issues uses client.get directly
        mock_search_results = [
            {"id": "2-123", "idReadable": "DEMO-123", "summary": "First Issue"},
            {"id": "2-124", "idReadable": "DEMO-124", "summary": "Second Issue"}
        ]
        mock_client.get.return_value = mock_search_results
        
        tools = IssueTools()
        result = tools.search_issues("project: DEMO", limit=5)
        
        result_data = json.loads(result)
        assert len(result_data) == 2
        assert result_data[0]["idReadable"] == "DEMO-123"
        assert result_data[1]["idReadable"] == "DEMO-124"
        
        # Verify the correct API call was made
        expected_fields = "id,idReadable,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value)"
        expected_params = {"query": "project: DEMO", "$top": 5, "fields": expected_fields}
        mock_client.get.assert_called_once_with("issues", params=expected_params)
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_search_issues_error(self, mock_client_class, mock_issues_client_class):
        """Test issue search with error."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        mock_client.get.side_effect = YouTrackAPIError("Search failed")
        
        tools = IssueTools()
        result = tools.search_issues("invalid query")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Search failed" in result_data["error"]


class TestIssueToolsCreateIssue:
    """Test create_issue method."""
    
    @patch('youtrack_mcp.tools.issues.ProjectsClient')
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_create_issue_success(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test successful issue creation."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock project lookup
        mock_project = Mock()
        mock_project.id = "0-0"
        mock_project.name = "Demo Project"
        mock_projects_api.get_project_by_name.return_value = mock_project
        
        # Mock created issue
        mock_created_issue = Mock()
        mock_created_issue.model_dump.return_value = {
            "id": "2-125",
            "idReadable": "DEMO-125",
            "summary": "New Test Issue",
            "description": "New test description"
        }
        mock_issues_api.create_issue.return_value = mock_created_issue
        
        tools = IssueTools()
        result = tools.create_issue(
            project="DEMO",
            summary="New Test Issue",
            description="New test description"
        )
        
        result_data = json.loads(result)
        assert result_data["idReadable"] == "DEMO-125"
        assert result_data["summary"] == "New Test Issue"
        
        mock_issues_api.create_issue.assert_called_once()
    
    @patch('youtrack_mcp.tools.issues.ProjectsClient')
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_create_issue_with_project_id(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test issue creation with project ID (bypasses project lookup)."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock created issue
        mock_created_issue = Mock()
        mock_created_issue.model_dump.return_value = {
            "id": "2-126",
            "idReadable": "DEMO-126",
            "summary": "Issue with ID",
            "description": "Created with project ID"
        }
        mock_issues_api.create_issue.return_value = mock_created_issue
        
        tools = IssueTools()
        result = tools.create_issue(
            project="0-0",  # Project ID format
            summary="Issue with ID",
            description="Created with project ID"
        )
        
        result_data = json.loads(result)
        assert result_data["idReadable"] == "DEMO-126"
        assert result_data["summary"] == "Issue with ID"
        
        # Should not call project lookup for ID format
        mock_projects_api.get_project_by_name.assert_not_called()
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_create_issue_validation_error(self, mock_client_class, mock_issues_client_class):
        """Test issue creation with validation error."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        tools = IssueTools()
        result = tools.create_issue(
            project="",  # Empty project should cause validation error
            summary="Test Issue"
        )
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Project is required" in result_data["error"]
    
    @patch('youtrack_mcp.tools.issues.ProjectsClient')
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_create_issue_project_not_found(self, mock_client_class, mock_issues_client_class, mock_projects_client_class):
        """Test issue creation when project is not found."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_projects_api = Mock()
        mock_projects_client_class.return_value = mock_projects_api
        
        # Mock project lookup to return None (not found)
        mock_projects_api.get_project_by_name.return_value = None
        
        tools = IssueTools()
        result = tools.create_issue(
            project="NONEXISTENT",
            summary="Test Issue"
        )
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Project not found: NONEXISTENT" in result_data["error"]


class TestIssueToolsAddComment:
    """Test add_comment method."""
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_add_comment_success(self, mock_client_class, mock_issues_client_class):
        """Test successful comment addition."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        # Mock added comment - return the dict directly to avoid serialization issues
        mock_added_comment = {
            "id": "comment-123",
            "text": "Test comment",
            "author": {"login": "testuser"},
            "created": 1640995200000
        }
        mock_issues_api.add_comment.return_value = mock_added_comment
        
        tools = IssueTools()
        result = tools.add_comment("DEMO-123", "Test comment")
        
        result_data = json.loads(result)
        assert result_data["id"] == "comment-123"
        assert result_data["text"] == "Test comment"
        
        mock_issues_api.add_comment.assert_called_once_with("DEMO-123", "Test comment")
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_add_comment_error(self, mock_client_class, mock_issues_client_class):
        """Test comment addition with error."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        mock_issues_api.add_comment.side_effect = YouTrackAPIError("Permission denied")
        
        tools = IssueTools()
        result = tools.add_comment("DEMO-123", "Test comment")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Permission denied" in result_data["error"]


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
        
        # The close method should not call client.close in the current implementation
        # It's empty in the current code
    
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_close_without_close_method(self, mock_client_class):
        """Test close method when client has no close method."""
        mock_client = Mock()
        # Create a Mock that will raise AttributeError when close is accessed
        type(mock_client).close = Mock(side_effect=AttributeError("Mock object has no attribute 'close'"))
        mock_client_class.return_value = mock_client
        
        tools = IssueTools()
        # Should raise an exception since the actual close method calls self.client.close()
        with pytest.raises(AttributeError):
            tools.close()


class TestIssueToolsGetToolDefinitions:
    """Test get_tool_definitions method."""
    
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_get_tool_definitions(self, mock_client_class):
        """Test get_tool_definitions method."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = IssueTools()
        definitions = tools.get_tool_definitions()
        
        assert isinstance(definitions, dict)
        
        # Check that all expected tools are defined
        expected_tools = [
            "get_issue", "search_issues", "create_issue", "add_comment",
            "get_issue_raw", "get_attachment_content", "link_issues",
            "get_issue_links", "get_available_link_types", "update_issue",
            "add_dependency", "remove_dependency", "add_relates_link",
            "add_duplicate_link"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in definitions
            assert "description" in definitions[tool_name]
            assert "parameter_descriptions" in definitions[tool_name]
        
        # Check specific tool structure
        get_issue_def = definitions["get_issue"]
        assert "issue_id" in get_issue_def["parameter_descriptions"]
        
        create_issue_def = definitions["create_issue"]
        assert "project" in create_issue_def["parameter_descriptions"]
        assert "summary" in create_issue_def["parameter_descriptions"]


class TestIssueToolsGetIssueRaw:
    """Test get_issue_raw method."""
    
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_get_issue_raw_success(self, mock_client_class):
        """Test successful raw issue retrieval."""
        # Setup mock
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issue_data = {
            "id": "2-123",
            "idReadable": "DEMO-123",
            "summary": "Test Issue",
            "customFields": [{"name": "Priority", "value": {"name": "High"}}],
            "attachments": [{"id": "att-1", "name": "test.txt"}],
            "comments": [{"id": "comm-1", "text": "Test comment"}]
        }
        
        mock_client.get.return_value = mock_issue_data
        
        tools = IssueTools()
        result = tools.get_issue_raw("DEMO-123")
        
        result_data = json.loads(result)
        assert result_data["id"] == "2-123"
        assert result_data["idReadable"] == "DEMO-123"
        assert "customFields" in result_data
        assert "attachments" in result_data
        assert "comments" in result_data
        
        # Verify comprehensive fields were requested
        expected_fields = "id,idReadable,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value(id,name)),attachments(id,name,size,url),comments(id,text,author(login,name),created)"
        mock_client.get.assert_called_once_with(f"issues/DEMO-123?fields={expected_fields}")
    
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_get_issue_raw_error(self, mock_client_class):
        """Test raw issue retrieval with error."""
        # Setup mock to raise exception
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.get.side_effect = YouTrackAPIError("Issue not found")
        
        tools = IssueTools()
        result = tools.get_issue_raw("NONEXISTENT-123")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Issue not found" in result_data["error"]


class TestIssueToolsGetAttachmentContent:
    """Test get_attachment_content method."""
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_get_attachment_content_success(self, mock_client_class, mock_issues_client_class):
        """Test successful attachment content retrieval."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        # Mock attachment content
        test_content = b"Test file content"
        mock_issues_api.get_attachment_content.return_value = test_content
        
        # Mock attachment metadata
        mock_client.get.return_value = {
            "attachments": [
                {
                    "id": "att-123",
                    "name": "test.txt",
                    "mimeType": "text/plain",
                    "size": 17
                }
            ]
        }
        
        tools = IssueTools()
        result = tools.get_attachment_content("DEMO-123", "att-123")
        
        result_data = json.loads(result)
        assert result_data["status"] == "success"
        assert "content" in result_data
        assert result_data["filename"] == "test.txt"
        assert result_data["mime_type"] == "text/plain"
        assert result_data["size_bytes_original"] == len(test_content)
        
        mock_issues_api.get_attachment_content.assert_called_once_with("DEMO-123", "att-123")
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_get_attachment_content_not_found(self, mock_client_class, mock_issues_client_class):
        """Test attachment content retrieval when attachment not found in metadata."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        # Mock attachment content
        test_content = b"Test file content"
        mock_issues_api.get_attachment_content.return_value = test_content
        
        # Mock attachment metadata with different attachment ID
        mock_client.get.return_value = {
            "attachments": [
                {
                    "id": "att-999",  # Different ID
                    "name": "other.txt",
                    "mimeType": "text/plain",
                    "size": 10
                }
            ]
        }
        
        tools = IssueTools()
        result = tools.get_attachment_content("DEMO-123", "att-123")
        
        result_data = json.loads(result)
        assert result_data["status"] == "success"
        assert "content" in result_data
        assert result_data["filename"] is None  # No metadata found
        assert result_data["mime_type"] is None
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_get_attachment_content_error(self, mock_client_class, mock_issues_client_class):
        """Test attachment content retrieval with error."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        mock_issues_api.get_attachment_content.side_effect = YouTrackAPIError("Attachment not found")
        
        tools = IssueTools()
        result = tools.get_attachment_content("DEMO-123", "att-123")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert result_data["status"] == "error"
        assert "Attachment not found" in result_data["error"]


class TestIssueToolsLinkIssues:
    """Test link_issues method."""
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_link_issues_success(self, mock_client_class, mock_issues_client_class):
        """Test successful issue linking."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        # Mock link result
        mock_link_result = {"status": "success", "linkType": "Relates"}
        mock_issues_api.link_issues.return_value = mock_link_result
        
        tools = IssueTools()
        result = tools.link_issues("DEMO-123", "DEMO-456", "Relates")
        
        result_data = json.loads(result)
        assert result_data["status"] == "success"
        assert result_data["linkType"] == "Relates"
        
        mock_issues_api.link_issues.assert_called_once_with("DEMO-123", "DEMO-456", "Relates")
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_link_issues_error(self, mock_client_class, mock_issues_client_class):
        """Test issue linking with error."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        mock_issues_api.link_issues.side_effect = YouTrackAPIError("Invalid link type")
        
        tools = IssueTools()
        result = tools.link_issues("DEMO-123", "DEMO-456", "InvalidType")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert result_data["status"] == "error"
        assert "Invalid link type" in result_data["error"]


class TestIssueToolsGetIssueLinks:
    """Test get_issue_links method."""
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_get_issue_links_success(self, mock_client_class, mock_issues_client_class):
        """Test successful issue links retrieval."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        # Mock links result
        mock_links_result = {
            "inward": [{"id": "link-1", "type": "Depends on", "target": "DEMO-456"}],
            "outward": [{"id": "link-2", "type": "Relates", "target": "DEMO-789"}]
        }
        mock_issues_api.get_issue_links.return_value = mock_links_result
        
        tools = IssueTools()
        result = tools.get_issue_links("DEMO-123")
        
        result_data = json.loads(result)
        assert "inward" in result_data
        assert "outward" in result_data
        assert len(result_data["inward"]) == 1
        assert len(result_data["outward"]) == 1
        
        mock_issues_api.get_issue_links.assert_called_once_with("DEMO-123")
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_get_issue_links_error(self, mock_client_class, mock_issues_client_class):
        """Test issue links retrieval with error."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        mock_issues_api.get_issue_links.side_effect = YouTrackAPIError("Issue not found")
        
        tools = IssueTools()
        result = tools.get_issue_links("NONEXISTENT-123")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert result_data["status"] == "error"
        assert "Issue not found" in result_data["error"]


class TestIssueToolsGetAvailableLinkTypes:
    """Test get_available_link_types method."""
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_get_available_link_types_success(self, mock_client_class, mock_issues_client_class):
        """Test successful link types retrieval."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        # Mock link types result
        mock_link_types = [
            {"name": "Relates", "inward": "relates to", "outward": "relates to"},
            {"name": "Depends on", "inward": "depends on", "outward": "is depended on by"},
            {"name": "Duplicates", "inward": "duplicates", "outward": "is duplicated by"}
        ]
        mock_issues_api.get_available_link_types.return_value = mock_link_types
        
        tools = IssueTools()
        result = tools.get_available_link_types()
        
        result_data = json.loads(result)
        assert len(result_data) == 3
        assert result_data[0]["name"] == "Relates"
        assert result_data[1]["name"] == "Depends on"
        assert result_data[2]["name"] == "Duplicates"
        
        mock_issues_api.get_available_link_types.assert_called_once()
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_get_available_link_types_error(self, mock_client_class, mock_issues_client_class):
        """Test link types retrieval with error."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        mock_issues_api.get_available_link_types.side_effect = YouTrackAPIError("Access denied")
        
        tools = IssueTools()
        result = tools.get_available_link_types()
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert result_data["status"] == "error"
        assert "Access denied" in result_data["error"]


class TestIssueToolsUpdateIssue:
    """Test update_issue method."""
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_update_issue_success(self, mock_client_class, mock_issues_client_class):
        """Test successful issue update."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        # Mock updated issue
        mock_updated_issue = Mock()
        mock_updated_issue.model_dump.return_value = {
            "id": "2-123",
            "idReadable": "DEMO-123",
            "summary": "Updated Summary",
            "description": "Updated Description"
        }
        mock_issues_api.update_issue.return_value = mock_updated_issue
        
        tools = IssueTools()
        result = tools.update_issue(
            "DEMO-123",
            summary="Updated Summary",
            description="Updated Description",
            additional_fields={"Priority": "High"}
        )
        
        result_data = json.loads(result)
        assert result_data["idReadable"] == "DEMO-123"
        assert result_data["summary"] == "Updated Summary"
        assert result_data["description"] == "Updated Description"
        
        mock_issues_api.update_issue.assert_called_once_with(
            issue_id="DEMO-123",
            summary="Updated Summary",
            description="Updated Description",
            additional_fields={"Priority": "High"}
        )
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_update_issue_dict_response(self, mock_client_class, mock_issues_client_class):
        """Test issue update with dict response (no model_dump)."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        # Mock updated issue as dict
        mock_updated_issue = {
            "id": "2-123",
            "idReadable": "DEMO-123",
            "summary": "Updated Summary"
        }
        mock_issues_api.update_issue.return_value = mock_updated_issue
        
        tools = IssueTools()
        result = tools.update_issue("DEMO-123", summary="Updated Summary")
        
        result_data = json.loads(result)
        assert result_data["idReadable"] == "DEMO-123"
        assert result_data["summary"] == "Updated Summary"
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_update_issue_error(self, mock_client_class, mock_issues_client_class):
        """Test issue update with error."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        mock_issues_api.update_issue.side_effect = YouTrackAPIError("Permission denied")
        
        tools = IssueTools()
        result = tools.update_issue("DEMO-123", summary="Updated Summary")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert result_data["status"] == "error"
        assert "Permission denied" in result_data["error"]


class TestIssueToolsDependencyMethods:
    """Test dependency-related methods."""
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_add_dependency_success(self, mock_client_class, mock_issues_client_class):
        """Test successful dependency addition."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        # Mock link result for dependency
        mock_link_result = {"status": "success", "linkType": "Depends on"}
        mock_issues_api.link_issues.return_value = mock_link_result
        
        tools = IssueTools()
        # Mock the link_issues method directly since add_dependency calls it
        with patch.object(tools, 'link_issues') as mock_link_issues:
            mock_link_issues.return_value = json.dumps(mock_link_result)
            
            result = tools.add_dependency("DEMO-123", "DEMO-456")
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["linkType"] == "Depends on"
            
            mock_link_issues.assert_called_once_with("DEMO-123", "DEMO-456", "Depends on")
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_add_dependency_error(self, mock_client_class, mock_issues_client_class):
        """Test dependency addition with error."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        tools = IssueTools()
        # Mock the link_issues method to raise an exception
        with patch.object(tools, 'link_issues') as mock_link_issues:
            mock_link_issues.side_effect = Exception("Link failed")
            
            result = tools.add_dependency("DEMO-123", "DEMO-456")
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert result_data["status"] == "error"
            assert "Link failed" in result_data["error"]
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_remove_dependency_success(self, mock_client_class, mock_issues_client_class):
        """Test successful dependency removal."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        # Mock internal ID methods
        mock_issues_api._get_internal_id.return_value = "internal-123"
        mock_issues_api._get_readable_id.return_value = "DEMO-456"
        
        # Mock command response
        mock_client.post.return_value = {"status": "success"}
        
        tools = IssueTools()
        result = tools.remove_dependency("DEMO-123", "DEMO-456")
        
        result_data = json.loads(result)
        assert result_data["status"] == "success"
        assert "Successfully removed dependency" in result_data["message"]
        
        # Verify command was posted
        expected_command_data = {
            "query": "remove depends on DEMO-456",
            "issues": [{"id": "internal-123"}]
        }
        mock_client.post.assert_called_once_with("commands", data=expected_command_data)
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_remove_dependency_error(self, mock_client_class, mock_issues_client_class):
        """Test dependency removal with error."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        mock_issues_api._get_internal_id.side_effect = YouTrackAPIError("Issue not found")
        
        tools = IssueTools()
        result = tools.remove_dependency("DEMO-123", "DEMO-456")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert result_data["status"] == "error"
        assert "Issue not found" in result_data["error"]


class TestIssueToolsRelatesAndDuplicateLinks:
    """Test relates and duplicate link methods."""
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_add_relates_link_success(self, mock_client_class, mock_issues_client_class):
        """Test successful relates link addition."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        tools = IssueTools()
        # Mock the link_issues method
        with patch.object(tools, 'link_issues') as mock_link_issues:
            mock_link_result = {"status": "success", "linkType": "Relates"}
            mock_link_issues.return_value = json.dumps(mock_link_result)
            
            result = tools.add_relates_link("DEMO-123", "DEMO-456")
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["linkType"] == "Relates"
            
            mock_link_issues.assert_called_once_with("DEMO-123", "DEMO-456", "Relates")
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_add_relates_link_error(self, mock_client_class, mock_issues_client_class):
        """Test relates link addition with error."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        tools = IssueTools()
        # Mock the link_issues method to raise an exception
        with patch.object(tools, 'link_issues') as mock_link_issues:
            mock_link_issues.side_effect = Exception("Link failed")
            
            result = tools.add_relates_link("DEMO-123", "DEMO-456")
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert result_data["status"] == "error"
            assert "Link failed" in result_data["error"]
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_add_duplicate_link_success(self, mock_client_class, mock_issues_client_class):
        """Test successful duplicate link addition."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        tools = IssueTools()
        # Mock the link_issues method
        with patch.object(tools, 'link_issues') as mock_link_issues:
            mock_link_result = {"status": "success", "linkType": "Duplicates"}
            mock_link_issues.return_value = json.dumps(mock_link_result)
            
            result = tools.add_duplicate_link("DEMO-123", "DEMO-456")
            
            result_data = json.loads(result)
            assert result_data["status"] == "success"
            assert result_data["linkType"] == "Duplicates"
            
            mock_link_issues.assert_called_once_with("DEMO-123", "DEMO-456", "Duplicates")
    
    @patch('youtrack_mcp.tools.issues.IssuesClient')
    @patch('youtrack_mcp.tools.issues.YouTrackClient')
    def test_add_duplicate_link_error(self, mock_client_class, mock_issues_client_class):
        """Test duplicate link addition with error."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        tools = IssueTools()
        # Mock the link_issues method to raise an exception
        with patch.object(tools, 'link_issues') as mock_link_issues:
            mock_link_issues.side_effect = Exception("Link failed")
            
            result = tools.add_duplicate_link("DEMO-123", "DEMO-456")
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert result_data["status"] == "error"
            assert "Link failed" in result_data["error"] 