"""
YouTrack Project MCP tools.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.projects import ProjectsClient

logger = logging.getLogger(__name__)


class ProjectTools:
    """Project-related MCP tools."""
    
    def __init__(self):
        """Initialize the project tools."""
        self.client = YouTrackClient()
        self.projects_api = ProjectsClient(self.client)
        
    def get_projects(self, include_archived: bool = False) -> str:
        """
        Get a list of all projects.
        
        Args:
            include_archived: Whether to include archived projects
            
        Returns:
            JSON string with projects information
        """
        try:
            projects = self.projects_api.get_projects(include_archived)
            return json.dumps([project.model_dump() for project in projects], indent=2)
        except Exception as e:
            logger.exception("Error getting projects")
            return json.dumps({"error": str(e)})
    
    def get_project(self, project_id: str) -> str:
        """
        Get information about a specific project.
        
        Args:
            project_id: The project ID
            
        Returns:
            JSON string with project information
        """
        try:
            project = self.projects_api.get_project(project_id)
            return json.dumps(project.model_dump(), indent=2)
        except Exception as e:
            logger.exception(f"Error getting project {project_id}")
            return json.dumps({"error": str(e)})
    
    def get_project_by_name(self, project_name: str) -> str:
        """
        Find a project by its name.
        
        Args:
            project_name: The project name or short name
            
        Returns:
            JSON string with project information or error if not found
        """
        try:
            project = self.projects_api.get_project_by_name(project_name)
            if project:
                return json.dumps(project.model_dump(), indent=2)
            else:
                return json.dumps({"error": f"Project '{project_name}' not found"})
        except Exception as e:
            logger.exception(f"Error finding project '{project_name}'")
            return json.dumps({"error": str(e)})
    
    def get_project_issues(self, project_id: str, limit: int = 10) -> str:
        """
        Get issues for a specific project.
        
        Args:
            project_id: The project ID
            limit: Maximum number of issues to return
            
        Returns:
            JSON string with project issues
        """
        try:
            issues = self.projects_api.get_project_issues(project_id, limit)
            return json.dumps(issues, indent=2)
        except Exception as e:
            logger.exception(f"Error getting issues for project {project_id}")
            return json.dumps({"error": str(e)})
    
    def create_project(self, name: str, short_name: str, 
                     lead_id: str,
                     description: Optional[str] = None) -> str:
        """
        Create a new project with a required leader.
        
        Args:
            name: The project name
            short_name: The project short name (used in issue IDs)
            lead_id: ID of the user who will be the project leader (required)
            description: Optional project description
            
        Returns:
            JSON string with the created project information
        """
        try:
            # Directly create the project with the required leader
            data = {
                "name": name,
                "shortName": short_name,
                "leader": {"id": lead_id}
            }
            
            if description:
                data["description"] = description
            
            # Log the data being sent
            logger.info(f"Creating project with leader data: {data}")
            
            # Make direct API call
            response = self.client.post("admin/projects", data=data)
            return json.dumps(response, indent=2)
        except Exception as e:
            logger.exception(f"Error creating project {name}")
            return json.dumps({"error": str(e)})
    
    def update_project(self, project_id: str, name: Optional[str] = None, 
                      description: Optional[str] = None, 
                      archived: Optional[bool] = None,
                      lead_id: Optional[str] = None) -> str:
        """
        Update an existing project.
        
        Args:
            project_id: The project ID
            name: The new project name
            description: The new project description
            archived: Whether the project should be archived
            lead_id: ID of the user who will be the project leader
            
        Returns:
            JSON string with the updated project information
        """
        try:
            project = self.projects_api.update_project(
                project_id=project_id,
                name=name,
                description=description,
                archived=archived,
                lead_id=lead_id
            )
            return json.dumps(project.model_dump(), indent=2)
        except Exception as e:
            logger.exception(f"Error updating project {project_id}")
            return json.dumps({"error": str(e)})
    
    def get_custom_fields(self, project_id: str) -> str:
        """
        Get custom fields for a project.
        
        Args:
            project_id: The project ID
            
        Returns:
            JSON string with custom fields
        """
        try:
            custom_fields = self.projects_api.get_custom_fields(project_id)
            return json.dumps(custom_fields, indent=2)
        except Exception as e:
            logger.exception(f"Error getting custom fields for project {project_id}")
            return json.dumps({"error": str(e)})
    
    def close(self) -> None:
        """Close the API client."""
        self.client.close()
    
    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the definitions of all project tools.
        
        Returns:
            Dictionary mapping tool names to their configuration
        """
        return {
            "get_projects": {
                "function": self.get_projects,
                "description": "Get a list of all YouTrack projects",
                "parameter_descriptions": {
                    "include_archived": "Whether to include archived projects (default: false)"
                }
            },
            "get_project": {
                "function": self.get_project,
                "description": "Get information about a specific YouTrack project by its ID",
                "parameter_descriptions": {
                    "project_id": "The project ID"
                }
            },
            "get_project_by_name": {
                "function": self.get_project_by_name,
                "description": "Find a YouTrack project by its name or short name",
                "parameter_descriptions": {
                    "project_name": "The project name or short name to search for"
                }
            },
            "get_project_issues": {
                "function": self.get_project_issues,
                "description": "Get issues for a specific YouTrack project",
                "parameter_descriptions": {
                    "project_id": "The project ID",
                    "limit": "Maximum number of issues to return (default: 10)"
                }
            },
            "create_project": {
                "function": self.create_project,
                "description": "Create a new YouTrack project",
                "parameter_descriptions": {
                    "name": "The project name",
                    "short_name": "The project short name (used in issue IDs)",
                    "lead_id": "ID of the user who will be the project leader (required)",
                    "description": "Optional project description"
                }
            },
            "update_project": {
                "function": self.update_project,
                "description": "Update an existing YouTrack project",
                "parameter_descriptions": {
                    "project_id": "The project ID",
                    "name": "The new project name (optional)",
                    "description": "The new project description (optional)",
                    "archived": "Whether the project should be archived (optional)",
                    "lead_id": "ID of the user who will be the project leader (optional)"
                }
            },
            "get_custom_fields": {
                "function": self.get_custom_fields,
                "description": "Get custom fields for a YouTrack project",
                "parameter_descriptions": {
                    "project_id": "The project ID"
                }
            }
        } 