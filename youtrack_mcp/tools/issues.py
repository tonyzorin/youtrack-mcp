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
            },
            "link_issues": {
                "description": "Create a link/relationship between two issues in YouTrack.",
                "parameter_descriptions": {
                    "source_issue_id": "The issue ID that will have the link applied to it (e.g., 'PAY-893')",
                    "target_issue_id": "The issue ID to link to (e.g., 'SP-8730')",
                    "link_type": "The type of link relationship (optional, default: 'relates to'). Examples: 'relates to', 'depends on', 'blocks', 'duplicates'"
                }
            },
            "get_issue_links": {
                "description": "Get all existing links/relationships for a specific issue.",
                "parameter_descriptions": {
                    "issue_id": "The issue ID or readable ID (e.g., PROJECT-123)"
                }
            },
            "get_available_link_types": {
                "description": "Get the list of available issue link types that can be used when linking issues.",
                "parameter_descriptions": {}
            },
            "update_issue": {
                "description": "Update issue fields like assignee, priority, state, etc. using YouTrack commands.",
                "parameter_descriptions": {
                    "issue_id": "The issue ID or readable ID (e.g., DSO-45)",
                    "assignee": "Username to assign to (optional, e.g., 'cventers', 'me', or 'Unassigned')",
                    "priority": "Priority level (optional, e.g., 'Critical', 'High', 'Normal', 'Low')",
                    "state": "Issue state (optional, e.g., 'Open', 'In Progress', 'Resolved', 'Closed')",
                    "type": "Issue type (optional, varies by project)"
                }
            },
            "create_dependency": {
                "description": "Create a dependency relationship where one issue depends on another. This is a convenience method for the 'depends on' link type.",
                "parameter_descriptions": {
                    "dependent_issue_id": "The issue that depends on another (e.g., 'DSO-45')",
                    "dependency_issue_id": "The issue that is required/depended upon (e.g., 'PAY-887')"
                }
            },
            "remove_link": {
                "description": "Remove an existing link/relationship between two issues.",
                "parameter_descriptions": {
                    "source_issue_id": "The issue that will have the link removed from it",
                    "target_issue_id": "The issue to unlink from",
                    "link_type": "The type of link to remove (optional, default: 'relates to')"
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
            raw_issue = self.client.get(f"issues/{issue_id}")
            return json.dumps(raw_issue, indent=2)
        except Exception as e:
            logger.exception(f"Error getting raw issue {issue_id}")
            return json.dumps({"error": str(e)})
    
    @sync_wrapper
    def link_issues(self, source_issue_id: str, target_issue_id: str, link_type: str = "relates to") -> str:
        """
        Link two issues together using a specified link type.
        
        FORMAT: link_issues(source_issue_id="PAY-893", target_issue_id="SP-8730", link_type="relates to")
        
        Args:
            source_issue_id: The ID of the issue that will have the link applied to it
            target_issue_id: The ID of the issue to link to  
            link_type: The type of link (optional, default: "relates to")
            
        Returns:
            JSON string with the result of the linking operation
        """
        try:
            result = self.issues_api.link_issues(source_issue_id, target_issue_id, link_type)
            return json.dumps({
                "status": "success",
                "message": f"Successfully linked {source_issue_id} to {target_issue_id} with link type '{link_type}'",
                "result": result
            }, indent=2)
        except Exception as e:
            logger.exception(f"Error linking issues {source_issue_id} -> {target_issue_id}")
            return json.dumps({"error": str(e), "status": "error"})
    
    @sync_wrapper
    def get_issue_links(self, issue_id: str) -> str:
        """
        Get all links for a specific issue.
        
        FORMAT: get_issue_links(issue_id="PAY-893")
        
        Args:
            issue_id: The issue ID or readable ID
            
        Returns:
            JSON string containing all links for the issue
        """
        try:
            links = self.issues_api.get_issue_links(issue_id)
            return json.dumps(links, indent=2)
        except Exception as e:
            logger.exception(f"Error getting links for issue {issue_id}")
            return json.dumps({"error": str(e)})
    
    @sync_wrapper
    def get_available_link_types(self) -> str:
        """
        Get available issue link types from YouTrack.
        
        FORMAT: get_available_link_types()
        
        Returns:
            JSON string containing available link types
        """
        try:
            link_types = self.issues_api.get_available_link_types()
            return json.dumps(link_types, indent=2)
        except Exception as e:
            logger.exception(f"Error getting available link types")
            return json.dumps({"error": str(e)})
    
    @sync_wrapper
    def update_issue(self, issue_id: str, **fields) -> str:
        """
        Update issue fields using YouTrack commands.
        
        FORMAT: update_issue(issue_id="DSO-45", assignee="cventers", priority="Critical")
        
        Args:
            issue_id: The issue ID or readable ID
            **fields: Field updates as keyword arguments
            
        Common field names:
            assignee: Username to assign to (use "cventers", "me", or "Unassigned")
            priority: Priority level (e.g., "Critical", "High", "Normal", "Low")
            state: Issue state (e.g., "Open", "In Progress", "Resolved", "Closed") 
            type: Issue type (varies by project)
            
        Returns:
            JSON string with the result of the update operation
        """
        try:
            result = self.issues_api.update_issue(issue_id, **fields)
            return json.dumps({
                "status": "success",
                "message": f"Successfully updated issue {issue_id}",
                "result": result
            }, indent=2)
        except Exception as e:
            logger.exception(f"Error updating issue {issue_id}")
            return json.dumps({"error": str(e), "status": "error"})
    
    @sync_wrapper
    def create_dependency(self, dependent_issue_id: str, dependency_issue_id: str) -> str:
        """
        Create a dependency relationship where one issue depends on another.
        
        FORMAT: create_dependency(dependent_issue_id="DSO-45", dependency_issue_id="PAY-887")
        
        Args:
            dependent_issue_id: The issue that depends on another (e.g., "DSO-45") 
            dependency_issue_id: The issue that is required (e.g., "PAY-887")
            
        Returns:
            JSON string with the result of creating the dependency
        """
        try:
            result = self.issues_api.create_dependency(dependent_issue_id, dependency_issue_id)
            return json.dumps({
                "status": "success",
                "message": f"Successfully created dependency: {dependent_issue_id} depends on {dependency_issue_id}",
                "result": result
            }, indent=2)
        except Exception as e:
            logger.exception(f"Error creating dependency {dependent_issue_id} -> {dependency_issue_id}")
            return json.dumps({"error": str(e), "status": "error"})
    
    @sync_wrapper
    def remove_link(self, source_issue_id: str, target_issue_id: str, link_type: str = "relates to") -> str:
        """
        Remove a link between two issues.
        
        FORMAT: remove_link(source_issue_id="DSO-45", target_issue_id="PAY-887", link_type="relates to")
        
        Args:
            source_issue_id: The issue that will have the link removed from it
            target_issue_id: The issue to unlink from
            link_type: The type of link to remove (optional, default: "relates to")
            
        Returns:
            JSON string with the result of removing the link
        """
        try:
            result = self.issues_api.remove_link(source_issue_id, target_issue_id, link_type)
            return json.dumps({
                "status": "success",
                "message": f"Successfully removed {link_type} link from {source_issue_id} to {target_issue_id}",
                "result": result
            }, indent=2)
        except Exception as e:
            logger.exception(f"Error removing link {source_issue_id} -> {target_issue_id}")
            return json.dumps({"error": str(e), "status": "error"}) 