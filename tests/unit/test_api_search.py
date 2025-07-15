import pytest
from unittest.mock import Mock, patch
import json

from youtrack_mcp.api.search import SearchClient
from youtrack_mcp.api.client import YouTrackClient


class TestSearchClient:
    """Test SearchClient functionality."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock YouTrack client."""
        client = Mock(spec=YouTrackClient)
        client.base_url = "https://test.youtrack.cloud/api"
        return client

    @pytest.fixture
    def search_client(self, mock_client):
        """Create a SearchClient instance with mock client."""
        return SearchClient(mock_client)

    @pytest.mark.unit
    def test_search_client_initialization(self, mock_client):
        """Test SearchClient initialization."""
        search_client = SearchClient(mock_client)
        assert search_client.client is mock_client

    @pytest.mark.unit
    def test_search_issues_basic(self, search_client, mock_client):
        """Test basic issue search functionality."""
        # Mock response
        mock_response = [
            {
                "id": "1-1",
                "idReadable": "TEST-1",
                "summary": "Test issue",
                "description": "Test description"
            }
        ]
        mock_client.get.return_value = mock_response

        # Call search_issues
        result = search_client.search_issues("TEST")

        # Verify API call
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "issues"
        
        # Check parameters
        params = call_args[1]["params"]
        assert params["query"] == "TEST"
        assert params["$top"] == 10
        assert params["$skip"] == 0
        assert "fields" in params
        
        # Verify result
        assert result == mock_response

    @pytest.mark.unit
    def test_search_issues_with_parameters(self, search_client, mock_client):
        """Test issue search with custom parameters."""
        mock_client.get.return_value = []

        # Call with custom parameters
        search_client.search_issues(
            query="project: TEST",
            fields=["assignee", "tags"],
            limit=20,
            offset=10,
            sort_by="created",
            sort_order="desc",
            custom_fields=["Sprint", "Story Points"]
        )

        # Verify API call parameters
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        
        assert params["query"] == "project: TEST"
        assert params["$top"] == 20
        assert params["$skip"] == 10
        assert params["$sort"] == "created"
        assert params["$sortOrder"] == "desc"
        
        # Check that fields include default and custom fields
        fields = params["fields"]
        assert "id" in fields
        assert "assignee" in fields
        assert "tags" in fields
        assert "customFields" in fields

    @pytest.mark.unit
    def test_search_issues_with_invalid_sort_order(self, search_client, mock_client):
        """Test issue search with invalid sort order."""
        mock_client.get.return_value = []

        # Call with invalid sort order
        search_client.search_issues(
            query="test",
            sort_by="created",
            sort_order="invalid"
        )

        # Verify that invalid sort order is not included
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        
        assert params["$sort"] == "created"
        assert "$sortOrder" not in params

    @pytest.mark.unit
    def test_search_issues_default_fields(self, search_client, mock_client):
        """Test that default fields are included in search."""
        mock_client.get.return_value = []

        search_client.search_issues("test")

        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        fields = params["fields"]
        
        # Check that default fields are present
        default_fields = ["id", "idReadable", "summary", "description", "created"]
        for field in default_fields:
            assert field in fields

    @pytest.mark.unit
    def test_search_with_custom_field_values_string(self, search_client, mock_client):
        """Test search with string custom field values."""
        mock_client.get.return_value = []

        # Mock the search_issues method to avoid recursion
        with patch.object(search_client, 'search_issues') as mock_search:
            search_client.search_with_custom_field_values(
                query="project: TEST",
                custom_field_values={"Sprint": "Sprint 1", "Component": "Backend"},
                limit=5
            )

            # Verify the enhanced query
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            enhanced_query = call_args[0][0]
            
            assert 'Sprint: "Sprint 1"' in enhanced_query
            assert 'Component: "Backend"' in enhanced_query
            assert call_args[1]["limit"] == 5

    @pytest.mark.unit
    def test_search_with_custom_field_values_boolean(self, search_client, mock_client):
        """Test search with boolean custom field values."""
        with patch.object(search_client, 'search_issues') as mock_search:
            search_client.search_with_custom_field_values(
                query="project: TEST",
                custom_field_values={"IsBlocked": True, "IsArchived": False}
            )

            call_args = mock_search.call_args
            enhanced_query = call_args[0][0]
            
            assert "IsBlocked: true" in enhanced_query
            assert "IsArchived: false" in enhanced_query

    @pytest.mark.unit
    def test_search_with_custom_field_values_numeric(self, search_client, mock_client):
        """Test search with numeric custom field values."""
        with patch.object(search_client, 'search_issues') as mock_search:
            search_client.search_with_custom_field_values(
                query="project: TEST",
                custom_field_values={"StoryPoints": 5, "Priority": 1.5}
            )

            call_args = mock_search.call_args
            enhanced_query = call_args[0][0]
            
            assert "StoryPoints: 5" in enhanced_query
            assert "Priority: 1.5" in enhanced_query

    @pytest.mark.unit
    def test_search_with_custom_field_values_list(self, search_client, mock_client):
        """Test search with list custom field values."""
        with patch.object(search_client, 'search_issues') as mock_search:
            search_client.search_with_custom_field_values(
                query="project: TEST",
                custom_field_values={"Labels": ["bug", "urgent", "frontend"]}
            )

            call_args = mock_search.call_args
            enhanced_query = call_args[0][0]
            
            assert 'Labels in ("bug", "urgent", "frontend")' in enhanced_query

    @pytest.mark.unit
    def test_search_with_custom_field_values_none_values(self, search_client, mock_client):
        """Test search ignores None custom field values."""
        with patch.object(search_client, 'search_issues') as mock_search:
            search_client.search_with_custom_field_values(
                query="project: TEST",
                custom_field_values={"Sprint": "Sprint 1", "Component": None, "Labels": ["bug"]}
            )

            call_args = mock_search.call_args
            enhanced_query = call_args[0][0]
            
            assert 'Sprint: "Sprint 1"' in enhanced_query
            assert "Component" not in enhanced_query
            assert 'Labels in ("bug")' in enhanced_query

    @pytest.mark.unit
    def test_search_with_filter_all_parameters(self, search_client, mock_client):
        """Test structured filter search with all parameters."""
        with patch.object(search_client, 'search_issues') as mock_search:
            search_client.search_with_filter(
                project="TEST",
                author="john.doe",
                assignee="jane.smith",
                state="Open",
                priority="High",
                text="bug fix",
                created_after="2023-01-01",
                created_before="2023-12-31",
                updated_after="2023-06-01",
                updated_before="2023-06-30",
                limit=25
            )

            call_args = mock_search.call_args
            query = call_args[0][0]
            
            # Verify all filters are in the query
            assert 'project: "TEST"' in query
            assert 'reporter: "john.doe"' in query
            assert 'assignee: "jane.smith"' in query
            assert 'State: "Open"' in query
            assert 'Priority: "High"' in query
            assert 'summary: "bug fix" description: "bug fix"' in query
            assert 'created: 2023-01-01 ..' in query
            assert 'created: .. 2023-12-31' in query
            assert 'updated: 2023-06-01 ..' in query
            assert 'updated: .. 2023-06-30' in query
            
            assert call_args[1]["limit"] == 25

    @pytest.mark.unit
    def test_search_with_filter_unassigned(self, search_client, mock_client):
        """Test filter search with unassigned issues."""
        with patch.object(search_client, 'search_issues') as mock_search:
            search_client.search_with_filter(assignee="unassigned")

            call_args = mock_search.call_args
            query = call_args[0][0]
            
            assert 'assignee: Unassigned' in query

    @pytest.mark.unit
    def test_search_with_filter_custom_fields(self, search_client, mock_client):
        """Test filter search with custom fields."""
        with patch.object(search_client, 'search_with_custom_field_values') as mock_search_cf:
            custom_fields = {"Sprint": "Sprint 1", "Labels": ["bug"]}
            
            search_client.search_with_filter(
                project="TEST",
                custom_fields=custom_fields,
                limit=15
            )

            # Should call search_with_custom_field_values
            mock_search_cf.assert_called_once()
            call_args = mock_search_cf.call_args
            
            assert 'project: "TEST"' in call_args[0][0]
            assert call_args[0][1] == custom_fields
            assert call_args[0][2] == 15

    @pytest.mark.unit
    def test_search_with_filter_minimal(self, search_client, mock_client):
        """Test filter search with minimal parameters."""
        with patch.object(search_client, 'search_issues') as mock_search:
            search_client.search_with_filter(project="TEST")

            call_args = mock_search.call_args
            query = call_args[0][0]
            
            assert query == 'project: "TEST"'
            assert call_args[1]["limit"] == 10

    @pytest.mark.unit
    def test_get_available_custom_fields_all(self, search_client, mock_client):
        """Test getting all available custom fields."""
        mock_response = [
            {
                "id": "cf1",
                "name": "Sprint",
                "fieldType": {"id": "string", "name": "string"}
            }
        ]
        mock_client.get.return_value = mock_response

        result = search_client.get_available_custom_fields()

        # Verify API call
        mock_client.get.assert_called_once_with(
            "admin/customFieldSettings/customFields",
            params={"fields": "id,name,localizedName,fieldType(id,name),isPrivate,isPublic,aliases"}
        )
        assert result == mock_response

    @pytest.mark.unit
    def test_get_available_custom_fields_project_specific(self, search_client, mock_client):
        """Test getting custom fields for a specific project."""
        mock_response = []
        mock_client.get.return_value = mock_response

        result = search_client.get_available_custom_fields(project_id="TEST")

        # Verify API call
        mock_client.get.assert_called_once_with(
            "admin/projects/TEST/customFields",
            params={"fields": "id,name,localizedName,fieldType(id,name),isPrivate,isPublic,aliases"}
        )
        assert result == mock_response


