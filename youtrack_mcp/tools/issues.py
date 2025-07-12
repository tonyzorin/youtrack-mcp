"""
YouTrack Issue MCP tools.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.issues import IssuesClient
from youtrack_mcp.api.projects import ProjectsClient
from youtrack_mcp.mcp_wrappers import sync_wrapper

logger = logging.getLogger(__name__)


class IssueTools:
    """Issue-related MCP tools."""
    
    def __init__(self):
        """Initialize the issue tools."""
        self.client = YouTrackClient()
        self.issues_api = IssuesClient(self.client)
    
    @sync_wrapper    
    def get_issue(self, issue_id: str) -> str:
        """
        Get information about a specific issue.
        
        FORMAT: get_issue(issue_id="DEMO-123") - You must use the exact parameter name 'issue_id'.
        
        Args:
            issue_id: The issue ID or readable ID (e.g., PROJECT-123)
            
        Returns:
            JSON string with issue information
        """
        try:
            # First try to get the issue data with explicit fields
            fields = "id,idReadable,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value)"
            raw_issue = self.client.get(f"issues/{issue_id}?fields={fields}")
            
            # If we got a minimal response, enhance it with default values
            if isinstance(raw_issue, dict) and raw_issue.get('$type') == 'Issue' and 'summary' not in raw_issue:
                raw_issue['summary'] = f"Issue {issue_id}"  # Provide a default summary
            
            # Return the raw issue data directly - avoid model validation issues
            return json.dumps(raw_issue, indent=2)
            
        except Exception as e:
            logger.exception(f"Error getting issue {issue_id}")
            return json.dumps({"error": str(e)})
    
    @sync_wrapper    
    def search_issues(self, query: str, limit: int = 10) -> str:
        """
        Search for issues using YouTrack query language.
        
        FORMAT: search_issues(query="project: DEMO #Unresolved", limit=10)
        
        Args:
            query: The search query
            limit: Maximum number of issues to return
            
        Returns:
            JSON string with matching issues
        """
        try:
            # Request with explicit fields to get complete data
            fields = "id,idReadable,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value)"
            params = {"query": query, "$top": limit, "fields": fields}
            raw_issues = self.client.get("issues", params=params)
            
            # Return the raw issues data directly
            return json.dumps(raw_issues, indent=2)
            
        except Exception as e:
            logger.exception(f"Error searching issues with query: {query}")
            return json.dumps({"error": str(e)})
    
    @sync_wrapper
    def create_issue(self, project: str, summary: str, description: Optional[str] = None) -> str:
        """
        Create a new issue in YouTrack.
        
        FORMAT: create_issue(project="DEMO", summary="Bug: Login not working", description="Details here")
        
        Args:
            project: The ID or short name of the project
            summary: The issue summary
            description: The issue description (optional)
            
        Returns:
            JSON string with the created issue information
        """
        try:
            # Check if we got proper parameters
            logger.debug(f"Creating issue with: project={project}, summary={summary}, description={description}")
            
            # Handle kwargs format from MCP
            if isinstance(project, dict) and 'project' in project and 'summary' in project:
                # Extract from dict if we got project as a JSON object
                logger.info("Detected project as a dictionary, extracting parameters")
                description = project.get('description', None)
                summary = project.get('summary')
                project = project.get('project')
                
            # Ensure we have valid data
            if not project:
                return json.dumps({"error": "Project is required", "status": "error"})
            if not summary:
                return json.dumps({"error": "Summary is required", "status": "error"})
            
            # Check if project is a project ID or short name
            project_id = project
            if project and not project.startswith("0-"):
                # Try to get the project ID from the short name (e.g., "DEMO")
                try:
                    logger.info(f"Looking up project ID for: {project}")
                    projects_api = ProjectsClient(self.client)
                    project_obj = projects_api.get_project_by_name(project)
                    if project_obj:
                        logger.info(f"Found project {project_obj.name} with ID {project_obj.id}")
                        project_id = project_obj.id
                    else:
                        logger.warning(f"Project not found: {project}")
                        return json.dumps({"error": f"Project not found: {project}", "status": "error"})
                except Exception as e:
                    logger.warning(f"Error finding project: {str(e)}")
                    return json.dumps({"error": f"Error finding project: {str(e)}", "status": "error"})
            
            logger.info(f"Creating issue in project {project_id}: {summary}")
            
            # Call the API client to create the issue
            try:
                issue = self.issues_api.create_issue(project_id, summary, description)
                
                # Check if we got an issue with an ID
                if isinstance(issue, dict) and issue.get('error'):
                    # Handle error returned as a dict
                    return json.dumps(issue)
                
                # Try to get full issue details right after creation
                if hasattr(issue, 'id'):
                    try:
                        # Get the full issue details using issue ID
                        issue_id = issue.id
                        detailed_issue = self.issues_api.get_issue(issue_id)
                        
                        if hasattr(detailed_issue, 'model_dump'):
                            return json.dumps(detailed_issue.model_dump(), indent=2)
                        else:
                            return json.dumps(detailed_issue, indent=2)
                    except Exception as e:
                        logger.warning(f"Could not retrieve detailed issue: {str(e)}")
                        # Fall back to original issue
                
                # Original issue as fallback
                if hasattr(issue, 'model_dump'):
                    return json.dumps(issue.model_dump(), indent=2)
                else:
                    return json.dumps(issue, indent=2)
            except Exception as e:
                error_msg = str(e)
                if hasattr(e, 'response') and e.response:
                    try:
                        # Try to get detailed error message from response
                        error_content = e.response.content.decode('utf-8', errors='replace')
                        error_msg = f"{error_msg} - {error_content}"
                    except:
                        pass
                logger.error(f"API error creating issue: {error_msg}")
                return json.dumps({"error": error_msg, "status": "error"})
                
        except Exception as e:
            logger.exception(f"Error creating issue in project {project}")
            return json.dumps({"error": str(e), "status": "error"})
    
    @sync_wrapper        
    def add_comment(self, issue_id: str, text: str) -> str:
        """
        Add a comment to an issue.
        
        FORMAT: add_comment(issue_id="DEMO-123", text="This is my comment")
        
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
                "description": "Get information about a specific issue in YouTrack. Returns detailed information including custom fields.",
                "parameter_descriptions": {
                    "issue_id": "The issue ID or readable ID (e.g., PROJECT-123)"
                }
            },
            "search_issues": {
                "description": "Search for issues using YouTrack query language. Supports all YouTrack search syntax.",
                "parameter_descriptions": {
                    "query": "The search query (e.g., 'project: DEMO #Unresolved')",
                    "limit": "Maximum number of issues to return (optional, default: 10)"
                }
            },
            "create_issue": {
                "description": "Create a new issue in YouTrack with the specified details.",
                "parameter_descriptions": {
                    "project": "The project ID or short name (e.g., 'DEMO' or '0-0')",
                    "summary": "The issue title/summary",
                    "description": "Detailed description of the issue (optional)"
                }
            },
            "add_comment": {
                "description": "Add a comment to an existing issue in YouTrack.",
                "parameter_descriptions": {
                    "issue_id": "The issue ID or readable ID (e.g., PROJECT-123)",
                    "text": "The comment text to add to the issue"
                }
            },
            "get_issue_raw": {
                "description": "Get raw information about a specific issue, bypassing the Pydantic model.",
                "parameter_descriptions": {
                    "issue_id": "The issue ID or readable ID (e.g., PROJECT-123)"
                }
            }
        }
    
    @sync_wrapper
    def get_issue_raw(self, issue_id: str) -> str:
        """
        Get raw information about a specific issue, bypassing the Pydantic model.
        
        FORMAT: get_issue_raw(issue_id="DEMO-123")
        
        Args:
            issue_id: The issue ID or readable ID
            
        Returns:
            Raw JSON string with the issue data
        """
        try:
            fields = "id,idReadable,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value)"
            raw_issue = self.client.get(f"issues/{issue_id}?fields={fields}")
            return json.dumps(raw_issue, indent=2)
        except Exception as e:
            logger.exception(f"Error getting raw issue {issue_id}")
            return json.dumps({"error": str(e)}) 