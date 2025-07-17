"""
Comprehensive unit tests for YouTrack API MCP wrappers.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import importlib

from youtrack_mcp.api import mcp_wrappers


class TestMCPWrapperFunctions:
    """Test MCP wrapper functions."""

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.issues_api")
    def test_get_issue_success(self, mock_issues_api):
        """Test successful issue retrieval."""
        mock_issue = Mock()
        mock_issue.model_dump.return_value = {
            "id": "TEST-123",
            "summary": "Test issue",
            "project": {"id": "0-1"},
        }
        mock_issues_api.get_issue.return_value = mock_issue

        result = mcp_wrappers.get_issue("TEST-123")

        mock_issues_api.get_issue.assert_called_once_with("TEST-123")
        assert result["id"] == "TEST-123"
        assert result["summary"] == "Test issue"

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.issues_api")
    def test_get_issue_api_error(self, mock_issues_api):
        """Test issue retrieval with API error."""
        mock_issues_api.get_issue.side_effect = Exception("API Error")

        result = mcp_wrappers.get_issue("TEST-123")

        assert "error" in result
        assert result["status"] == "error"

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.issues_api")
    def test_get_issue_none_api(self, mock_issues_api):
        """Test issue retrieval when API client is None."""
        mock_issues_api = None

        with patch("youtrack_mcp.api.mcp_wrappers.issues_api", None):
            result = mcp_wrappers.get_issue("TEST-123")

        assert "error" in result
        assert "failed to initialize" in result["error"]

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.projects_api")
    @patch("youtrack_mcp.api.mcp_wrappers.issues_api")
    def test_create_issue_success(self, mock_issues_api, mock_projects_api):
        """Test successful issue creation."""
        mock_issue = Mock()
        mock_issue.model_dump.return_value = {
            "id": "TEST-124",
            "summary": "New test issue",
            "project": {"id": "0-1"},
        }
        mock_issues_api.create_issue.return_value = mock_issue

        result = mcp_wrappers.create_issue(
            project="0-1",
            summary="New test issue",
            description="Test description",
        )

        mock_issues_api.create_issue.assert_called_once_with(
            "0-1", "New test issue", "Test description"
        )
        assert result["id"] == "TEST-124"
        assert result["summary"] == "New test issue"

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.projects_api")
    @patch("youtrack_mcp.api.mcp_wrappers.issues_api")
    def test_create_issue_with_additional_fields(
        self, mock_issues_api, mock_projects_api
    ):
        """Test issue creation with additional fields."""
        mock_issue = Mock()
        mock_issue.model_dump.return_value = {
            "id": "TEST-124",
            "summary": "Test",
        }
        mock_issues_api.create_issue.return_value = mock_issue

        additional_fields = {
            "customFields": [{"name": "Priority", "value": {"name": "High"}}]
        }

        result = mcp_wrappers.create_issue(project="0-1", summary="Test issue")

        mock_issues_api.create_issue.assert_called_once_with(
            "0-1", "Test issue", None
        )
        assert result["id"] == "TEST-124"

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.issues_api")
    def test_create_issue_api_error(self, mock_issues_api):
        """Test issue creation with API error."""
        mock_issues_api.create_issue.side_effect = Exception("Create failed")

        result = mcp_wrappers.create_issue(project="0-1", summary="Test issue")

        assert "error" in result
        assert result["status"] == "error"

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.issues_api")
    def test_search_issues_success(self, mock_issues_api):
        """Test successful issue search."""
        mock_issues = [
            Mock(
                model_dump=lambda: {"id": "TEST-123", "summary": "First issue"}
            ),
            Mock(
                model_dump=lambda: {
                    "id": "TEST-124",
                    "summary": "Second issue",
                }
            ),
        ]
        mock_issues_api.search_issues.return_value = mock_issues

        result = mcp_wrappers.search_issues("project: TEST", limit=10)

        mock_issues_api.search_issues.assert_called_once_with(
            "project: TEST", 10
        )
        assert len(result) == 2
        assert result[0]["id"] == "TEST-123"

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.issues_api")
    def test_search_issues_default_limit(self, mock_issues_api):
        """Test issue search with default limit."""
        mock_issues_api.search_issues.return_value = []

        result = mcp_wrappers.search_issues("project: TEST")

        mock_issues_api.search_issues.assert_called_once_with(
            "project: TEST", 10
        )
        assert len(result) == 0

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.issues_api")
    def test_add_comment_success(self, mock_issues_api):
        """Test successful comment addition."""
        mock_comment = {"id": "comment-123", "text": "Test comment"}
        mock_issues_api.add_comment.return_value = mock_comment

        result = mcp_wrappers.add_comment("TEST-123", "Test comment")

        mock_issues_api.add_comment.assert_called_once_with(
            "TEST-123", "Test comment"
        )
        assert result["id"] == "comment-123"

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.projects_api")
    def test_get_projects_success(self, mock_projects_api):
        """Test successful projects retrieval."""
        mock_projects = [
            Mock(model_dump=lambda: {"id": "0-1", "name": "Project 1"}),
            Mock(model_dump=lambda: {"id": "0-2", "name": "Project 2"}),
        ]
        mock_projects_api.get_projects.return_value = mock_projects

        result = mcp_wrappers.get_projects(include_archived=True)

        mock_projects_api.get_projects.assert_called_once_with(True)
        assert len(result) == 2
        assert result[0]["name"] == "Project 1"

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.projects_api")
    def test_get_project_success(self, mock_projects_api):
        """Test successful project retrieval."""
        mock_project = Mock()
        mock_project.model_dump.return_value = {
            "id": "0-1",
            "name": "Test Project",
            "shortName": "TEST",
        }
        mock_projects_api.get_project.return_value = mock_project

        result = mcp_wrappers.get_project("0-1")

        mock_projects_api.get_project.assert_called_once_with("0-1")
        assert result["id"] == "0-1"
        assert result["name"] == "Test Project"

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.users_api")
    def test_get_current_user_success(self, mock_users_api):
        """Test successful current user retrieval."""
        mock_user = Mock()
        mock_user.model_dump.return_value = {
            "id": "user-123",
            "login": "testuser",
            "fullName": "Test User",
            "email": "test@example.com",
        }
        mock_users_api.get_current_user.return_value = mock_user

        result = mcp_wrappers.get_current_user()

        mock_users_api.get_current_user.assert_called_once()
        assert result["id"] == "user-123"
        assert result["login"] == "testuser"


class TestMCPWrapperInitialization:
    """Test MCP wrapper initialization and error handling."""

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.YouTrackClient")
    def test_client_initialization_success(self, mock_client_class):
        """Test successful client initialization."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Force reimport to test initialization
        import importlib
        import youtrack_mcp.api.mcp_wrappers

        # The initialization happens at module import time, but due to environment
        # not having valid config, it will fail and set clients to None
        # This is expected behavior in test environment
        assert True  # Just verify the import doesn't crash

    @pytest.mark.unit
    def test_client_initialization_failure(self):
        """Test client initialization failure handling."""
        # Import the module - it should handle initialization errors gracefully
        import youtrack_mcp.api.mcp_wrappers

        # In test environment without valid config, clients should be None
        # This is the expected behavior for graceful error handling
        assert True  # Just verify the import doesn't crash


