"""
YouTrack Projects API client.
"""

from typing import Any, Dict, List, Optional
import json

from pydantic import BaseModel, Field

from youtrack_mcp.api.client import YouTrackClient
import logging


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
        params = {
            "fields": "id,name,shortName,description,archived,created,updated,lead(id,name,login)"
        }
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
        response = self.client.get(
            f"admin/projects/{project_id}",
            params={
                "fields": "id,name,shortName,description,archived,created,updated,lead(id,name,login)"
            },
        )
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

    def get_project_issues(
        self, project_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get issues for a specific project.

        Args:
            project_id: The project ID
            limit: Maximum number of issues to return

        Returns:
            List of issues in the project
        """
        logger = logging.getLogger(__name__)
        logger.info(f"Getting issues for project {project_id}, limit {limit}")

        # Request more fields to get complete issue information
        fields = "id,summary,description,created,updated,reporter(id,login,name),assignee(id,login,name),project(id,name,shortName),customFields(id,name,value($type,name,text,id),projectCustomField(field(name)))"

        params = {
            "$filter": f"project/id eq {project_id}",
            "$top": limit,
            "fields": fields,
        }

        try:
            issues = self.client.get("issues", params=params)
            logger.info(
                f"Retrieved {len(issues) if isinstance(issues, list) else 0} issues"
            )
            return issues
        except Exception as e:
            logger.error(
                f"Error getting issues for project {project_id}: {str(e)}"
            )
            # Return empty list on error
            return []

    def create_project(
        self,
        name: str,
        short_name: str,
        description: Optional[str] = None,
        lead_id: Optional[str] = None,
    ) -> Project:
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
        if not name:
            raise ValueError("Project name is required")
        if not short_name:
            raise ValueError("Project short name is required")

        data = {"name": name, "shortName": short_name}

        if description:
            data["description"] = description

        if lead_id:
            # The YouTrack API expects "leader", not "lead_id"
            data["leader"] = {"id": lead_id}

        # Debug logging
        logger = logging.getLogger(__name__)
        logger.info(f"Creating project with data: {json.dumps(data)}")
        logger.info(
            f"Base URL: {self.client.base_url}, API endpoint: admin/projects"
        )

        try:
            response = self.client.post("admin/projects", data=data)
            logger.info(f"Create project response: {json.dumps(response)}")

            # The response might not include all required fields,
            # Try to get the complete project now
            if isinstance(response, dict) and "id" in response:
                try:
                    # Get the full project details
                    created_project = self.get_project(response["id"])
                    logger.info(
                        f"Successfully retrieved full project details: {created_project.name}"
                    )
                    return created_project
                except Exception as e:
                    logger.warning(
                        f"Could not retrieve full project details: {str(e)}"
                    )
                    # Fall back to creating a model with the available data
                    # We need to ensure shortName is present
                    if "shortName" not in response and short_name:
                        response["shortName"] = short_name
                    if "name" not in response and name:
                        response["name"] = name

            # Try to validate the model, which might fail if fields are missing
            try:
                return Project.model_validate(response)
            except Exception as e:
                logger.warning(f"Could not validate project model: {str(e)}")
                # As a last resort, create a minimal valid project
                minimal_project = {
                    "id": response.get("id", "unknown"),
                    "name": name,
                    "shortName": short_name,
                    "description": description,
                }
                return Project.model_validate(minimal_project)
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            raise

    def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        lead_id: Optional[str] = None,
        archived: Optional[bool] = None,
    ) -> Project:
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
        # First get the existing project data
        logger = logging.getLogger(__name__)
        logger.info(f"Getting existing project data for {project_id}")

        try:
            # Prepare data for update API call
            data = {}

            # Include any provided parameters
            if name is not None:
                data["name"] = name
            if description is not None:
                data["description"] = description
            if lead_id is not None:
                data["leader"] = {"id": lead_id}
            if archived is not None:
                data["archived"] = archived

            # Make sure we have at least one parameter to update
            if not data:
                logger.info(
                    "No parameters to update, returning current project data"
                )
                return self.get_project(project_id)

            logger.info(f"Updating project with data: {data}")
            response = self.client.post(
                f"admin/projects/{project_id}", data=data
            )
            logger.info(f"Update project response: {response}")

            # The API response might not contain all required fields,
            # so we need to get the full project data after the update
            try:
                # Get the updated project data
                updated_project = self.get_project(project_id)
                logger.info(
                    f"Successfully retrieved updated project: {updated_project.name}"
                )
                return updated_project
            except Exception as e:
                logger.error(f"Error getting updated project: {str(e)}")
                # If we can't get the updated project, create a partial project with the data we have
                if isinstance(response, dict) and "id" in response:
                    logger.info(
                        f"Creating partial project from response: {response}"
                    )
                    # Try to get the original project to fill in missing fields
                    try:
                        original_project = self.get_project(project_id)
                        # Update with new values
                        for key, value in data.items():
                            if key == "leader":
                                setattr(original_project, "lead", value)
                            else:
                                setattr(original_project, key, value)
                        return original_project
                    except Exception:
                        # If we can't get the original project either, just return the response
                        logger.warning(
                            f"Unable to get original project, returning response: {response}"
                        )
                        return response
                else:
                    # If the response doesn't have an ID, just return it
                    return response
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {str(e)}")
            raise

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

    def add_custom_field(
        self,
        project_id: str,
        field_id: str,
        empty_field_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a custom field to a project.

        Args:
            project_id: The project ID
            field_id: The custom field ID
            empty_field_text: Optional text to show for empty fields

        Returns:
            The added custom field
        """
        data = {"field": {"id": field_id}}

        if empty_field_text:
            data["emptyFieldText"] = empty_field_text

        return self.client.post(
            f"admin/projects/{project_id}/customFields", data=data
        )
