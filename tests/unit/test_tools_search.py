"""
Unit tests for YouTrack Search Tools.
"""
import json
import pytest
from unittest.mock import Mock, patch

from youtrack_mcp.tools.search import SearchTools
from youtrack_mcp.api.client import YouTrackAPIError


class TestSearchToolsInitialization:
    """Test SearchTools initialization."""
    
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_search_tools_initialization(self, mock_client_class):
        """Test that SearchTools initializes correctly."""
        # Mock the client instance
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = SearchTools()
        assert tools.client is not None
        assert tools.issues_api is not None
        mock_client_class.assert_called_once()


class TestSearchToolsAdvancedSearch:
    """Test advanced_search method."""
    
    @patch('youtrack_mcp.tools.search.IssuesClient')
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_advanced_search_success(self, mock_client_class, mock_issues_client_class):
        """Test successful advanced search."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues = [
            {"id": "2-123", "summary": "Test Issue 1"},
            {"id": "2-124", "summary": "Test Issue 2"}
        ]
        mock_issues_api.search_issues.return_value = mock_issues
        
        tools = SearchTools()
        result = tools.advanced_search("project: DEMO #Unresolved")
        
        result_data = json.loads(result)
        assert len(result_data) == 2
        assert result_data[0]["id"] == "2-123"
        
        mock_issues_api.search_issues.assert_called_once_with(
            query="project: DEMO #Unresolved",
            limit=10,
            sort_by=None,
            sort_order=None
        )
    
    @patch('youtrack_mcp.tools.search.IssuesClient')
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_advanced_search_with_sorting(self, mock_client_class, mock_issues_client_class):
        """Test advanced search with sorting parameters."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.search_issues.return_value = []
        
        tools = SearchTools()
        result = tools.advanced_search(
            query="project: DEMO",
            limit=5,
            sort_by="created",
            sort_order="desc"
        )
        
        mock_issues_api.search_issues.assert_called_once_with(
            query="project: DEMO",
            limit=5,
            sort_by="created",
            sort_order="desc"
        )
    
    @patch('youtrack_mcp.tools.search.IssuesClient')
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_advanced_search_empty_query(self, mock_client_class, mock_issues_client_class):
        """Test advanced search with empty query."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = SearchTools()
        result = tools.advanced_search("")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Query is required" in result_data["error"]
    
    @patch('youtrack_mcp.tools.search.IssuesClient')
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_advanced_search_api_error(self, mock_client_class, mock_issues_client_class):
        """Test handling of API error in advanced search."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.search_issues.side_effect = YouTrackAPIError("Invalid query")
        
        tools = SearchTools()
        result = tools.advanced_search("invalid query syntax")
        
        result_data = json.loads(result)
        assert "error" in result_data
        assert "Invalid query" in result_data["error"]