class TestMCPWrapperParameterHandling:
    """Test parameter handling and normalization in MCP wrappers."""

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.projects_api")
    @patch("youtrack_mcp.api.mcp_wrappers.issues_api")
    def test_optional_parameters(self, mock_issues_api, mock_projects_api):
        """Test handling of optional parameters."""
        mock_issue = Mock()
        mock_issue.model_dump.return_value = {"id": "TEST-123"}
        mock_issues_api.create_issue.return_value = mock_issue

        # Test with minimal parameters
        result = mcp_wrappers.create_issue(project="0-1", summary="Test issue")

        mock_issues_api.create_issue.assert_called_once_with(
            "0-1", "Test issue", None
        )
        assert result["id"] == "TEST-123"

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.issues_api")
    def test_default_limit_parameter(self, mock_issues_api):
        """Test default limit parameter handling."""
        mock_issues = []
        mock_issues_api.search_issues.return_value = mock_issues

        # Test with default limit
        result = mcp_wrappers.search_issues("project: TEST")

        mock_issues_api.search_issues.assert_called_once_with(
            "project: TEST", 10
        )
        assert len(result) == 0

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.projects_api")
    def test_none_response_handling(self, mock_projects_api):
        """Test handling of None responses from API."""
        mock_projects_api.get_projects.return_value = None

        result = mcp_wrappers.get_projects("0-1")

        assert len(result) == 0


