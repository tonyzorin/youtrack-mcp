"""
YouTrack Search MCP tools.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.search import SearchClient

logger = logging.getLogger(__name__)


class SearchTools:
    """Search-related MCP tools."""
    
    def __init__(self):
        """Initialize the search tools."""
        self.client = YouTrackClient()
        self.search_api = SearchClient(self.client)
    
    def advanced_search(self, query: str, limit: int = 10, 
                       sort_by: Optional[str] = None, 
                       sort_order: Optional[str] = None) -> str:
        """
        Advanced search for issues using YouTrack query language with sorting.
        
        Args:
            query: The search query using YouTrack query syntax
            limit: Maximum number of issues to return
            sort_by: Field to sort by (e.g., 'created', 'updated', 'priority')
            sort_order: Sort order ('asc' or 'desc')
            
        Returns:
            JSON string with matching issues
        """
        try:
            issues = self.search_api.search_issues(
                query=query, 
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order
            )
            return json.dumps(issues, indent=2)
        except Exception as e:
            logger.exception(f"Error searching issues with query: {query}")
            return json.dumps({"error": str(e)})
    
    def filter_issues(self, 
                    project: Optional[str] = None,
                    author: Optional[str] = None,
                    assignee: Optional[str] = None,
                    state: Optional[str] = None,
                    priority: Optional[str] = None,
                    text: Optional[str] = None,
                    created_after: Optional[str] = None,
                    created_before: Optional[str] = None,
                    updated_after: Optional[str] = None,
                    updated_before: Optional[str] = None,
                    limit: int = 10) -> str:
        """
        Search for issues using a structured filter approach.
        
        Args:
            project: Project ID or name
            author: Issue author (reporter) login or name
            assignee: Issue assignee login or name
            state: Issue state (e.g., "Open", "Resolved")
            priority: Issue priority
            text: Text to search in summary and description
            created_after: Issues created after this date (YYYY-MM-DD)
            created_before: Issues created before this date (YYYY-MM-DD)
            updated_after: Issues updated after this date (YYYY-MM-DD)
            updated_before: Issues updated before this date (YYYY-MM-DD)
            limit: Maximum number of issues to return
            
        Returns:
            JSON string with matching issues
        """
        try:
            issues = self.search_api.search_with_filter(
                project=project,
                author=author,
                assignee=assignee,
                state=state,
                priority=priority,
                text=text,
                created_after=created_after,
                created_before=created_before,
                updated_after=updated_after,
                updated_before=updated_before,
                limit=limit
            )
            return json.dumps(issues, indent=2)
        except Exception as e:
            logger.exception("Error filtering issues")
            return json.dumps({"error": str(e)})
    
    def search_with_custom_fields(self, 
                                query: str, 
                                custom_fields: str,
                                limit: int = 10) -> str:
        """
        Search for issues with specific custom field values.
        
        Args:
            query: The base YouTrack query string
            custom_fields: JSON string mapping custom field names to values
            limit: Maximum number of issues to return
            
        Returns:
            JSON string with matching issues
        """
        try:
            # Parse custom fields from JSON string
            custom_field_values = json.loads(custom_fields)
            
            # Validate input
            if not isinstance(custom_field_values, dict):
                return json.dumps({"error": "custom_fields must be a valid JSON object mapping field names to values"})
            
            issues = self.search_api.search_with_custom_field_values(
                query=query,
                custom_field_values=custom_field_values,
                limit=limit
            )
            return json.dumps(issues, indent=2)
        except json.JSONDecodeError:
            error_msg = "Invalid JSON format for custom_fields parameter"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})
        except Exception as e:
            logger.exception(f"Error searching with custom fields: {query}")
            return json.dumps({"error": str(e)})
    
    def get_custom_fields(self, project_id: Optional[str] = None) -> str:
        """
        Get all available custom fields, optionally for a specific project.
        
        Args:
            project_id: Optional project ID to get fields for a specific project
            
        Returns:
            JSON string with custom fields information
        """
        try:
            custom_fields = self.search_api.get_available_custom_fields(project_id)
            return json.dumps(custom_fields, indent=2)
        except Exception as e:
            logger.exception("Error getting custom fields")
            return json.dumps({"error": str(e)})
    
    def close(self) -> None:
        """Close the API client."""
        self.client.close()
    
    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the definitions of all search tools.
        
        Returns:
            Dictionary mapping tool names to their configuration
        """
        return {
            "advanced_search": {
                "function": self.advanced_search,
                "description": "Advanced search for YouTrack issues with sorting options",
                "parameter_descriptions": {
                    "query": "The search query using YouTrack query syntax",
                    "limit": "Maximum number of issues to return (default: 10)",
                    "sort_by": "Field to sort by (e.g., 'created', 'updated', 'priority')",
                    "sort_order": "Sort order ('asc' or 'desc')"
                }
            },
            "filter_issues": {
                "function": self.filter_issues,
                "description": "Search for YouTrack issues using a structured filter approach",
                "parameter_descriptions": {
                    "project": "Project ID or name",
                    "author": "Issue author (reporter) login or name",
                    "assignee": "Issue assignee login or name",
                    "state": "Issue state (e.g., 'Open', 'Resolved')",
                    "priority": "Issue priority",
                    "text": "Text to search in summary and description",
                    "created_after": "Issues created after this date (YYYY-MM-DD)",
                    "created_before": "Issues created before this date (YYYY-MM-DD)",
                    "updated_after": "Issues updated after this date (YYYY-MM-DD)",
                    "updated_before": "Issues updated before this date (YYYY-MM-DD)",
                    "limit": "Maximum number of issues to return (default: 10)"
                }
            },
            "search_with_custom_fields": {
                "function": self.search_with_custom_fields,
                "description": "Search for YouTrack issues with specific custom field values",
                "parameter_descriptions": {
                    "query": "The base YouTrack query string",
                    "custom_fields": "JSON string mapping custom field names to values",
                    "limit": "Maximum number of issues to return (default: 10)"
                }
            },
            "get_custom_fields": {
                "function": self.get_custom_fields,
                "description": "Get available custom fields for YouTrack projects",
                "parameter_descriptions": {
                    "project_id": "Optional project ID to get fields for a specific project"
                }
            }
        } 