class TestSearchToolsCustomFieldSearch:
    """Test search_with_custom_field_values method."""
    
    @patch('youtrack_mcp.tools.search.IssuesClient')
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_search_with_custom_field_values_success(self, mock_client_class, mock_issues_client_class):
        """Test successful search with custom field values."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues = [{"id": "2-123", "summary": "High Priority Issue"}]
        mock_issues_api.search_issues.return_value = mock_issues
        
        tools = SearchTools()
        result = tools.search_with_custom_field_values(
            query="project: DEMO",
            custom_field_values={"Priority": "High", "Assignee": "admin"}
        )
        
        result_data = json.loads(result)
        assert len(result_data) == 1
        assert result_data[0]["id"] == "2-123"
        
        # Verify the expanded query was used
        expected_query = "project: DEMO Priority: High Assignee: admin"
        mock_issues_api.search_issues.assert_called_once_with(
            query=expected_query,
            limit=10
        )
    
    @patch('youtrack_mcp.tools.search.IssuesClient')
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_search_with_custom_field_values_no_custom_fields(self, mock_client_class, mock_issues_client_class):
        """Test search with no custom fields specified."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.search_issues.return_value = []
        
        tools = SearchTools()
        result = tools.search_with_custom_field_values(query="project: DEMO")
        
        mock_issues_api.search_issues.assert_called_once_with(
            query="project: DEMO",
            limit=10
        )
    
    @patch('youtrack_mcp.tools.search.IssuesClient')
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_search_with_custom_field_values_empty_values(self, mock_client_class, mock_issues_client_class):
        """Test search with empty custom field values."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.search_issues.return_value = []
        
        tools = SearchTools()
        result = tools.search_with_custom_field_values(
            query="project: DEMO",
            custom_field_values={"Priority": "", "Assignee": None}
        )
        
        # Only base query should be used (empty/None values filtered out)
        mock_issues_api.search_issues.assert_called_once_with(
            query="project: DEMO",
            limit=10
        )


class TestSearchToolsFilterSearch:
    """Test search_with_filter method."""
    
    @patch('youtrack_mcp.tools.search.IssuesClient')
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_search_with_filter_basic(self, mock_client_class, mock_issues_client_class):
        """Test basic filter search."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues = [{"id": "2-123", "summary": "Open Issue"}]
        mock_issues_api.search_issues.return_value = mock_issues
        
        tools = SearchTools()
        result = tools.search_with_filter(
            project="DEMO",
            assignee="admin",
            state="Open"
        )
        
        result_data = json.loads(result)
        assert len(result_data) == 1
        
        # Verify the constructed query
        expected_query = "project: DEMO Assignee: admin State: Open"
        mock_issues_api.search_issues.assert_called_once_with(
            query=expected_query,
            limit=10
        )
    
    @patch('youtrack_mcp.tools.search.IssuesClient')
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_search_with_filter_unassigned(self, mock_client_class, mock_issues_client_class):
        """Test filter search for unassigned issues."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.search_issues.return_value = []
        
        tools = SearchTools()
        result = tools.search_with_filter(
            project="DEMO",
            assignee="unassigned"
        )
        
        expected_query = "project: DEMO #Unassigned"
        mock_issues_api.search_issues.assert_called_once_with(
            query=expected_query,
            limit=10
        )
    
    @patch('youtrack_mcp.tools.search.IssuesClient')
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_search_with_filter_date_filtering(self, mock_client_class, mock_issues_client_class):
        """Test filter search with date filtering."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.search_issues.return_value = []
        
        tools = SearchTools()
        result = tools.search_with_filter(
            project="DEMO",
            created_after="2023-01-01",
            updated_after="2023-06-01"
        )
        
        expected_query = "project: DEMO created: 2023-01-01 .. Today updated: 2023-06-01 .. Today"
        mock_issues_api.search_issues.assert_called_once_with(
            query=expected_query,
            limit=10
        )
    
    @patch('youtrack_mcp.tools.search.IssuesClient')
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_search_with_filter_invalid_date(self, mock_client_class, mock_issues_client_class):
        """Test filter search with invalid date format."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.search_issues.return_value = []
        
        tools = SearchTools()
        result = tools.search_with_filter(
            project="DEMO",
            created_after="invalid-date"
        )
        
        # Invalid date should be ignored, only project filter should remain
        expected_query = "project: DEMO"
        mock_issues_api.search_issues.assert_called_once_with(
            query=expected_query,
            limit=10
        )
    
    @patch('youtrack_mcp.tools.search.IssuesClient')
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_search_with_filter_custom_fields(self, mock_client_class, mock_issues_client_class):
        """Test filter search with custom fields."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.search_issues.return_value = []
        
        tools = SearchTools()
        result = tools.search_with_filter(
            project="DEMO",
            custom_fields={"Component": "Backend", "Version": "2.0"}
        )
        
        expected_query = "project: DEMO Component: Backend Version: 2.0"
        mock_issues_api.search_issues.assert_called_once_with(
            query=expected_query,
            limit=10
        )
    
    @patch('youtrack_mcp.tools.search.IssuesClient')
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_search_with_filter_no_filters(self, mock_client_class, mock_issues_client_class):
        """Test filter search with no filters (should use 'true' query)."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues_api.search_issues.return_value = []
        
        tools = SearchTools()
        result = tools.search_with_filter()
        
        expected_query = "true"
        mock_issues_api.search_issues.assert_called_once_with(
            query=expected_query,
            limit=10
        )
    
    @patch('youtrack_mcp.tools.search.IssuesClient')
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_search_with_filter_dict_response(self, mock_client_class, mock_issues_client_class):
        """Test filter search handling dictionary response."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        # Return a dictionary instead of list
        mock_issues_api.search_issues.return_value = {
            "issues": [{"id": "2-123", "summary": "Test"}],
            "total": 1
        }
        
        tools = SearchTools()
        result = tools.search_with_filter(project="DEMO")
        
        result_data = json.loads(result)
        assert "issues" in result_data
        assert result_data["total"] == 1