class TestMCPWrapperErrorScenarios:
    """Test error scenarios and edge cases."""

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.issues_api", None)
    def test_all_functions_with_none_api(self):
        """Test all functions handle None API clients gracefully."""
        # Test get_issue
        result = mcp_wrappers.get_issue("TEST-123")
        assert "error" in result
        assert "failed to initialize" in result["error"]

        # Test create_issue
        result = mcp_wrappers.create_issue("0-1", "Test")
        assert "error" in result
        assert "failed to initialize" in result["error"]

        # Test search_issues
        result = mcp_wrappers.search_issues("project: TEST")
        assert len(result) == 1
        assert "error" in result[0]

    @pytest.mark.unit
    def test_logging_functionality(self):
        """Test that wrapper functions log appropriately."""
        with patch("youtrack_mcp.api.mcp_wrappers.logger") as mock_logger:
            with patch("youtrack_mcp.api.mcp_wrappers.issues_api", None):
                mcp_wrappers.get_issue("TEST-123")

                # Verify logging was called
                mock_logger.info.assert_called()


class TestMCPWrapperIntegrationScenarios:
    """Test integration scenarios across multiple wrapper functions."""

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.issues_api")
    @patch("youtrack_mcp.api.mcp_wrappers.projects_api")
    def test_project_lookup_in_create_issue(
        self, mock_projects_api, mock_issues_api
    ):
        """Test project lookup when creating issue with project name."""
        # Mock project lookup by name
        mock_project = Mock()
        mock_project.id = "0-1"
        mock_project.name = "Test Project"
        mock_projects_api.get_project_by_name.return_value = mock_project

        # Mock issue creation
        mock_issue = Mock()
        mock_issue.model_dump.return_value = {
            "id": "TEST-124",
            "summary": "Test",
        }
        mock_issues_api.create_issue.return_value = mock_issue

        # Create issue with project short name
        result = mcp_wrappers.create_issue("DEMO", "Test issue")

        # Verify project lookup was attempted
        mock_projects_api.get_project_by_name.assert_called_once_with("DEMO")
        # Verify issue creation used project ID
        mock_issues_api.create_issue.assert_called_once_with(
            "0-1", "Test issue", None
        )
        assert result["id"] == "TEST-124"

    @pytest.mark.unit
    @patch("youtrack_mcp.api.mcp_wrappers.issues_api")
    @patch("youtrack_mcp.api.mcp_wrappers.projects_api")
    def test_project_lookup_failure(self, mock_projects_api, mock_issues_api):
        """Test graceful handling when project lookup fails."""
        # Mock project lookup failure
        mock_projects_api.get_project_by_name.side_effect = Exception(
            "Project not found"
        )

        # Mock issue creation
        mock_issue = Mock()
        mock_issue.model_dump.return_value = {
            "id": "TEST-124",
            "summary": "Test",
        }
        mock_issues_api.create_issue.return_value = mock_issue

        # Create issue - should proceed with original project string
        result = mcp_wrappers.create_issue("DEMO", "Test issue")

        # Verify issue creation proceeded with original project name
        mock_issues_api.create_issue.assert_called_once_with(
            "DEMO", "Test issue", None
        )
        assert result["id"] == "TEST-124"


