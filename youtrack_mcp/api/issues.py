"""
YouTrack Issues API client.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from youtrack_mcp.api.client import YouTrackClient


class Issue(BaseModel):
    """Model for a YouTrack issue."""
    
    id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    created: Optional[int] = None
    updated: Optional[int] = None
    project: Dict[str, Any] = Field(default_factory=dict)
    reporter: Optional[Dict[str, Any]] = None
    assignee: Optional[Dict[str, Any]] = None
    custom_fields: List[Dict[str, Any]] = Field(default_factory=list)
    
    model_config = {
        "extra": "allow",  # Allow extra fields from the API
        "populate_by_name": True  # Allow population by field name (helps with aliases)
    }


class IssuesClient:
    """Client for interacting with YouTrack Issues API."""
    
    def __init__(self, client: YouTrackClient):
        """
        Initialize the Issues API client.
        
        Args:
            client: The YouTrack API client
        """
        self.client = client
    
    def get_issue(self, issue_id: str) -> Issue:
        """
        Get an issue by ID.
        
        Args:
            issue_id: The issue ID or readable ID (e.g., PROJECT-123)
            
        Returns:
            The issue data
        """
        response = self.client.get(f"issues/{issue_id}")
        
        # If the response doesn't have all needed fields, fetch more details
        if isinstance(response, dict) and response.get('$type') == 'Issue' and 'summary' not in response:
            # Get additional fields we need
            fields = "summary,description,created,updated,project,reporter,assignee,customFields"
            detailed_response = self.client.get(f"issues/{issue_id}?fields={fields}")
            return Issue.model_validate(detailed_response)
        
        return Issue.model_validate(response)
    
    def create_issue(self, 
                     project_id: str, 
                     summary: str, 
                     description: Optional[str] = None,
                     additional_fields: Optional[Dict[str, Any]] = None) -> Issue:
        """
        Create a new issue.
        
        Args:
            project_id: The ID of the project
            summary: The issue summary
            description: The issue description
            additional_fields: Additional fields to set on the issue
            
        Returns:
            The created issue data
        """
        data = {
            "project": {"id": project_id},
            "summary": summary,
        }
        
        if description:
            data["description"] = description
            
        if additional_fields:
            data.update(additional_fields)
            
        response = self.client.post("issues", data=data)
        return Issue.model_validate(response)
    
    def update_issue(self, 
                     issue_id: str, 
                     summary: Optional[str] = None,
                     description: Optional[str] = None,
                     additional_fields: Optional[Dict[str, Any]] = None) -> Issue:
        """
        Update an existing issue.
        
        Args:
            issue_id: The issue ID or readable ID
            summary: The new issue summary
            description: The new issue description
            additional_fields: Additional fields to update
            
        Returns:
            The updated issue data
        """
        data = {}
        
        if summary is not None:
            data["summary"] = summary
            
        if description is not None:
            data["description"] = description
            
        if additional_fields:
            data.update(additional_fields)
            
        if not data:
            # Nothing to update
            return self.get_issue(issue_id)
            
        response = self.client.post(f"issues/{issue_id}", data=data)
        return Issue.model_validate(response)
    
    def search_issues(self, query: str, limit: int = 10) -> List[Issue]:
        """
        Search for issues using YouTrack query language.
        
        Args:
            query: The search query
            limit: Maximum number of issues to return
            
        Returns:
            List of matching issues
        """
        # Request additional fields to ensure we get summary
        fields = "id,summary,description,created,updated,project,reporter,assignee,customFields"
        params = {"query": query, "$top": limit, "fields": fields}
        response = self.client.get("issues", params=params)
        
        issues = []
        for item in response:
            try:
                issues.append(Issue.model_validate(item))
            except Exception as e:
                # Log the error but continue processing other issues
                import logging
                logging.getLogger(__name__).warning(f"Failed to validate issue: {str(e)}")
        
        return issues
    
    def add_comment(self, issue_id: str, text: str) -> Dict[str, Any]:
        """
        Add a comment to an issue.
        
        Args:
            issue_id: The issue ID or readable ID
            text: The comment text
            
        Returns:
            The created comment data
        """
        data = {"text": text}
        return self.client.post(f"issues/{issue_id}/comments", data=data) 