class TestSearchToolsClose:
    """Test close method."""
    
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_close_with_close_method(self, mock_client_class):
        """Test close method when client has close method."""
        mock_client = Mock()
        mock_client.close = Mock()
        mock_client_class.return_value = mock_client
        
        tools = SearchTools()
        tools.close()
        
        mock_client.close.assert_called_once()
    
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_close_without_close_method(self, mock_client_class):
        """Test close method when client doesn't have close method."""
        mock_client = Mock()
        # Remove close method
        if hasattr(mock_client, 'close'):
            del mock_client.close
        mock_client_class.return_value = mock_client
        
        tools = SearchTools()
        # Should not raise an exception
        tools.close()


class TestSearchToolsDefinitions:
    """Test tool definitions."""
    
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_get_tool_definitions(self, mock_client_class):
        """Test that tool definitions are properly structured."""
        # Mock the client instance
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        tools = SearchTools()
        definitions = tools.get_tool_definitions()
        
        assert isinstance(definitions, dict)
        
        expected_tools = [
            "advanced_search",
            "search_with_custom_field_values", 
            "search_with_filter"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in definitions
            assert "description" in definitions[tool_name]
            assert "parameter_descriptions" in definitions[tool_name]
        
        # Check advanced_search definition structure
        advanced_search_def = definitions["advanced_search"]
        param_descriptions = advanced_search_def["parameter_descriptions"]
        assert "query" in param_descriptions
        assert "limit" in param_descriptions
        assert "sort_by" in param_descriptions
        assert "sort_order" in param_descriptions
        
        # Check search_with_filter definition structure  
        filter_search_def = definitions["search_with_filter"]
        filter_params = filter_search_def["parameter_descriptions"]
        assert "project" in filter_params
        assert "assignee" in filter_params
        assert "state" in filter_params


class TestSearchToolsIntegration:
    """Integration tests for SearchTools."""
    
    @patch('youtrack_mcp.tools.search.IssuesClient')
    @patch('youtrack_mcp.tools.search.YouTrackClient')
    def test_complete_search_workflow(self, mock_client_class, mock_issues_client_class):
        """Test a complete search workflow scenario."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_issues_api = Mock()
        mock_issues_client_class.return_value = mock_issues_api
        
        mock_issues = [
            {"id": "2-123", "summary": "Test Issue", "priority": "High"}
        ]
        mock_issues_api.search_issues.return_value = mock_issues
        
        tools = SearchTools()
        
        # Test advanced search
        advanced_result = tools.advanced_search("project: DEMO", limit=5)
        advanced_data = json.loads(advanced_result)
        assert len(advanced_data) == 1
        
        # Test filter search
        filter_result = tools.search_with_filter(project="DEMO", state="Open")
        filter_data = json.loads(filter_result)
        assert len(filter_data) == 1
        
        # Test custom field search
        custom_result = tools.search_with_custom_field_values(
            query="project: DEMO",
            custom_field_values={"Priority": "High"}
        )
        custom_data = json.loads(custom_result)
        assert len(custom_data) == 1
        
        # Verify all methods were called correctly
        assert mock_issues_api.search_issues.call_count == 3
        
        tools.close() 