"""
Comprehensive unit tests for YouTrack API issues module.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from youtrack_mcp.api.issues import Issue, IssuesClient
from youtrack_mcp.api.client import YouTrackAPIError


class TestIssueModel:
    """Test cases for Issue model."""
    
    @pytest.mark.unit
    def test_issue_creation_basic(self):
        """Test basic Issue model creation."""
        issue_data = {
            "id": "TEST-123",
            "summary": "Test issue",
            "description": "Test description"
        }
        
        issue = Issue(**issue_data)
        
        assert issue.id == "TEST-123"
        assert issue.summary == "Test issue"
        assert issue.description == "Test description"
        assert issue.custom_fields == []
        assert issue.attachments == []
    
    @pytest.mark.unit
    def test_issue_creation_with_extra_fields(self):
        """Test Issue model creation with extra fields from API."""
        issue_data = {
            "id": "TEST-123",
            "summary": "Test issue",
            "description": "Test description",
            "state": "Open",
            "priority": "High",
            "extra_field": "extra_value"
        }
        
        issue = Issue(**issue_data)
        
        assert issue.id == "TEST-123"
        assert issue.summary == "Test issue"
        assert issue.state == "Open"
        assert issue.priority == "High"
        assert issue.extra_field == "extra_value"
    
    @pytest.mark.unit
    def test_issue_creation_with_project(self):
        """Test Issue model creation with project data."""
        issue_data = {
            "id": "TEST-123",
            "summary": "Test issue",
            "project": {
                "id": "0-1",
                "name": "Test Project",
                "shortName": "TEST"
            }
        }
        
        issue = Issue(**issue_data)
        
        assert issue.id == "TEST-123"
        assert issue.project["name"] == "Test Project"
        assert issue.project["shortName"] == "TEST"
    
    @pytest.mark.unit
    def test_issue_creation_with_custom_fields(self):
        """Test Issue model creation with custom fields."""
        issue_data = {
            "id": "TEST-123",
            "summary": "Test issue",
            "custom_fields": [
                {
                    "name": "Priority",
                    "value": {"name": "High"}
                },
                {
                    "name": "Component",
                    "value": [{"name": "Backend"}, {"name": "API"}]
                }
            ]
        }
        
        issue = Issue(**issue_data)
        
        assert issue.id == "TEST-123"
        assert len(issue.custom_fields) == 2
        assert issue.custom_fields[0]["name"] == "Priority"
        assert issue.custom_fields[1]["name"] == "Component"
    
    @pytest.mark.unit
    def test_issue_model_validate_fallback(self):
        """Test Issue model_validate fallback behavior."""
        # Test with YouTrack API format that might not validate normally
        api_data = {
            "$type": "Issue",
            "idReadable": "TEST-123",
            "summary": "Test issue",
            "created": 1640995200000,
            "someUnknownField": "unknown_value"
        }
        
        issue = Issue.model_validate(api_data)
        
        # Should use idReadable as id and handle known fields
        assert issue.id == "TEST-123"
        assert issue.summary == "Test issue"
        assert issue.created == 1640995200000
        # Fallback validation only includes known fields
    
    @pytest.mark.unit
    def test_issue_model_validate_with_minimal_data(self):
        """Test Issue model_validate with minimal data."""
        minimal_data = {
            "$type": "Issue",
            "created": 1640995200000
        }
        
        issue = Issue.model_validate(minimal_data)
        
        # Should generate ID from created timestamp
        assert issue.id == "1640995200000"


class TestIssuesClient:
    """Test cases for IssuesClient class."""
    
    @pytest.fixture
    def mock_client(self):
        """Mock YouTrack client."""
        return Mock()
    
    @pytest.fixture
    def issues_client(self, mock_client):
        """Create IssuesClient with mocked YouTrack client."""
        return IssuesClient(mock_client)
    
    @pytest.mark.unit
    def test_issues_client_init(self, mock_client):
        """Test IssuesClient initialization."""
        client = IssuesClient(mock_client)
        assert client.client is mock_client
    
    @pytest.mark.unit
    def test_get_issue_success(self, issues_client, mock_client):
        """Test successful issue retrieval."""
        mock_response = {
            "id": "TEST-123",
            "summary": "Test issue",
            "description": "Test description",
            "project": {"shortName": "TEST"}
        }
        mock_client.get.return_value = mock_response
        
        result = issues_client.get_issue("TEST-123")
        
        mock_client.get.assert_called_once_with("issues/TEST-123")
        assert isinstance(result, Issue)
        assert result.id == "TEST-123"
        assert result.summary == "Test issue"
    
    @pytest.mark.unit
    def test_get_issue_detailed_response(self, issues_client, mock_client):
        """Test issue retrieval with detailed response when summary is missing."""
        # First response missing summary
        first_response = {
            "$type": "Issue",
            "id": "TEST-123"
        }
        # Second response with full details
        detailed_response = {
            "id": "TEST-123",
            "summary": "Test issue",
            "customFields": [{"name": "Priority", "value": {"name": "High"}}]
        }
        mock_client.get.side_effect = [first_response, detailed_response]
        
        result = issues_client.get_issue("TEST-123")
        
        # Should make two calls - first basic, then detailed
        assert mock_client.get.call_count == 2
        assert result.id == "TEST-123"
        assert result.summary == "Test issue"
    
    @pytest.mark.unit
    def test_get_issue_not_found(self, issues_client, mock_client):
        """Test issue retrieval when issue not found."""
        mock_client.get.side_effect = YouTrackAPIError("Issue not found", status_code=404)
        
        with pytest.raises(YouTrackAPIError):
            issues_client.get_issue("NOTFOUND-123")
    
    @pytest.mark.unit
    def test_create_issue_success(self, issues_client, mock_client):
        """Test successful issue creation."""
        mock_response = {
            "id": "TEST-124",
            "summary": "New test issue",
            "project": {"id": "0-1"}
        }
        mock_client.post.return_value = mock_response
        
        result = issues_client.create_issue(
            project_id="0-1",
            summary="New test issue",
            description="New test description"
        )
        
        expected_data = {
            "project": {"id": "0-1"},
            "summary": "New test issue",
            "description": "New test description"
        }
        mock_client.post.assert_called_once_with("issues", data=expected_data)
        assert isinstance(result, Issue)
        assert result.id == "TEST-124"
    
    @pytest.mark.unit
    def test_create_issue_with_additional_fields(self, issues_client, mock_client):
        """Test issue creation with additional fields."""
        mock_response = {
            "id": "TEST-124",
            "summary": "New test issue",
            "project": {"id": "0-1"}
        }
        mock_client.post.return_value = mock_response
        
        additional_fields = {
            "customFields": [
                {"name": "Priority", "value": {"name": "High"}},
                {"name": "Component", "value": [{"name": "Backend"}, {"name": "API"}]}
            ]
        }
        
        result = issues_client.create_issue(
            project_id="0-1",
            summary="New test issue",
            additional_fields=additional_fields
        )
        
        call_args = mock_client.post.call_args[1]["data"]
        assert "customFields" in call_args
        assert isinstance(result, Issue)
        assert result.id == "TEST-124"
    
    @pytest.mark.unit
    def test_update_issue_success(self, issues_client, mock_client):
        """Test successful issue update."""
        mock_response = {
            "id": "TEST-123",
            "summary": "Updated summary",
            "description": "Updated description"
        }
        mock_client.post.return_value = mock_response
        
        result = issues_client.update_issue(
            "TEST-123",
            summary="Updated summary",
            description="Updated description"
        )
        
        expected_data = {
            "summary": "Updated summary",
            "description": "Updated description"
        }
        mock_client.post.assert_called_once_with("issues/TEST-123", data=expected_data)
        assert isinstance(result, Issue)
        assert result.summary == "Updated summary"
    
    @pytest.mark.unit
    def test_search_issues_success(self, issues_client, mock_client):
        """Test successful issue search."""
        mock_response = [
            {
                "id": "TEST-123",
                "summary": "First issue",
                "project": {"id": "0-1"}
            },
            {
                "id": "TEST-124", 
                "summary": "Second issue",
                "project": {"id": "0-1"}
            }
        ]
        mock_client.get.return_value = mock_response
        
        result = issues_client.search_issues("project: TEST")
        
        expected_params = {
            "query": "project: TEST",
            "$top": 10,
            "fields": "id,summary,description,created,updated,project,reporter,assignee,customFields"
        }
        mock_client.get.assert_called_once_with("issues", params=expected_params)
        assert len(result) == 2
        assert all(isinstance(issue, Issue) for issue in result)
        assert result[0].id == "TEST-123"
        assert result[1].id == "TEST-124"
    
    @pytest.mark.unit
    def test_search_issues_with_limit(self, issues_client, mock_client):
        """Test issue search with custom limit."""
        mock_response = [{"id": "TEST-123", "summary": "Test issue"}]
        mock_client.get.return_value = mock_response
        
        result = issues_client.search_issues("project: TEST", limit=50)
        
        expected_params = {
            "query": "project: TEST",
            "$top": 50,
            "fields": "id,summary,description,created,updated,project,reporter,assignee,customFields"
        }
        mock_client.get.assert_called_once_with("issues", params=expected_params)
        assert len(result) == 1
    
    @pytest.mark.unit
    def test_add_comment_success(self, issues_client, mock_client):
        """Test successful comment addition."""
        mock_response = {
            "id": "comment-123",
            "text": "Test comment",
            "author": {"login": "testuser"}
        }
        mock_client.post.return_value = mock_response
        
        result = issues_client.add_comment("TEST-123", "Test comment")
        
        expected_data = {"text": "Test comment"}
        mock_client.post.assert_called_once_with(
            "issues/TEST-123/comments",
            data=expected_data
        )
        assert result["text"] == "Test comment"
    
    @pytest.mark.unit
    def test_get_attachment_content_success(self, issues_client, mock_client):
        """Test successful attachment content retrieval."""
        mock_content = b"PDF file content"
        mock_client.get.return_value = mock_content
        
        result = issues_client.get_attachment_content("TEST-123", "attachment-456")
        
        mock_client.get.assert_called_once_with("issues/TEST-123/attachments/attachment-456")
        assert result == mock_content
        assert isinstance(result, bytes)
    
    @pytest.mark.unit
    def test_api_error_handling(self, issues_client, mock_client):
        """Test API error handling in various methods."""
        mock_client.get.side_effect = YouTrackAPIError("API Error", status_code=500)
        
        with pytest.raises(YouTrackAPIError):
            issues_client.get_issue("TEST-123")
        
        with pytest.raises(YouTrackAPIError):
            issues_client.search_issues("project: TEST")
        
        with pytest.raises(YouTrackAPIError):
            issues_client.get_comments("TEST-123")
    



class TestIssueIntegrationScenarios:
    """Integration test scenarios for issues API."""
    
    @pytest.mark.unit
    def test_full_issue_lifecycle(self):
        """Test full issue lifecycle: create, update, comment."""
        mock_client = Mock()
        issues_client = IssuesClient(mock_client)
        
        # Mock responses for each operation
        create_response = {
            "id": "TEST-125",
            "summary": "Lifecycle test issue",
            "project": {"id": "0-1"}
        }
        
        update_response = {
            "id": "TEST-125",
            "summary": "Updated lifecycle test issue",
            "project": {"id": "0-1"}
        }
        
        comment_response = {
            "id": "comment-125",
            "text": "Test comment for lifecycle",
            "author": {"login": "testuser"}
        }
        
        # Configure mock responses
        mock_client.post.side_effect = [create_response, update_response, comment_response]
        
        # 1. Create issue
        created_issue = issues_client.create_issue(
            project_id="0-1",
            summary="Lifecycle test issue"
        )
        assert created_issue.id == "TEST-125"
        
        # 2. Update issue
        updated_issue = issues_client.update_issue(
            "TEST-125",
            summary="Updated lifecycle test issue"
        )
        assert updated_issue.summary == "Updated lifecycle test issue"
        
        # 3. Add comment
        comment = issues_client.add_comment("TEST-125", "Test comment for lifecycle")
        assert comment["text"] == "Test comment for lifecycle"
        
        # Verify all API calls were made
        assert mock_client.post.call_count == 3 