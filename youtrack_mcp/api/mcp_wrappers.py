"""
MCP wrapper functions for YouTrack API.

These functions provide a clean interface for MCP tools to interact with the YouTrack API.
All functions are designed to handle parameters in the format expected by MCP.
"""
import json
import logging
from typing import Dict, Any, Optional, List, Union
import asyncio
import nest_asyncio

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.issues import IssuesClient
from youtrack_mcp.api.projects import ProjectsClient
from youtrack_mcp.api.users import UsersClient

try:
    nest_asyncio.apply()  # Allow nested event loops
except RuntimeError:
    pass  # If already applied, ignore the error

logger = logging.getLogger(__name__)

# Initialize API clients with error handling
try:
    client = YouTrackClient()
    issues_api = IssuesClient(client)
    projects_api = ProjectsClient(client)
    users_api = UsersClient(client)
except Exception as e:
    logger.error(f"Error initializing YouTrack API clients: {str(e)}")
    # Create placeholder clients that will report the error when used
    client = None
    issues_api = None
    projects_api = None
    users_api = None

# ================================================
# Issue-related MCP wrappers
# ================================================

def get_issue(issue_id: str) -> Dict[str, Any]:
    """
    Get information about a specific issue.
    
    Args:
        issue_id: The issue ID or readable ID (e.g., PROJECT-123)
        
    Returns:
        Dictionary with issue information
        
    Example:
        >>> get_issue(issue_id="DEMO-123")
    """
    logger.info(f"MCP wrapper: get_issue({issue_id})")
    
    # Check if API client is available
    if issues_api is None:
        return {"error": "YouTrack API client failed to initialize", "status": "error"}
    
    try:
        issue = issues_api.get_issue(issue_id)
        return issue.model_dump() if hasattr(issue, 'model_dump') else issue
    except Exception as e:
        logger.exception(f"Error getting issue {issue_id}")
        return {"error": str(e), "status": "error"}

