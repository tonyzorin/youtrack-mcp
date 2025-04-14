"""
YouTrack Issue MCP tools.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.issues import IssuesClient

logger = logging.getLogger(__name__)


class IssueTools:
    """Issue-related MCP tools."""
    
    def __init__(self):
        """Initialize the issue tools."""
        self.client = YouTrackClient()
        self.issues_api = IssuesClient(self.client)
        
    def get_issue(self, issue_id: str) -> str:
        """
        Get information about a specific issue.
        
        Args:
            issue_id: The issue ID or readable ID (e.g., PROJECT-123)
            
        Returns:
            JSON string with issue information
        """
        try:
            # First try to get the issue data with explicit fields
            fields = "id,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value)"
            raw_issue = self.client.get(f"issues/{issue_id}?fields={fields}")
            
            # If we got a minimal response, enhance it with default values
            if isinstance(raw_issue, dict) and raw_issue.get('$type') == 'Issue' and 'summary' not in raw_issue:
                raw_issue['summary'] = f"Issue {issue_id}"  # Provide a default summary
            
            # Return the raw issue data directly - avoid model validation issues
            return json.dumps(raw_issue, indent=2)
            
        except Exception as e:
            logger.exception(f"Error getting issue {issue_id}")
            return json.dumps({"error": str(e)})
        
    def search_issues(self, query: str, limit: int = 10) -> str:
        """
        Search for issues using YouTrack query language.
        
        Args:
            query: The search query
            limit: Maximum number of issues to return
            
        Returns:
            JSON string with matching issues
        """
        try:
            # Request with explicit fields to get complete data
            fields = "id,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value)"
            params = {"query": query, "$top": limit, "fields": fields}
            raw_issues = self.client.get("issues", params=params)
            
            # Return the raw issues data directly
            return json.dumps(raw_issues, indent=2)
            
        except Exception as e:
            logger.exception(f"Error searching issues with query: {query}")
            return json.dumps({"error": str(e)})
    
    def create_issue(self, project_id: str, summary: str, description: Optional[str] = None) -> str:
        """
        Create a new issue in YouTrack.
        
        Args:
            project_id: The ID of the project
            summary: The issue summary
            description: The issue description (optional)
            
        Returns:
            JSON string with the created issue information
        """
        try:
            issue = self.issues_api.create_issue(project_id, summary, description)
            return json.dumps(issue.model_dump(), indent=2)
        except Exception as e:
            logger.exception(f"Error creating issue in project {project_id}")
            return json.dumps({"error": str(e)})
            
    def add_comment(self, issue_id: str, text: str) -> str:
        """
        Add a comment to an issue.
        
        Args:
            issue_id: The issue ID or readable ID
            text: The comment text
            
        Returns:
            JSON string with the result
        """
        try:
            result = self.issues_api.add_comment(issue_id, text)
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception(f"Error adding comment to issue {issue_id}")
            return json.dumps({"error": str(e)})
    
    def close(self) -> None:
        """Close the API client."""
        self.client.close()
        
    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the definitions of all issue tools.
        
        Returns:
            Dictionary mapping tool names to their configuration
        """
        return {
            "get_issue": {
                "function": self.get_issue,
                "description": "Get information about a specific YouTrack issue by its ID",
                "parameter_descriptions": {
                    "issue_id": "The issue ID or readable ID (e.g., PROJECT-123)"
                }
            },
            "get_issue_raw": {
                "function": self.get_issue_raw,
                "description": "Get raw information about a specific YouTrack issue by its ID (bypasses model validation)",
                "parameter_descriptions": {
                    "issue_id": "The issue ID or readable ID (e.g., PROJECT-123)"
                }
            },
            "search_issues": {
                "function": self.search_issues,
                "description": "Search for YouTrack issues using the query language",
                "parameter_descriptions": {
                    "query": "The search query using YouTrack query syntax",
                    "limit": "Maximum number of issues to return (default: 10)"
                }
            },
            "create_issue": {
                "function": self.create_issue,
                "description": "Create a new issue in YouTrack",
                "parameter_descriptions": {
                    "project_id": "The ID of the project",
                    "summary": "The issue summary",
                    "description": "The issue description (optional)"
                }
            },
            "add_comment": {
                "function": self.add_comment,
                "description": "Add a comment to a YouTrack issue",
                "parameter_descriptions": {
                    "issue_id": "The issue ID or readable ID",
                    "text": "The comment text"
                }
            }
        }
        
    def get_issue_raw(self, issue_id: str) -> str:
        """
        Get raw information about a specific issue, bypassing the Pydantic model.
        
        Args:
            issue_id: The issue ID or readable ID (e.g., PROJECT-123)
            
        Returns:
            JSON string with raw issue information
        """
        try:
            # Request with explicit fields to get complete data
            fields = "id,idReadable,summary,description,created,updated,resolved,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value)"
            response = self.client.get(f"issues/{issue_id}?fields={fields}")
            return json.dumps(response, indent=2)
        except Exception as e:
            logger.exception(f"Error getting issue {issue_id}")
            return json.dumps({"error": str(e)}) 