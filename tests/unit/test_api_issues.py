"""
Comprehensive unit tests for YouTrack API issues module.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from youtrack_mcp.api.issues import Issue, IssuesClient
from youtrack_mcp.api.client import YouTrackAPIError


class TestIssue:
    """Test Issue model."""

    @pytest.mark.unit
    def test_issue_creation_with_minimal_data(self):
        """Test issue creation with minimal required data."""
        issue_data = {
            "id": "TEST-123",
            "summary": "Test issue",
            "project": {"id": "0-1", "name": "Test Project"},
        }

        issue = Issue.model_validate(issue_data)

        assert issue.id == "TEST-123"
        assert issue.summary == "Test issue"
        assert issue.project is not None

    @pytest.mark.unit
    def test_issue_creation_with_complete_data(self):
        """Test issue creation with complete data."""
        issue_data = {
            "id": "TEST-123",
            "summary": "Test issue with all fields",
            "description": "This is a test issue",
            "project": {"id": "0-1", "name": "Test Project"},
            "reporter": {"login": "testuser", "fullName": "Test User"},
            "customFields": [
                {"name": "Priority", "value": {"name": "High"}},
                {"name": "Component", "value": [{"name": "Backend"}]},
            ],
        }

        issue = Issue.model_validate(issue_data)

        assert issue.id == "TEST-123"
        assert issue.summary == "Test issue with all fields"
        assert issue.description == "This is a test issue"
        assert issue.project is not None
        assert issue.reporter is not None

    @pytest.mark.unit
    def test_issue_model_fallback_validation(self):
        """Test issue model fallback validation for unexpected API data."""
        # Test with missing required field (should handle gracefully)
        incomplete_data = {
            "id": "TEST-123",
            # Missing summary and project
            "unexpected_field": "should be ignored",
        }

        # Should create issue even with incomplete data due to flexible validation
        issue = Issue.model_validate(incomplete_data)
        assert issue.id == "TEST-123"


class TestIssuesClient:
    """Test IssuesClient functionality."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock YouTrack client."""
        client = Mock()
        client.base_url = "https://test.youtrack.cloud/api"
        client.session = Mock()
        return client

    @pytest.fixture
    def issues_client(self, mock_client):
        """Create an IssuesClient with a mock client."""
        return IssuesClient(mock_client)

    @pytest.mark.unit
    def test_get_issue_success(self, issues_client, mock_client):
        """Test successful issue retrieval."""
        # Mock successful response
        mock_response = {
            "id": "TEST-123",
            "summary": "Test issue",
            "project": {"id": "0-1", "name": "Test Project"},
        }
        mock_client.get.return_value = mock_response

        result = issues_client.get_issue("TEST-123")

        assert result.id == "TEST-123"
        assert result.summary == "Test issue"
        mock_client.get.assert_called_once_with("issues/TEST-123")

    @pytest.mark.unit
    def test_get_issue_not_found(self, issues_client, mock_client):
        """Test issue retrieval when issue not found."""
        mock_client.get.side_effect = YouTrackAPIError(
            "Issue not found", status_code=404
        )

        # The method catches the exception and creates an Issue object with error info
        result = issues_client.get_issue("NOTFOUND-123")
        assert result is not None
        assert result.id == "NOTFOUND-123"
        assert "Issue not found" in result.summary

    @pytest.mark.unit
    def test_create_issue_success(self, issues_client, mock_client):
        """Test successful issue creation."""
        mock_response_obj = Mock()
        mock_response_obj.status_code = 201
        mock_response_obj.json.return_value = {
            "id": "TEST-124",
            "summary": "New test issue",
            "project": {"id": "0-1"},
        }
        mock_client.session.post.return_value = mock_response_obj

        result = issues_client.create_issue(
            project_id="0-1",
            summary="New test issue",
            description="New test description",
        )

        assert result.id == "TEST-124"
        assert result.summary == "New test issue"
        mock_client.session.post.assert_called_once()

    @pytest.mark.unit
    def test_create_issue_with_additional_fields(
        self, issues_client, mock_client
    ):
        """Test issue creation with additional fields."""
        mock_response_obj = Mock()
        mock_response_obj.status_code = 201
        mock_response_obj.json.return_value = {
            "id": "TEST-124",
            "summary": "New test issue",
            "project": {"id": "0-1"},
        }
        mock_client.session.post.return_value = mock_response_obj

        additional_fields = {
            "customFields": [
                {"name": "Priority", "value": {"name": "High"}},
                {
                    "name": "Component",
                    "value": [{"name": "Backend"}, {"name": "API"}],
                },
            ]
        }

        result = issues_client.create_issue(
            project_id="0-1",
            summary="New test issue",
            additional_fields=additional_fields,
        )

        assert result.id == "TEST-124"
        assert result.summary == "New test issue"
        mock_client.session.post.assert_called_once()

    @pytest.mark.unit
    def test_create_issue_validation_errors(self, issues_client, mock_client):
        """Test issue creation with validation errors."""
        # Test missing project ID
        with pytest.raises(ValueError, match="Project ID is required"):
            issues_client.create_issue(project_id="", summary="Test")

        # Test missing summary
        with pytest.raises(ValueError, match="Summary is required"):
            issues_client.create_issue(project_id="0-1", summary="")

    @pytest.mark.unit
    def test_create_issue_api_error(self, issues_client, mock_client):
        """Test issue creation with API error."""
        mock_response_obj = Mock()
        mock_response_obj.status_code = 400
        mock_response_obj.json.return_value = {"error": "Invalid project"}
        mock_response_obj.text = "Bad Request"
        mock_client.session.post.return_value = mock_response_obj

        with pytest.raises(YouTrackAPIError):
            issues_client.create_issue(
                project_id="invalid", summary="Test issue"
            )

    @pytest.mark.unit
    def test_search_issues_success(self, issues_client, mock_client):
        """Test successful issue search."""
        mock_response = [
            {
                "id": "TEST-123",
                "summary": "First issue",
                "project": {"id": "0-1"},
            },
            {
                "id": "TEST-124",
                "summary": "Second issue",
                "project": {"id": "0-1"},
            },
        ]
        mock_client.get.return_value = mock_response

        result = issues_client.search_issues("project: TEST", limit=10)

        assert len(result) == 2
        assert result[0].id == "TEST-123"
        assert result[1].id == "TEST-124"
        mock_client.get.assert_called_once()

    @pytest.mark.unit
    def test_search_issues_empty_results(self, issues_client, mock_client):
        """Test search with no results."""
        mock_client.get.return_value = []

        result = issues_client.search_issues("project: EMPTY")

        assert len(result) == 0
        mock_client.get.assert_called_once()

    @pytest.mark.unit
    def test_add_comment_success(self, issues_client, mock_client):
        """Test successful comment addition."""
        mock_response = {
            "id": "comment-123",
            "text": "Test comment",
            "author": {"login": "testuser"},
        }
        mock_client.post.return_value = mock_response

        result = issues_client.add_comment("TEST-123", "Test comment")

        assert result["id"] == "comment-123"
        assert result["text"] == "Test comment"
        mock_client.post.assert_called_once_with(
            "issues/TEST-123/comments", data={"text": "Test comment"}
        )

    @pytest.mark.unit
    def test_get_attachment_content_success(self, issues_client, mock_client):
        """Test successful attachment content retrieval."""
        # Mock issue response with attachments
        mock_issue_response = {
            "attachments": [
                {
                    "id": "attachment-456",
                    "url": "/api/files/attachment-456",
                    "size": 1024,
                    "name": "test.pdf",
                    "mimeType": "application/pdf",
                }
            ]
        }

        # Mock attachment content response
        mock_content_response = Mock()
        mock_content_response.status_code = 200
        mock_content_response.content = b"PDF file content"

        mock_client.get.return_value = mock_issue_response
        mock_client.session.get.return_value = mock_content_response

        result = issues_client.get_attachment_content(
            "TEST-123", "attachment-456"
        )

        assert result == b"PDF file content"
        assert mock_client.get.call_count == 1
        assert mock_client.session.get.call_count == 1

    @pytest.mark.unit
    def test_api_error_handling(self, issues_client, mock_client):
        """Test API error handling in various methods."""
        mock_client.get.side_effect = YouTrackAPIError(
            "API Error", status_code=500
        )

        # get_issue should return an Issue object with error info, not None
        result = issues_client.get_issue("TEST-123")
        assert result is not None
        assert result.id == "TEST-123"
        assert "API Error" in result.summary


