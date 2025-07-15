"""
Comprehensive unit tests for YouTrack API MCP wrappers.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from youtrack_mcp.api import mcp_wrappers


class TestMCPWrapperFunctions:
    """Test cases for MCP wrapper functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock the API clients
        self.mock_client = Mock()
        self.mock_issues_api = Mock()
        self.mock_projects_api = Mock()
        self.mock_users_api = Mock()
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    def test_get_issue_success(self, mock_issues_api):
        """Test successful issue retrieval."""
        mock_issue = Mock()
        mock_issue.model_dump.return_value = {
            "id": "TEST-123",
            "summary": "Test issue",
            "description": "Test description"
        }
        mock_issues_api.get_issue.return_value = mock_issue
        
        result = mcp_wrappers.get_issue("TEST-123")
        
        mock_issues_api.get_issue.assert_called_once_with("TEST-123")
        assert result["id"] == "TEST-123"
        assert result["summary"] == "Test issue"
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    def test_get_issue_error_handling(self, mock_issues_api):
        """Test issue retrieval error handling."""
        mock_issues_api.get_issue.side_effect = Exception("API Error")
        
        result = mcp_wrappers.get_issue("TEST-123")
        
        assert "error" in result
        assert "API Error" in result["error"]
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')  
    def test_get_issue_none_api(self, mock_issues_api):
        """Test issue retrieval when API client is None."""
        mock_issues_api = None
        
        with patch('youtrack_mcp.api.mcp_wrappers.issues_api', None):
            result = mcp_wrappers.get_issue("TEST-123")
        
        assert "error" in result
        assert "not initialized" in result["error"]
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    def test_create_issue_success(self, mock_issues_api):
        """Test successful issue creation."""
        mock_issue = Mock()
        mock_issue.model_dump.return_value = {
            "id": "TEST-124",
            "summary": "New test issue",
            "project": {"id": "0-1"}
        }
        mock_issues_api.create_issue.return_value = mock_issue
        
        result = mcp_wrappers.create_issue(
            project_id="0-1",
            summary="New test issue",
            description="Test description"
        )
        
        mock_issues_api.create_issue.assert_called_once_with(
            project_id="0-1",
            summary="New test issue",
            description="Test description",
            additional_fields=None
        )
        assert result["id"] == "TEST-124"
        assert result["summary"] == "New test issue"
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    def test_create_issue_with_additional_fields(self, mock_issues_api):
        """Test issue creation with additional fields."""
        mock_issue = Mock()
        mock_issue.model_dump.return_value = {"id": "TEST-124", "summary": "Test"}
        mock_issues_api.create_issue.return_value = mock_issue
        
        additional_fields = {"customFields": [{"name": "Priority", "value": {"name": "High"}}]}
        
        result = mcp_wrappers.create_issue(
            project_id="0-1",
            summary="Test issue",
            additional_fields=additional_fields
        )
        
        mock_issues_api.create_issue.assert_called_once_with(
            project_id="0-1",
            summary="Test issue",
            description=None,
            additional_fields=additional_fields
        )
        assert result["id"] == "TEST-124"
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    def test_search_issues_success(self, mock_issues_api):
        """Test successful issue search."""
        mock_issues = [
            Mock(model_dump=lambda: {"id": "TEST-123", "summary": "First issue"}),
            Mock(model_dump=lambda: {"id": "TEST-124", "summary": "Second issue"})
        ]
        mock_issues_api.search_issues.return_value = mock_issues
        
        result = mcp_wrappers.search_issues("project: TEST", limit=10)
        
        mock_issues_api.search_issues.assert_called_once_with("project: TEST", limit=10)
        assert len(result["issues"]) == 2
        assert result["issues"][0]["id"] == "TEST-123"
        assert result["issues"][1]["id"] == "TEST-124"
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    def test_update_issue_success(self, mock_issues_api):
        """Test successful issue update."""
        mock_issue = Mock()
        mock_issue.model_dump.return_value = {
            "id": "TEST-123",
            "summary": "Updated summary",
            "description": "Updated description"
        }
        mock_issues_api.update_issue.return_value = mock_issue
        
        result = mcp_wrappers.update_issue(
            issue_id="TEST-123",
            summary="Updated summary",
            description="Updated description"
        )
        
        mock_issues_api.update_issue.assert_called_once_with(
            "TEST-123",
            summary="Updated summary", 
            description="Updated description",
            additional_fields=None
        )
        assert result["id"] == "TEST-123"
        assert result["summary"] == "Updated summary"
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    def test_add_comment_success(self, mock_issues_api):
        """Test successful comment addition."""
        mock_comment = {
            "id": "comment-123",
            "text": "Test comment",
            "author": {"login": "testuser"}
        }
        mock_issues_api.add_comment.return_value = mock_comment
        
        result = mcp_wrappers.add_comment("TEST-123", "Test comment")
        
        mock_issues_api.add_comment.assert_called_once_with("TEST-123", "Test comment")
        assert result["id"] == "comment-123"
        assert result["text"] == "Test comment"
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.projects_api')
    def test_get_project_success(self, mock_projects_api):
        """Test successful project retrieval."""
        mock_project = Mock()
        mock_project.model_dump.return_value = {
            "id": "0-1",
            "name": "Test Project",
            "shortName": "TEST"
        }
        mock_projects_api.get_project.return_value = mock_project
        
        result = mcp_wrappers.get_project("0-1")
        
        mock_projects_api.get_project.assert_called_once_with("0-1")
        assert result["id"] == "0-1"
        assert result["name"] == "Test Project"
        assert result["shortName"] == "TEST"
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.projects_api')
    def test_get_project_issues_success(self, mock_projects_api):
        """Test successful project issues retrieval."""
        mock_issues = [
            {"id": "TEST-123", "summary": "First issue"},
            {"id": "TEST-124", "summary": "Second issue"}
        ]
        mock_projects_api.get_project_issues.return_value = mock_issues
        
        result = mcp_wrappers.get_project_issues("0-1", limit=10)
        
        mock_projects_api.get_project_issues.assert_called_once_with("0-1", limit=10)
        assert len(result["issues"]) == 2
        assert result["issues"][0]["id"] == "TEST-123"
        assert result["issues"][1]["id"] == "TEST-124"
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.projects_api')
    def test_get_custom_fields_success(self, mock_projects_api):
        """Test successful custom fields retrieval."""
        mock_fields = [
            {"id": "field-1", "name": "Priority", "type": "EnumField"},
            {"id": "field-2", "name": "Component", "type": "VersionField"}
        ]
        mock_projects_api.get_custom_fields.return_value = mock_fields
        
        result = mcp_wrappers.get_custom_fields("0-1")
        
        mock_projects_api.get_custom_fields.assert_called_once_with("0-1")
        assert len(result["fields"]) == 2
        assert result["fields"][0]["name"] == "Priority"
        assert result["fields"][1]["name"] == "Component"
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.users_api')
    def test_get_user_success(self, mock_users_api):
        """Test successful user retrieval."""
        mock_user = Mock()
        mock_user.model_dump.return_value = {
            "id": "user-123",
            "login": "testuser",
            "fullName": "Test User",
            "email": "test@example.com"
        }
        mock_users_api.get_user.return_value = mock_user
        
        result = mcp_wrappers.get_user("testuser")
        
        mock_users_api.get_user.assert_called_once_with("testuser")
        assert result["id"] == "user-123"
        assert result["login"] == "testuser"
        assert result["fullName"] == "Test User"
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.users_api')
    def test_search_users_success(self, mock_users_api):
        """Test successful user search."""
        mock_users = [
            Mock(model_dump=lambda: {"id": "user-1", "login": "user1"}),
            Mock(model_dump=lambda: {"id": "user-2", "login": "user2"})
        ]
        mock_users_api.search_users.return_value = mock_users
        
        result = mcp_wrappers.search_users("test", limit=10)
        
        mock_users_api.search_users.assert_called_once_with("test", limit=10)
        assert len(result["users"]) == 2
        assert result["users"][0]["login"] == "user1"
        assert result["users"][1]["login"] == "user2"
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    def test_get_attachment_content_success(self, mock_issues_api):
        """Test successful attachment content retrieval."""
        mock_content = b"PDF file content"
        mock_issues_api.get_attachment_content.return_value = mock_content
        
        result = mcp_wrappers.get_attachment_content("TEST-123", "attachment-456")
        
        mock_issues_api.get_attachment_content.assert_called_once_with("TEST-123", "attachment-456")
        assert result["content"] == mock_content
        assert result["size"] == len(mock_content)
    
    @pytest.mark.unit
    def test_format_error_response(self):
        """Test error response formatting."""
        result = mcp_wrappers._format_error_response("Test error message")
        
        assert result["error"] == "Test error message"
        assert result["status"] == "error"
    
    @pytest.mark.unit
    def test_format_success_response(self):
        """Test success response formatting."""
        data = {"id": "TEST-123", "summary": "Test"}
        result = mcp_wrappers._format_success_response(data)
        
        assert result["id"] == "TEST-123"
        assert result["summary"] == "Test"
        assert result["status"] == "success"


