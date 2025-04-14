"""
YouTrack Projects API client.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from youtrack_mcp.api.client import YouTrackClient


class Project(BaseModel):
    """Model for a YouTrack project."""
    
    id: str
    name: str
    shortName: str
    description: Optional[str] = None
    archived: bool = False
    created: Optional[int] = None
    updated: Optional[int] = None
    lead: Optional[Dict[str, Any]] = None
    custom_fields: List[Dict[str, Any]] = Field(default_factory=list)


class ProjectsClient:
    """Client for interacting with YouTrack Projects API."""
    
    def __init__(self, client: YouTrackClient):
        """
        Initialize the Projects API client.
        
        Args:
            client: The YouTrack API client
        """
        self.client = client
    
    def get_projects(self, include_archived: bool = False) -> List[Project]:
        """
        Get all projects.
        
        Args:
            include_archived: Whether to include archived projects
            
        Returns:
            List of projects
        """
        params = {"fields": "id,name,shortName,description,archived,created,updated,lead(id,name,login)"}
        if not include_archived:
            params["$filter"] = "archived eq false"
            
        response = self.client.get("admin/projects", params=params)
        return [Project.model_validate(project) for project in response]
    
    def get_project(self, project_id: str) -> Project:
        """
        Get a project by ID.
        
        Args:
            project_id: The project ID
            
        Returns:
            The project data
        """
        response = self.client.get(f"admin/projects/{project_id}", params={
            "fields": "id,name,shortName,description,archived,created,updated,lead(id,name,login)"
        })
        return Project.model_validate(response)
    
    def get_project_by_name(self, project_name: str) -> Optional[Project]:
        """
        Get a project by its name or short name.
        
        Args:
            project_name: The project name or short name
            
        Returns:
            The project data or None if not found
        """
        projects = self.get_projects(include_archived=True)
        
        # First try to match by short name (exact match)
        for project in projects:
            if project.shortName.lower() == project_name.lower():
                return project
                
        # Then try to match by full name (case insensitive)
        for project in projects:
            if project.name.lower() == project_name.lower():
                return project
                
        # Finally try to match if project_name is contained in the name
        for project in projects:
            if project_name.lower() in project.name.lower():
                return project
                
        return None
    
    def get_project_issues(self, project_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get issues for a specific project.
        
        Args:
            project_id: The project ID
            limit: Maximum number of issues to return
            
        Returns:
            List of issues in the project
        """
        params = {
            "$filter": f"project/id eq {project_id}",
            "$top": limit
        }
        return self.client.get("issues", params=params)
    
    def create_project(self, 
                      name: str, 
                      short_name: str, 
                      description: Optional[str] = None,
                      lead_id: Optional[str] = None) -> Project:
        """
        Create a new project.
        
        Args:
            name: The project name
            short_name: The project short name (used in issue IDs)
            description: Optional project description
            lead_id: Optional project lead user ID
            
        Returns:
            The created project data
        """
        data = {
            "name": name,
            "shortName": short_name
        }
        
        if description:
            data["description"] = description
            
        if lead_id:
            data["leader"] = {"id": lead_id}
            
        # Debug logging
        print(f"Creating project with data: {data}")
        import logging
        logging.getLogger(__name__).info(f"Creating project with data: {data}")
            
        response = self.client.post("admin/projects", data=data)
        return Project.model_validate(response)
    
    def update_project(self, 
                      project_id: str,
                      name: Optional[str] = None,
                      description: Optional[str] = None,
                      lead_id: Optional[str] = None,
                      archived: Optional[bool] = None) -> Project:
        """
        Update an existing project.
        
        Args:
            project_id: The project ID
            name: The new project name
            description: The new project description
            lead_id: The new project lead user ID
            archived: Whether the project should be archived
            
        Returns:
            The updated project data
        """
        data = {}
        
        if name is not None:
            data["name"] = name
            
        if description is not None:
            data["description"] = description
            
        if lead_id is not None:
            data["leader"] = {"id": lead_id}
            
        if archived is not None:
            data["archived"] = archived
            
        if not data:
            # Nothing to update
            return self.get_project(project_id)
            
        response = self.client.post(f"admin/projects/{project_id}", data=data)
        return Project.model_validate(response)
    
    def delete_project(self, project_id: str) -> None:
        """
        Delete a project.
        
        Args:
            project_id: The project ID
        """
        self.client.delete(f"admin/projects/{project_id}")
        
    def get_custom_fields(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get custom fields for a project.
        
        Args:
            project_id: The project ID
            
        Returns:
            List of custom fields
        """
        return self.client.get(f"admin/projects/{project_id}/customFields")
    
    def add_custom_field(self, 
                        project_id: str, 
                        field_id: str, 
                        empty_field_text: Optional[str] = None) -> Dict[str, Any]:
        """
        Add a custom field to a project.
        
        Args:
            project_id: The project ID
            field_id: The custom field ID
            empty_field_text: Optional text to show for empty fields
            
        Returns:
            The added custom field
        """
        data = {
            "field": {"id": field_id}
        }
        
        if empty_field_text:
            data["emptyFieldText"] = empty_field_text
            
        return self.client.post(f"admin/projects/{project_id}/customFields", data=data) 