class TestIssueIntegrationScenarios:
    """Test integration scenarios with multiple operations."""

    @pytest.mark.unit
    def test_full_issue_lifecycle(self):
        """Test full issue lifecycle: create, update, comment."""
        mock_client = Mock()
        mock_client.base_url = "https://test.youtrack.cloud/api"
        mock_client.session = Mock()
        issues_client = IssuesClient(mock_client)

        # Mock responses for each operation
        create_response_obj = Mock()
        create_response_obj.status_code = 201
        create_response_obj.json.return_value = {
            "id": "TEST-125",
            "summary": "Lifecycle test issue",
            "project": {"id": "0-1"},
        }

        comment_response = {
            "id": "comment-125",
            "text": "Test comment for lifecycle",
            "author": {"login": "testuser"},
        }

        # Configure mock responses
        mock_client.session.post.return_value = create_response_obj
        mock_client.post.return_value = comment_response

        # 1. Create issue
        created_issue = issues_client.create_issue(
            project_id="0-1", summary="Lifecycle test issue"
        )
        assert created_issue.id == "TEST-125"

        # 2. Add comment
        comment_result = issues_client.add_comment(
            "TEST-125", "Test comment for lifecycle"
        )
        assert comment_result["id"] == "comment-125"

        # Verify all operations were called
        assert mock_client.session.post.call_count == 1
        assert mock_client.post.call_count == 1

    @pytest.mark.unit
    def test_error_recovery_scenarios(self):
        """Test error recovery in various scenarios."""
        mock_client = Mock()
        mock_client.base_url = "https://test.youtrack.cloud/api"
        mock_client.session = Mock()
        issues_client = IssuesClient(mock_client)

        # Test create issue with network error
        mock_client.session.post.side_effect = Exception("Network error")

        with pytest.raises(Exception):
            issues_client.create_issue("0-1", "Test issue")

        # Test search issues with API error - the current implementation doesn't catch exceptions
        # so it should raise the exception
        mock_client.get.side_effect = YouTrackAPIError("Search failed", 500)
        with pytest.raises(YouTrackAPIError):
            issues_client.search_issues("invalid query")