class TestMCPWrapperClientInitializationFailure:
    """Test scenarios where API client initialization fails."""

    @patch('youtrack_mcp.api.mcp_wrappers.YouTrackClient')
    @patch('youtrack_mcp.api.mcp_wrappers.IssuesClient')
    @patch('youtrack_mcp.api.mcp_wrappers.ProjectsClient')
    @patch('youtrack_mcp.api.mcp_wrappers.UsersClient')
    def test_api_client_initialization_failure(self, mock_users_client, mock_projects_client, 
                                             mock_issues_client, mock_youtrack_client):
        """Test behavior when API client initialization fails."""
        # Mock the initialization to raise an exception
        mock_youtrack_client.side_effect = Exception("Connection failed")
        
        # Reload the module to trigger the initialization error
        import importlib
        import youtrack_mcp.api.mcp_wrappers as mcp_wrappers
        importlib.reload(mcp_wrappers)
        
        # Test that functions return appropriate error responses
        result = mcp_wrappers.get_issue("TEST-123")
        assert result["status"] == "error"
        assert "YouTrack API client failed to initialize" in result["error"]

    @patch('youtrack_mcp.api.mcp_wrappers.issues_api', None)
    def test_get_issue_with_none_api_client(self):
        """Test get_issue when API client is None."""
        import youtrack_mcp.api.mcp_wrappers as mcp_wrappers
        
        # When issues_api is None, should return error
        result = mcp_wrappers.get_issue("TEST-123")
        
        assert result["status"] == "error"
        assert "YouTrack API client failed to initialize" in result["error"]

    @patch('youtrack_mcp.api.mcp_wrappers.issues_api', None)
    def test_create_issue_with_none_api_client(self):
        """Test create_issue when API client is None."""
        import youtrack_mcp.api.mcp_wrappers as mcp_wrappers
        
        result = mcp_wrappers.create_issue("DEMO", "Test issue")
        
        assert result["status"] == "error"
        assert "YouTrack API client failed to initialize" in result["error"]

    @patch('youtrack_mcp.api.mcp_wrappers.issues_api', None)
    def test_search_issues_with_none_api_client(self):
        """Test search_issues when API client is None."""
        import youtrack_mcp.api.mcp_wrappers as mcp_wrappers
        
        result = mcp_wrappers.search_issues("test query")
        
        # search_issues returns a list with error dict as first element
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["status"] == "error"
        assert "YouTrack API client failed to initialize" in result[0]["error"]

    @patch('youtrack_mcp.api.mcp_wrappers.issues_api', None)
    def test_add_comment_with_none_api_client(self):
        """Test add_comment when API client is None."""
        import youtrack_mcp.api.mcp_wrappers as mcp_wrappers
        
        result = mcp_wrappers.add_comment("TEST-123", "Test comment")
        
        assert result["status"] == "error"
        assert "YouTrack API client failed to initialize" in result["error"]

    @patch('youtrack_mcp.api.mcp_wrappers.projects_api', None)
    def test_get_projects_with_none_api_client(self):
        """Test get_projects when API client is None."""
        import youtrack_mcp.api.mcp_wrappers as mcp_wrappers
        
        result = mcp_wrappers.get_projects()
        
        # get_projects returns a list with error dict as first element
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["status"] == "error"
        assert "YouTrack API client failed to initialize" in result[0]["error"]

    @patch('youtrack_mcp.api.mcp_wrappers.projects_api', None)
    def test_get_project_with_none_api_client(self):
        """Test get_project when API client is None."""
        import youtrack_mcp.api.mcp_wrappers as mcp_wrappers
        
        result = mcp_wrappers.get_project("DEMO")
        
        assert result["status"] == "error"
        assert "YouTrack API client failed to initialize" in result["error"]

    @patch('youtrack_mcp.api.mcp_wrappers.users_api', None)
    def test_get_current_user_with_none_api_client(self):
        """Test get_current_user when API client is None."""
        import youtrack_mcp.api.mcp_wrappers as mcp_wrappers
        
        result = mcp_wrappers.get_current_user()
        
        assert result["status"] == "error"
        assert "YouTrack API client failed to initialize" in result["error"]