class TestSearchClientIntegration:
    """Integration tests for SearchClient."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock YouTrack client for integration tests."""
        client = Mock(spec=YouTrackClient)
        client.base_url = "https://test.youtrack.cloud/api"
        return client

    @pytest.mark.unit
    def test_complex_search_scenario(self, mock_client):
        """Test a complex search scenario combining multiple features."""
        search_client = SearchClient(mock_client)
        
        # Mock response
        mock_response = [
            {
                "id": "1-1",
                "idReadable": "TEST-1",
                "summary": "Bug in login system",
                "customFields": [
                    {"name": "Sprint", "value": "Sprint 1"},
                    {"name": "StoryPoints", "value": 5}
                ]
            }
        ]
        mock_client.get.return_value = mock_response

        # Perform complex search
        result = search_client.search_issues(
            query='project: TEST state: Open priority: High',
            fields=["tags", "comments"],
            limit=50,
            sort_by="updated",
            sort_order="desc"
        )

        # Verify result
        assert result == mock_response
        
        # Verify API call was made correctly
        assert mock_client.get.called
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        
        assert params["query"] == 'project: TEST state: Open priority: High'
        assert params["$top"] == 50
        assert params["$sort"] == "updated"
        assert params["$sortOrder"] == "desc"

    @pytest.mark.unit
    def test_search_error_handling(self, mock_client):
        """Test search error handling."""
        search_client = SearchClient(mock_client)
        
        # Mock API error
        mock_client.get.side_effect = Exception("API Error")

        # Should propagate the exception
        with pytest.raises(Exception, match="API Error"):
            search_client.search_issues("test query")

    @pytest.mark.unit
    def test_empty_search_results(self, mock_client):
        """Test handling of empty search results."""
        search_client = SearchClient(mock_client)
        mock_client.get.return_value = []

        result = search_client.search_issues("nonexistent query")
        
        assert result == []
        assert mock_client.get.called