def get_issue_comments(issue_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get comments for a specific issue.
    
    Args:
        issue_id: The issue ID or readable ID (e.g., PROJECT-123)
        limit: Maximum number of comments to return (default: 10)
        
    Returns:
        List of comments for the issue
        
    Example:
        >>> get_issue_comments(issue_id="DEMO-123", limit=5)
    """
    logger.info(f"MCP wrapper: get_issue_comments({issue_id}, limit={limit})")
    
    # Check if API client is available
    if issues_api is None:
        return [{"error": "YouTrack API client failed to initialize", "status": "error"}]
        
    try:
        comments = issues_api.get_issue_comments(issue_id, limit)
        return comments if isinstance(comments, list) else []
    except Exception as e:
        logger.exception(f"Error getting comments for issue {issue_id}")
        return [{"error": str(e), "status": "error"}]

def add_comment(issue_id: str, text: str) -> Dict[str, Any]:
    """
    Add a comment to an issue.
    
    Args:
        issue_id: The issue ID or readable ID (e.g., PROJECT-123)
        text: The comment text (supports markdown)
        
    Returns:
        Dictionary with the result
        
    Example:
        >>> add_comment(issue_id="DEMO-123", text="Fixed in the latest release")
    """
    logger.info(f"MCP wrapper: add_comment({issue_id}, {text[:20]}...)")
    
    # Check if API client is available
    if issues_api is None:
        return {"error": "YouTrack API client failed to initialize", "status": "error"}
        
    try:
        result = issues_api.add_comment(issue_id, text)
        return result if isinstance(result, dict) else {"status": "success"}
    except Exception as e:
        logger.exception(f"Error adding comment to issue {issue_id}")
        return {"error": str(e), "status": "error"}

def create_issue(project: str, summary: str, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new issue in a project.
    
    Args:
        project: The project ID or short name (e.g., "DEMO")
        summary: The issue summary
        description: The issue description (optional)
        
    Returns:
        Dictionary with the created issue information
        
    Example:
        >>> create_issue(project="DEMO", summary="Login button not working", description="Users cannot log in after the latest update")
    """
    logger.info(f"MCP wrapper: create_issue({project}, {summary}, {description and description[:20]}...)")
    
    # Check if API clients are available
    if issues_api is None or projects_api is None:
        return {"error": "YouTrack API client failed to initialize", "status": "error"}
        
    try:
        # Check if project is a project ID or short name
        if project and not project.startswith("0-"):
            # Try to get the project ID from the short name (e.g., "DEMO")
            try:
                project_obj = projects_api.get_project_by_name(project)
                if project_obj:
                    logger.info(f"Found project {project_obj.name} with ID {project_obj.id}")
                    project = project_obj.id
                else:
                    logger.warning(f"Project not found: {project}")
            except Exception as e:
                logger.warning(f"Error finding project: {str(e)}")
        
        # Ensure we have valid data
        if not project:
            return {"error": "Project is required", "status": "error"}
        if not summary:
            return {"error": "Summary is required", "status": "error"}
        
        # Create the issue
        issue = issues_api.create_issue(project, summary, description)
        return issue.model_dump() if hasattr(issue, 'model_dump') else issue
    except Exception as e:
        logger.exception(f"Error creating issue in project {project}")
        return {"error": str(e), "status": "error"}

def search_issues(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for issues using YouTrack query language.
    
    Args:
        query: The search query (e.g., "project: DEMO #Unresolved")
        limit: Maximum number of issues to return (default: 10)
        
    Returns:
        List of matching issues
        
    Example:
        >>> search_issues(query="project: DEMO #Unresolved", limit=5)
    """
    logger.info(f"MCP wrapper: search_issues({query}, limit={limit})")
    
    # Check if API client is available
    if issues_api is None:
        return [{"error": "YouTrack API client failed to initialize", "status": "error"}]
        
    try:
        issues = issues_api.search_issues(query, limit)
        # Convert to list of dictionaries
        if isinstance(issues, list):
            return [issue.model_dump() if hasattr(issue, 'model_dump') else issue for issue in issues]
        return []
    except Exception as e:
        logger.exception(f"Error searching for issues with query: {query}")
        return [{"error": str(e), "status": "error"}]

# ================================================
# Project-related MCP wrappers
# ================================================

def get_projects(include_archived: bool = False) -> List[Dict[str, Any]]:
    """
    Get a list of all projects.
    
    Args:
        include_archived: Whether to include archived projects (default: False)
        
    Returns:
        List of projects
        
    Example:
        >>> get_projects(include_archived=True)
    """
    logger.info(f"MCP wrapper: get_projects(include_archived={include_archived})")
    
    # Check if API client is available
    if projects_api is None:
        return [{"error": "YouTrack API client failed to initialize", "status": "error"}]
        
    try:
        projects = projects_api.get_projects(include_archived)
        # Convert to list of dictionaries
        if isinstance(projects, list):
            return [project.model_dump() if hasattr(project, 'model_dump') else project for project in projects]
        return []
    except Exception as e:
        logger.exception("Error getting projects")
        return [{"error": str(e), "status": "error"}]

def get_project(project_id: str) -> Dict[str, Any]:
    """
    Get information about a specific project.
    
    Args:
        project_id: The project ID or short name
        
    Returns:
        Dictionary with project information
        
    Example:
        >>> get_project(project_id="DEMO")
    """
    logger.info(f"MCP wrapper: get_project({project_id})")
    
    # Check if API client is available
    if projects_api is None:
        return {"error": "YouTrack API client failed to initialize", "status": "error"}
        
    try:
        project = projects_api.get_project(project_id)
        return project.model_dump() if hasattr(project, 'model_dump') else project
    except Exception as e:
        logger.exception(f"Error getting project {project_id}")
        return {"error": str(e), "status": "error"}

# ================================================
# User-related MCP wrappers
# ================================================

def get_current_user() -> Dict[str, Any]:
    """
    Get information about the currently authenticated user.
    
    Returns:
        Dictionary with user information
        
    Example:
        >>> get_current_user()
    """
    logger.info("MCP wrapper: get_current_user()")
    
    # Check if API client is available
    if users_api is None:
        return {"error": "YouTrack API client failed to initialize", "status": "error"}
        
    try:
        user = users_api.get_current_user()
        return user.model_dump() if hasattr(user, 'model_dump') else user
    except Exception as e:
        logger.exception("Error getting current user")
        return {"error": str(e), "status": "error"} 