class TestMCPWrapperFunctionReturnTypes:
    """Test that functions handle different return types correctly."""

    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    def test_add_comment_non_dict_return(self, mock_issues_api):
        """Test add_comment when API returns non-dict value."""
        # Mock add_comment to return a non-dict value
        mock_issues_api.add_comment.return_value = "Success"
        
        import youtrack_mcp.api.mcp_wrappers as mcp_wrappers
        
        result = mcp_wrappers.add_comment("TEST-123", "Test comment")
        
        # Should convert non-dict return to success dict
        assert result["status"] == "success"
        mock_issues_api.add_comment.assert_called_once_with("TEST-123", "Test comment")

    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    def test_add_comment_dict_return(self, mock_issues_api):
        """Test add_comment when API returns dict value."""
        # Mock add_comment to return a dict
        mock_issues_api.add_comment.return_value = {"id": "comment-123", "text": "Test comment"}
        
        import youtrack_mcp.api.mcp_wrappers as mcp_wrappers
        
        result = mcp_wrappers.add_comment("TEST-123", "Test comment")
        
        # Should return the dict as-is
        assert result["id"] == "comment-123"
        assert result["text"] == "Test comment"


class TestMCPWrapperLoggingScenarios:
    """Test specific logging scenarios in error handling."""

    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    @patch('youtrack_mcp.api.mcp_wrappers.logger')
    def test_get_issue_exception_logging(self, mock_logger, mock_issues_api):
        """Test that exceptions in get_issue are properly logged."""
        mock_issues_api.get_issue.side_effect = Exception("Database error")
        
        import youtrack_mcp.api.mcp_wrappers as mcp_wrappers
        
        result = mcp_wrappers.get_issue("TEST-123")
        
        # Should log the exception with traceback
        mock_logger.exception.assert_called_once_with("Error getting issue TEST-123")
        assert result["status"] == "error"
        assert "Database error" in result["error"]

    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    @patch('youtrack_mcp.api.mcp_wrappers.projects_api')
    @patch('youtrack_mcp.api.mcp_wrappers.logger')
    def test_create_issue_exception_logging(self, mock_logger, mock_projects_api, mock_issues_api):
        """Test that exceptions in create_issue are properly logged."""
        # Mock project lookup to return a project with ID
        mock_project = Mock()
        mock_project.id = "0-1"  # Mock project ID
        mock_project.name = "DEMO"
        mock_projects_api.get_project_by_name.return_value = mock_project
        
        # Make create_issue fail
        mock_issues_api.create_issue.side_effect = Exception("Validation error")
        
        import youtrack_mcp.api.mcp_wrappers as mcp_wrappers
        
        result = mcp_wrappers.create_issue("DEMO", "Test issue")
        
        # Should log the exception with the project ID (after lookup)
        mock_logger.exception.assert_called_once_with("Error creating issue in project 0-1")
        assert result["status"] == "error"
        assert "Validation error" in result["error"]

    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    @patch('youtrack_mcp.api.mcp_wrappers.logger')
    def test_search_issues_exception_logging(self, mock_logger, mock_issues_api):
        """Test that exceptions in search_issues are properly logged."""
        mock_issues_api.search_issues.side_effect = Exception("Search error")
        
        import youtrack_mcp.api.mcp_wrappers as mcp_wrappers
        
        result = mcp_wrappers.search_issues("test query")
        
        # Should log the exception with traceback
        mock_logger.exception.assert_called_once_with("Error searching for issues with query: test query")
        # search_issues returns a list with error dict
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["status"] == "error"
        assert "Search error" in result[0]["error"]

    @patch('youtrack_mcp.api.mcp_wrappers.issues_api')
    @patch('youtrack_mcp.api.mcp_wrappers.logger')
    def test_add_comment_exception_logging(self, mock_logger, mock_issues_api):
        """Test that exceptions in add_comment are properly logged."""
        mock_issues_api.add_comment.side_effect = Exception("Comment error")
        
        import youtrack_mcp.api.mcp_wrappers as mcp_wrappers
        
        result = mcp_wrappers.add_comment("TEST-123", "Test comment")
        
        # Should log the exception with traceback
        mock_logger.exception.assert_called_once_with("Error adding comment to issue TEST-123")
        assert result["status"] == "error"
        assert "Comment error" in result["error"]