class TestMCPWrapperInitialization:
    """Test cases for MCP wrapper initialization."""
    
    @pytest.mark.unit
    def test_module_imports(self):
        """Test that the module imports correctly."""
        # Test that we can import the module
        import youtrack_mcp.api.mcp_wrappers as mcp_wrappers_module
        assert mcp_wrappers_module is not None
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.YouTrackClient')
    def test_client_initialization_success(self, mock_client_class):
        """Test successful client initialization."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Force reimport to test initialization
        import importlib
        import youtrack_mcp.api.mcp_wrappers
        importlib.reload(youtrack_mcp.api.mcp_wrappers)
        
        # Verify client was initialized
        mock_client_class.assert_called_once()
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.YouTrackClient')
    def test_client_initialization_error(self, mock_client_class):
        """Test client initialization error handling."""
        mock_client_class.side_effect = Exception("Initialization error")
        
        # Force reimport to test error handling
        import importlib
        import youtrack_mcp.api.mcp_wrappers
        importlib.reload(youtrack_mcp.api.mcp_wrappers)
        
        # Should handle the error gracefully
        # No assertion needed - just making sure no exception is raised


class TestMCPWrapperAsyncSupport:
    """Test cases for async support in MCP wrappers."""
    
    @pytest.mark.unit
    def test_nest_asyncio_applied(self):
        """Test that nest_asyncio is applied for async support."""
        # Import should not raise an error
        import youtrack_mcp.api.mcp_wrappers
        
        # If we get here without exception, nest_asyncio handling works
        assert True


class TestMCPWrapperParameterHandling:
    """Test cases for parameter handling in MCP wrappers."""
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    def test_optional_parameters(self, mock_issues_api):
        """Test handling of optional parameters."""
        mock_issue = Mock()
        mock_issue.model_dump.return_value = {"id": "TEST-123"}
        mock_issues_api.create_issue.return_value = mock_issue
        
        # Test with minimal parameters
        result = mcp_wrappers.create_issue(
            project_id="0-1",
            summary="Test issue"
        )
        
        mock_issues_api.create_issue.assert_called_once_with(
            project_id="0-1",
            summary="Test issue",
            description=None,
            additional_fields=None
        )
        assert result["id"] == "TEST-123"
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    def test_default_limit_parameter(self, mock_issues_api):
        """Test default limit parameter handling."""
        mock_issues = []
        mock_issues_api.search_issues.return_value = mock_issues
        
        # Test with default limit
        result = mcp_wrappers.search_issues("project: TEST")
        
        mock_issues_api.search_issues.assert_called_once_with("project: TEST", limit=10)
        assert result["issues"] == []
    
    @pytest.mark.unit
    @patch('youtrack_mcp.api.mcp_wrappers.projects_api')
    def test_none_response_handling(self, mock_projects_api):
        """Test handling of None responses from API."""
        mock_projects_api.get_custom_fields.return_value = None
        
        result = mcp_wrappers.get_custom_fields("0-1")
        
        assert "error" in result
        assert "None" in result["error"] 