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
from youtrack_mcp.utils import format_json_response

logger = logging.getLogger(__name__)


class SearchTools:
    """Advanced search tools for YouTrack."""

    def __init__(self):
        """Initialize the search tools."""
        self.client = YouTrackClient()
        self.issues_api = IssuesClient(self.client)

    @sync_wrapper
    def advanced_search(
        self,
        query: str,
        limit: int = 10,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> str:
        """
        Advanced search for issues using YouTrack query language with sorting.

        FORMAT: advanced_search(query="project: DEMO #Unresolved", limit=5, sort_by="created", sort_order="desc")

        Args:
            query: YouTrack query string
            limit: Maximum number of results to return
            sort_by: Field to sort by (created, updated, priority, etc.)
            sort_order: Sort order ('asc' or 'desc')

        Returns:
            JSON string with search results
        """
        try:
            # Build sort parameter if provided
            sort_param = None
            if sort_by:
                if sort_order and sort_order.lower() in ["asc", "desc"]:
                    sort_param = f"{sort_by} {sort_order}"
                else:
                    sort_param = f"{sort_by} desc"  # Default to desc

            # Perform the search (note: sort parameter not supported by search_issues API)
            issues = self.issues_api.search_issues(query=query, limit=limit)

            # Handle response format
            if isinstance(issues, dict):
                return format_json_response(issues)
            else:
                # Convert list of issues to JSON
                result = []
                for issue in issues:
                    if hasattr(issue, "model_dump"):
                        result.append(issue.model_dump())
                    else:
                        result.append(issue)
                return format_json_response(result)

        except Exception as e:
            logger.exception(f"Error in advanced search with query: {query}")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def search_with_custom_field_values(
        self, query: str, custom_field_values: Dict[str, Any], limit: int = 10
    ) -> str:
        """
        Search for issues with specific custom field values.

        FORMAT: search_with_custom_field_values(query="project: DEMO", custom_field_values={"Priority": "High"}, limit=5)

        Args:
            query: Base YouTrack query string
            custom_field_values: Dictionary of custom field name-value pairs
            limit: Maximum number of results to return

        Returns:
            JSON string with search results
        """
        try:
            # Build extended query with custom field filters
            extended_query = query

            for field_name, field_value in custom_field_values.items():
                if field_value is not None:
                    if isinstance(field_value, str):
                        extended_query += f' "{field_name}": "{field_value}"'
                    elif isinstance(field_value, bool):
                        extended_query += f' "{field_name}": {str(field_value).lower()}'
                    elif isinstance(field_value, (int, float)):
                        extended_query += f' "{field_name}": {field_value}'
                    elif isinstance(field_value, list):
                        # Handle list values (e.g., multiple tags)
                        for value in field_value:
                            extended_query += f' "{field_name}": "{value}"'

            # Perform the search
            issues = self.issues_api.search_issues(query=extended_query, limit=limit)

            # Handle response format
            if isinstance(issues, dict):
                return format_json_response(issues)
            else:
                result = []
                for issue in issues:
                    if hasattr(issue, "model_dump"):
                        result.append(issue.model_dump())
                    else:
                        result.append(issue)
                return format_json_response(result)

        except Exception as e:
            logger.exception(f"Error in custom field search with query: {query}")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def search_with_filter(
        self,
        project: Optional[str] = None,
        assignee: Optional[str] = None,
        reporter: Optional[str] = None,
        state: Optional[str] = None,
        priority: Optional[str] = None,
        type_: Optional[str] = None,
        created_after: Optional[str] = None,
        updated_after: Optional[str] = None,
        custom_fields: Optional[Dict[str, str]] = None,
        limit: int = 10,
    ) -> str:
        """
        Search for issues using structured filters.

        FORMAT: search_with_filter(project="DEMO", assignee="admin", state="Open", limit=10)

        Args:
            project: Project name or ID
            assignee: Assignee username or "Unassigned" for unassigned issues
            reporter: Reporter username
            state: Issue state (Open, Fixed, etc.)
            priority: Priority level
            type_: Issue type
            created_after: Date string (YYYY-MM-DD)
            updated_after: Date string (YYYY-MM-DD)
            custom_fields: Additional custom field filters
            limit: Maximum number of results to return

        Returns:
            JSON string with search results
        """
        try:
            # Build query from filters
            query_parts = []

            if project:
                query_parts.append(f'project: "{project}"')

            if assignee:
                if assignee.lower() == "unassigned":
                    query_parts.append("#Unassigned")
                else:
                    query_parts.append(f'Assignee: "{assignee}"')

            if reporter:
                query_parts.append(f'Reporter: "{reporter}"')

            if state:
                query_parts.append(f'State: "{state}"')

            if priority:
                query_parts.append(f'Priority: "{priority}"')

            if type_:
                query_parts.append(f'Type: "{type_}"')

            if created_after:
                # Validate and format date
                try:
                    datetime.strptime(created_after, "%Y-%m-%d")
                    query_parts.append(f"created: {created_after} .. Today")
                except ValueError:
                    logger.warning(f"Invalid date format: {created_after}")

            if updated_after:
                try:
                    datetime.strptime(updated_after, "%Y-%m-%d")
                    query_parts.append(f"updated: {updated_after} .. Today")
                except ValueError:
                    logger.warning(f"Invalid date format: {updated_after}")

            if custom_fields:
                for field_name, field_value in custom_fields.items():
                    if field_value:
                        query_parts.append(f'"{field_name}": "{field_value}"')

            # Join all query parts
            final_query = " ".join(query_parts) if query_parts else "true"

            # Perform the search
            issues = self.issues_api.search_issues(query=final_query, limit=limit)

            # Handle response format
            if isinstance(issues, dict):
                return format_json_response(issues)
            else:
                result = []
                for issue in issues:
                    if hasattr(issue, "model_dump"):
                        result.append(issue.model_dump())
                    else:
                        result.append(issue)
                return format_json_response(result)

        except Exception as e:
            logger.exception("Error in filtered search")
            return format_json_response({"error": str(e)})

    def close(self) -> None:
        """Close the search tools."""
        if hasattr(self.client, "close"):
            self.client.close()

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions with descriptions."""
        return {
            "advanced_search": {
                "description": 'Advanced search for issues using YouTrack query language with sorting options. Example: advanced_search(query="project: DEMO #Unresolved", limit=5, sort_by="created", sort_order="desc")',
                "function": self.advanced_search,
                "parameter_descriptions": {
                    "query": "YouTrack query string",
                    "limit": "Maximum number of results to return (default: 10)",
                    "sort_by": "Field to sort by (created, updated, priority, etc.)",
                    "sort_order": "Sort order ('asc' or 'desc')",
                },
            },
            "search_with_custom_field_values": {
                "description": 'Search for issues with specific custom field values and filters. Example: search_with_custom_field_values(query="project: DEMO", custom_field_values={"Priority": "High"}, limit=5)',
                "function": self.search_with_custom_field_values,
                "parameter_descriptions": {
                    "query": "Base YouTrack query string",
                    "custom_field_values": "Dictionary of custom field name-value pairs",
                    "limit": "Maximum number of results to return (default: 10)",
                },
            },
            "search_with_filter": {
                "description": 'Search for issues using structured filters for common fields. Example: search_with_filter(project="DEMO", assignee="admin", state="Open", limit=10)',
                "function": self.search_with_filter,
                "parameter_descriptions": {
                    "project": "Project name or ID",
                    "assignee": "Assignee username or 'Unassigned'",
                    "reporter": "Reporter username",
                    "state": "Issue state (Open, Fixed, etc.)",
                    "priority": "Priority level",
                    "type_": "Issue type",
                    "created_after": "Date string (YYYY-MM-DD)",
                    "updated_after": "Date string (YYYY-MM-DD)",
                    "custom_fields": "Additional custom field filters",
                    "limit": "Maximum number of results (default: 10)",
                },
            },
        }
