"""
YouTrack Search MCP tools.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.issues import IssuesClient
from youtrack_mcp.mcp_wrappers import sync_wrapper

logger = logging.getLogger(__name__)

class SearchTools:
    """Advanced search tools for YouTrack."""
    
    def __init__(self):
        """Initialize the search tools."""
        self.client = YouTrackClient()
        self.issues_api = IssuesClient(self.client)
    
    @sync_wrapper
    def advanced_search(self, query: str, limit: int = 10, sort_by: Optional[str] = None, 
                     sort_order: Optional[str] = None) -> str:
        """
        Advanced search for issues using YouTrack query language with sorting.
        
        FORMAT: advanced_search(query="project: DEMO #Unresolved", limit=10, sort_by="created", sort_order="desc")
        
        Args:
            query: The search query using YouTrack query language
            limit: Maximum number of issues to return
            sort_by: Field to sort by (e.g., created, updated, priority)
            sort_order: Sort order (asc or desc)
            
        Returns:
            JSON string with search results
        """
        try:
            # Create sort specification if provided
            sort_param = None
            if sort_by:
                # Default to descending order if not specified
                order = sort_order or "desc"
                sort_param = f"{sort_by} {order}"
                logger.info(f"Sorting by: {sort_param}")
                
            # Request with explicit fields to get complete data
            fields = "id,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value)"
            params = {"query": query, "$top": limit, "fields": fields}
            
            if sort_param:
                params["$sort"] = sort_param
                
            raw_issues = self.client.get("issues", params=params)
            
            # Return the raw issues data directly
            return json.dumps(raw_issues, indent=2)
            
        except Exception as e:
            logger.exception(f"Error performing advanced search with query: {query}")
            return json.dumps({"error": str(e)})
    
    @sync_wrapper
    def filter_issues(self, project: Optional[str] = None, author: Optional[str] = None, 
                   assignee: Optional[str] = None, state: Optional[str] = None, 
                   priority: Optional[str] = None, text: Optional[str] = None,
                   created_after: Optional[str] = None, created_before: Optional[str] = None,
                   updated_after: Optional[str] = None, updated_before: Optional[str] = None,
                   limit: int = 10) -> str:
        """
        Search for issues using a structured filter approach.
        
        FORMAT: filter_issues(project="DEMO", author="user", assignee="user", state="Open", priority="High", text="bug", created_after="2023-01-01", created_before="2023-06-30", updated_after="2023-01-01", updated_before="2023-06-30", limit=10)
        
        Args:
            project: Filter by project (name or ID)
            author: Filter by issue reporter/author
            assignee: Filter by issue assignee
            state: Filter by issue state (e.g., Open, Resolved)
            priority: Filter by priority (e.g., Critical, High)
            text: Text to search in summary and description
            created_after: Filter issues created after this date (YYYY-MM-DD)
            created_before: Filter issues created before this date (YYYY-MM-DD)
            updated_after: Filter issues updated after this date (YYYY-MM-DD)
            updated_before: Filter issues updated before this date (YYYY-MM-DD)
            limit: Maximum number of issues to return
            
        Returns:
            JSON string with matching issues
        """
        try:
            # Build YouTrack query from structured filters
            query_parts = []
            
            if project:
                query_parts.append(f"project: {project}")
                
            if author:
                query_parts.append(f"reporter: {author}")
                
            if assignee:
                query_parts.append(f"assignee: {assignee}")
                
            if state:
                # Handle common states
                if state.lower() == "open" or state.lower() == "unresolved":
                    query_parts.append("#Unresolved")
                elif state.lower() == "resolved":
                    query_parts.append("#Resolved")
                else:
                    query_parts.append(f"State: {state}")
                    
            if priority:
                query_parts.append(f"Priority: {priority}")
                
            if text:
                # Search in summary and description
                query_parts.append(f'"{text}"')
                
            # Handle date filters
            if created_after:
                try:
                    # Validate date format
                    date = datetime.strptime(created_after, "%Y-%m-%d")
                    query_parts.append(f"created: {created_after} ..")
                except ValueError:
                    logger.warning(f"Invalid date format for created_after: {created_after}")
                    
            if created_before:
                try:
                    date = datetime.strptime(created_before, "%Y-%m-%d")
                    query_parts.append(f"created: .. {created_before}")
                except ValueError:
                    logger.warning(f"Invalid date format for created_before: {created_before}")
                    
            if updated_after:
                try:
                    date = datetime.strptime(updated_after, "%Y-%m-%d")
                    query_parts.append(f"updated: {updated_after} ..")
                except ValueError:
                    logger.warning(f"Invalid date format for updated_after: {updated_after}")
                    
            if updated_before:
                try:
                    date = datetime.strptime(updated_before, "%Y-%m-%d")
                    query_parts.append(f"updated: .. {updated_before}")
                except ValueError:
                    logger.warning(f"Invalid date format for updated_before: {updated_before}")
            
            # Combine all parts into a single query
            if query_parts:
                query = " ".join(query_parts)
            else:
                # Default query if no filters provided
                query = ""
                
            logger.info(f"Constructed filter query: {query}")
            
            # Call advanced_search with the constructed query
            return self.advanced_search(query=query, limit=limit)
                
        except Exception as e:
            logger.exception("Error filtering issues")
            return json.dumps({"error": str(e)})
    
    @sync_wrapper
    def search_with_custom_fields(self, query: str, custom_fields: Union[str, Dict[str, Any]], limit: int = 10) -> str:
        """
        Search for issues with specific custom field values.
        
        FORMAT: search_with_custom_fields(query="project: DEMO", custom_fields={"Priority": "High", "Type": "Bug"}, limit=10)
        
        Args:
            query: Base search query
            custom_fields: Dictionary of custom field names and values, or a JSON string
            limit: Maximum number of issues to return
            
        Returns:
            JSON string with matching issues
        """
        try:
            # Parse custom_fields if it's a string
            if isinstance(custom_fields, str):
                try:
                    custom_fields = json.loads(custom_fields)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse custom_fields as JSON: {custom_fields}")
                    custom_fields = {}
            
            # Ensure custom_fields is a dictionary
            if not isinstance(custom_fields, dict):
                logger.warning(f"custom_fields is not a dictionary: {custom_fields}")
                custom_fields = {}
                
            # Add custom field conditions to the query
            query_parts = [query] if query else []
            
            for field_name, field_value in custom_fields.items():
                # Handle special case for empty values
                if field_value is None or field_value == "":
                    query_parts.append(f"{field_name}: empty")
                else:
                    query_parts.append(f"{field_name}: {field_value}")
                    
            # Combine all parts into a single query
            combined_query = " ".join(query_parts)
            logger.info(f"Search with custom fields query: {combined_query}")
            
            # Call advanced_search with the combined query
            return self.advanced_search(query=combined_query, limit=limit)
                
        except Exception as e:
            logger.exception("Error searching with custom fields")
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
                "description": "Advanced search for issues using YouTrack query language with sorting. FORMAT: advanced_search(query=\"project: DEMO #Unresolved\", limit=10, sort_by=\"created\", sort_order=\"desc\")",
                "parameters": {
                    "query": "The search query using YouTrack query language",
                    "limit": "Maximum number of issues to return (optional, default: 10)",
                    "sort_by": "Field to sort by (e.g., created, updated, priority) (optional)",
                    "sort_order": "Sort order (asc or desc) (optional, default: desc)"
                }
            },
            "filter_issues": {
                "function": self.filter_issues,
                "description": "Search for issues using a structured filter approach. FORMAT: filter_issues(project=\"DEMO\", author=\"user\", assignee=\"user\", state=\"Open\", priority=\"High\", text=\"bug\", created_after=\"2023-01-01\", created_before=\"2023-06-30\", updated_after=\"2023-01-01\", updated_before=\"2023-06-30\", limit=10)",
                "parameters": {
                    "project": "Filter by project (name or ID) (optional)",
                    "author": "Filter by issue reporter/author (optional)",
                    "assignee": "Filter by issue assignee (optional)",
                    "state": "Filter by issue state (e.g., Open, Resolved) (optional)",
                    "priority": "Filter by priority (e.g., Critical, High) (optional)",
                    "text": "Text to search in summary and description (optional)",
                    "created_after": "Filter issues created after this date (YYYY-MM-DD) (optional)",
                    "created_before": "Filter issues created before this date (YYYY-MM-DD) (optional)",
                    "updated_after": "Filter issues updated after this date (YYYY-MM-DD) (optional)",
                    "updated_before": "Filter issues updated before this date (YYYY-MM-DD) (optional)",
                    "limit": "Maximum number of issues to return (optional, default: 10)"
                }
            },
            "search_with_custom_fields": {
                "function": self.search_with_custom_fields,
                "description": "Search for issues with specific custom field values. FORMAT: search_with_custom_fields(query=\"project: DEMO\", custom_fields={\"Priority\": \"High\", \"Type\": \"Bug\"}, limit=10)",
                "parameters": {
                    "query": "Base search query",
                    "custom_fields": "Dictionary of custom field names and values, or a JSON string",
                    "limit": "Maximum number of issues to return (optional, default: 10)"
                }
            }
        } 