class TestSearchClientEdgeCases:
    """Test edge cases and error scenarios for SearchClient."""

    @pytest.fixture
    def search_client(self):
        """Create a SearchClient with mock client."""
        mock_client = Mock(spec=YouTrackClient)
        return SearchClient(mock_client)

    @pytest.mark.unit
    def test_search_with_empty_query(self, search_client):
        """Test search with empty query string."""
        search_client.client.get.return_value = []
        
        result = search_client.search_issues("")
        
        # Should still work with empty query
        assert result == []
        assert search_client.client.get.called

    @pytest.mark.unit
    def test_search_with_special_characters(self, search_client):
        """Test search with special characters in query."""
        search_client.client.get.return_value = []
        
        # Query with special characters
        special_query = 'summary: "Bug with & special chars: @#$%"'
        search_client.search_issues(special_query)
        
        call_args = search_client.client.get.call_args
        params = call_args[1]["params"]
        assert params["query"] == special_query

    @pytest.mark.unit
    def test_search_with_zero_limit(self, search_client):
        """Test search with zero limit."""
        search_client.client.get.return_value = []
        
        result = search_client.search_issues("test", limit=0)
        
        call_args = search_client.client.get.call_args
        params = call_args[1]["params"]
        assert params["$top"] == 0

    @pytest.mark.unit
    def test_search_with_large_offset(self, search_client):
        """Test search with large offset value."""
        search_client.client.get.return_value = []
        
        search_client.search_issues("test", offset=10000)
        
        call_args = search_client.client.get.call_args
        params = call_args[1]["params"]
        assert params["$skip"] == 10000

    @pytest.mark.unit
    def test_custom_field_values_with_empty_dict(self, search_client):
        """Test custom field values search with empty dictionary."""
        with patch.object(search_client, 'search_issues') as mock_search:
            search_client.search_with_custom_field_values(
                query="test",
                custom_field_values={}
            )
            
            # Should call search_issues with original query
            mock_search.assert_called_once_with("test", limit=10)

    @pytest.mark.unit
    def test_filter_search_with_empty_strings(self, search_client):
        """Test filter search with empty string parameters."""
        with patch.object(search_client, 'search_issues') as mock_search:
            search_client.search_with_filter(
                project="",
                author="",
                text=""
            )
            
            # Empty strings are treated as falsy and should be skipped
            call_args = mock_search.call_args
            query = call_args[0][0]
            
            # Query should be empty since all parameters were empty strings
            assert query == "" 