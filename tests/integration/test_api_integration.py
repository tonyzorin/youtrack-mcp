"""
Integration tests for YouTrack MCP API components.

These tests mock external API calls but test the integration between components.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.issues import IssuesClient
from youtrack_mcp.api.projects import ProjectsClient

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestAPIIntegration:
    """Integration tests for API components working together."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock YouTrack client for integration testing."""
        client = Mock(spec=YouTrackClient)
        client.base_url = "https://test.youtrack.cloud/api"
        client.api_token = "test-token"
        
        # Mock the session for create_issue calls
        mock_session = Mock()
        client.session = mock_session
        
        return client

    @pytest.fixture
    def issues_client(self, mock_client):
        """Create an IssuesClient with mocked underlying client."""
        return IssuesClient(mock_client)

    @pytest.fixture
    def projects_client(self, mock_client):
        """Create a ProjectsClient with mocked underlying client."""
        return ProjectsClient(mock_client)

    def test_create_issue_with_project_lookup(self, mock_client, issues_client, projects_client):
        """Test creating an issue with project lookup integration."""
        # Mock issue creation via session.post (no get calls needed)
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "3-47",
            "idReadable": "DEMO-47", 
            "summary": "Integration Test Issue",
            "description": "Test description"
        }
        mock_client.session.post.return_value = mock_response

        # Test creating issue with project ID
        result = issues_client.create_issue(
            project_id="0-0",
            summary="Integration Test Issue",
            description="Test description"
        )

        # Verify session.post was called for issue creation
        mock_client.session.post.assert_called_once()
        call_args = mock_client.session.post.call_args
        
        # Verify the correct URL and data were sent
        assert "issues" in call_args[0][0]  # URL contains 'issues'
        assert call_args[1]['json']['project']['id'] == "0-0"  # Correct project ID
        assert call_args[1]['json']['summary'] == "Integration Test Issue"
        
        # Verify result
        assert result.id == "3-47"
        assert result.summary == "Integration Test Issue"

    @pytest.mark.slow
    def test_custom_field_update_with_validation(self, mock_client, issues_client):
        """Test custom field update with validation using the new API behavior."""
        # Mock issue data
        mock_client.get.return_value = {
            "id": "3-47",
            "project": {"id": "0-0", "shortName": "DEMO"}
        }
        
        # Mock the direct API call (which uses client.post for custom fields)
        mock_client.post.return_value = {}
        
        # Test custom field update using new behavior (direct API first)
        result = issues_client.update_issue_custom_fields(
            issue_id="DEMO-47",
            custom_fields={"Priority": "Critical"},
            validate=False
        )
        
        # Verify API calls were made
        # The new implementation tries direct API first (via client.post)
        mock_client.post.assert_called()
        
        # Check that the correct endpoint was called
        call_args = mock_client.post.call_args
        assert "issues/DEMO-47" in call_args[0][0]

    @pytest.mark.slow
    def test_full_issue_lifecycle(self, mock_client, issues_client):
        """Test full lifecycle from creation to custom field update."""
        # Mock issue creation response
        mock_client.session.post.return_value.status_code = 201
        mock_client.session.post.return_value.json.return_value = {
            "id": "3-47",
            "idReadable": "DEMO-47",
            "project": {"id": "0-0", "shortName": "DEMO"},
            "summary": "Test Issue"
        }
        
        # Mock all get_issue calls and schema lookups for enhanced object creation
        mock_client.get.side_effect = [
            # First: get_issue for state detection (in update_issue_custom_fields)
            {"id": "3-47", "idReadable": "DEMO-47", "project": {"id": "0-0", "shortName": "DEMO"}},
            # Second: get_issue for project ID extraction (in _update_other_custom_fields) 
            {"id": "3-47", "idReadable": "DEMO-47", "project": {"id": "0-0", "shortName": "DEMO"}},
            # Third: get_custom_fields_schemas call (for enhanced object creation)
            [],  # Empty schemas (will trigger fallback to simple approach)
            # Fourth: final get_issue for return value
            {"id": "3-47", "idReadable": "DEMO-47", "project": {"id": "0-0", "shortName": "DEMO"}}
        ]
        
        # Mock custom field update call
        mock_client.post.return_value = {}
        
        # Create issue
        issue = issues_client.create_issue(
            project_id="0-0",
            summary="Test Issue",
            description="Test Description"
        )
        
        # Update custom fields
        result = issues_client.update_issue_custom_fields(
            issue_id="DEMO-47",
            custom_fields={"Priority": "High"},
            validate=False  # This skips the project validation get call
        )
        
        # Verify API calls were made correctly
        mock_client.session.post.assert_called_once()  # Issue creation
        mock_client.post.assert_called_once()  # Custom field update via direct API
        assert mock_client.get.call_count >= 3  # Enhanced object creation makes additional calls for schema lookups 