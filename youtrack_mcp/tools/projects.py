"""
YouTrack Project MCP tools.
"""

import json
import logging
from typing import Any, Dict, Optional

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.issues import IssuesClient
from youtrack_mcp.api.projects import ProjectsClient
from youtrack_mcp.mcp_wrappers import sync_wrapper
from youtrack_mcp.utils import format_json_response

logger = logging.getLogger(__name__)


class ProjectTools:
    """Project-related MCP tools."""

    def __init__(self):
        """Initialize the project tools."""
        self.client = YouTrackClient()
        self.projects_api = ProjectsClient(self.client)

        # Also initialize the issues API for fetching issue details
        self.issues_api = IssuesClient(self.client)

    @sync_wrapper
    def get_projects(self, include_archived: bool = False) -> str:
        """
        Get a list of all projects.

        Args:
            include_archived: Whether to include archived projects (default: False)

        Returns:
            JSON string with projects information
        """
        try:
            projects = self.projects_api.get_projects(
                include_archived=include_archived
            )

            # Handle both Pydantic models and dictionaries in the response
            result = []
            for project in projects:
                if hasattr(project, "model_dump"):
                    result.append(project.model_dump())
                else:
                    result.append(project)  # Assume it's already a dict

            return format_json_response(result)
        except Exception as e:
            logger.exception("Error getting projects")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def get_project(self, project_id: str) -> str:
        """
        Get information about a specific project.

        Args:
            project_id: The project identifier (e.g., "DEMO", "0-0")

        Returns:
            JSON string with project information
        """
        try:
            if not project_id:
                return format_json_response(
                    {"error": "Project ID is required"}
                )

            project_obj = self.projects_api.get_project(project_id)

            # Handle both Pydantic models and dictionaries in the response
            if hasattr(project_obj, "model_dump"):
                result = project_obj.model_dump()
            else:
                result = project_obj  # Assume it's already a dict

            return format_json_response(result)
        except Exception as e:
            logger.exception(f"Error getting project {project_id}")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def get_project_by_name(self, project_name: str) -> str:
        """
        Find a project by its name.

        Args:
            project_name: The project name or short name

        Returns:
            JSON string with project information
        """
        try:
            project = self.projects_api.get_project_by_name(project_name)
            if project:
                # Handle both Pydantic models and dictionaries in the response
                if hasattr(project, "model_dump"):
                    result = project.model_dump()
                else:
                    result = project  # Assume it's already a dict

                return format_json_response(result)
            else:
                return format_json_response(
                    {"error": f"Project '{project_name}' not found"}
                )
        except Exception as e:
            logger.exception(f"Error finding project by name {project_name}")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def get_project_issues(self, project_id: str, limit: int = 50) -> str:
        """
        Get issues for a specific project.

        FORMAT: get_project_issues(project_id="DEMO", limit=50)

        Args:
            project_id: The project identifier (e.g., "DEMO", "0-0")
            limit: Maximum number of issues to return (default: 50)

        Returns:
            JSON string with the issues
        """
        try:
            if not project_id:
                return format_json_response(
                    {"error": "Project ID is required"}
                )

            # First try with the direct project ID
            try:
                issues = self.projects_api.get_project_issues(
                    project_id, limit
                )
                if issues:
                    return format_json_response(issues)
            except Exception as e:
                # If that fails, check if it was a non-ID format error
                if not str(e).startswith("Project not found"):
                    logger.exception(
                        f"Error getting issues for project {project_id}"
                    )
                    return format_json_response({"error": str(e)})

            # If that failed, try to find project by name
            try:
                project_obj = self.projects_api.get_project_by_name(project_id)
                if project_obj:
                    issues = self.projects_api.get_project_issues(
                        project_obj.id, limit
                    )
                    return format_json_response(issues)
                else:
                    return format_json_response(
                        {"error": f"Project not found: {project_id}"}
                    )
            except Exception as e:
                logger.exception(
                    f"Error getting issues for project {project_id}"
                )
                return format_json_response({"error": str(e)})
        except Exception as e:
            logger.exception(
                f"Error processing get_project_issues({project_id}, {limit})"
            )
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def get_custom_fields(self, project_id: str) -> str:
        """
        Get custom fields for a project.

        FORMAT: get_custom_fields(project_id="DEMO")

        Args:
            project_id: The project identifier (e.g., "DEMO", "0-0")

        Returns:
            JSON string with custom fields information
        """
        try:
            if not project_id:
                return format_json_response(
                    {"error": "Project ID is required"}
                )

            fields = self.projects_api.get_custom_fields(project_id)

            # Handle various response formats safely
            if fields is None:
                return format_json_response([])

            # If it's a dictionary (direct API response)
            if isinstance(fields, dict):
                return format_json_response(fields)

            # If it's a list of objects
            try:
                result = []
                # Try to iterate, but handle errors safely
                for field in fields:
                    if hasattr(field, "model_dump"):
                        result.append(field.model_dump())
                    elif isinstance(field, dict):
                        result.append(field)
                else:
                    # Last resort: convert to string
                    result.append(str(field))
                return format_json_response(result)
            except Exception as e:
                # If we can't iterate, return the raw string representation
                logger.warning(
                    f"Could not process custom fields response: {str(e)}"
                )
                return format_json_response({"custom_fields": str(fields)})
        except Exception as e:
            logger.exception(
                f"Error getting custom fields for project {project_id}"
            )
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def create_project(
        self,
        name: str,
        short_name: str,
        lead_id: str,
        description: Optional[str] = None,
    ) -> str:
        """
        Create a new project with a required leader.

        FORMAT: create_project(name="Demo Project", short_name="DEMO", lead_id="admin", description="A demo project")

        Args:
            name: The name of the project
            short_name: The short name of the project (used as prefix for issues)
            lead_id: The ID of the user who will be the project leader
            description: The project description (optional)

        Returns:
            JSON string with the created project information
        """
        try:
            # Check for missing required parameters
            if not name:
                return format_json_response(
                    {"error": "Project name is required"}
                )
            if not short_name:
                return format_json_response(
                    {"error": "Project short name is required"}
                )
            if not lead_id:
                return format_json_response(
                    {"error": "Project leader ID is required"}
                )

            project = self.projects_api.create_project(
                name=name,
                short_name=short_name,
                lead_id=lead_id,
                description=description,
            )

            # Handle both Pydantic models and dictionaries in the response
            if hasattr(project, "model_dump"):
                result = project.model_dump()
            else:
                result = project  # Assume it's already a dict

            return format_json_response(result)
        except Exception as e:
            logger.exception(f"Error creating project {name}")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        archived: Optional[bool] = None,
        lead_id: Optional[str] = None,
        short_name: Optional[str] = None,
    ) -> str:
        """
        Update an existing project.

        FORMAT: update_project(project_id="DEMO", name="New Name", description="New Description", archived=False, lead_id="admin", short_name="NEWKEY")

        Args:
            project_id: The project identifier (e.g., "DEMO", "0-0")
            name: The new name for the project (optional)
            description: The new project description (optional)
            archived: Whether the project should be archived (optional)
            lead_id: The ID of the new project leader (optional)
            short_name: The new short name for the project (optional) - used as prefix for issue IDs

        Returns:
            JSON string with the updated project information
        """
        try:
            if not project_id:
                return format_json_response(
                    {"error": "Project ID is required"}
                )

            # First, get the existing project to maintain required fields
            try:
                existing_project = self.projects_api.get_project(project_id)
                logger.info(
                    f"Found existing project: {existing_project.name} ({existing_project.id})"
                )

                # Prepare data for direct API call
                data = {}

                # Only include parameters that were explicitly provided
                if name is not None:
                    data["name"] = name
                if description is not None:
                    data["description"] = description
                if archived is not None:
                    data["archived"] = archived
                if lead_id is not None:
                    data["leader"] = {"id": lead_id}
                if short_name is not None:
                    data["shortName"] = short_name

                # If no parameters were provided, return current project
                if not data:
                    logger.info(
                        "No parameters to update, returning current project"
                    )
                    if hasattr(existing_project, "model_dump"):
                        return format_json_response(
                            existing_project.model_dump()
                        )
                    else:
                        return format_json_response(existing_project)

                # Log the data being sent
                logger.info(f"Updating project with data: {data}")

                # Make direct API call
                try:
                    # Use the client directly instead of the API method
                    self.client.post(f"admin/projects/{project_id}", data=data)
                    logger.info("Update API call successful")
                except Exception as e:
                    logger.warning(f"Update API call error: {str(e)}")
                    # Continue anyway as the update might still have worked

                # Get the updated project data
                try:
                    updated_project = self.projects_api.get_project(project_id)
                    logger.info(
                        f"Retrieved updated project: {updated_project.name}"
                    )

                    # Return updated project data
                    if hasattr(updated_project, "model_dump"):
                        return format_json_response(
                            updated_project.model_dump()
                        )
                    else:
                        return format_json_response(updated_project)
                except Exception as e:
                    logger.warning(
                        f"Could not retrieve updated project: {str(e)}"
                    )
                    return json.dumps(
                        {
                            "id": project_id,
                            "status": "updated",
                            "warning": str(e),
                        }
                    )
            except Exception as e:
                logger.exception(f"Error updating project {project_id}")
                return format_json_response({"error": str(e)})
        except Exception as e:
            logger.exception(f"Error processing update_project request")
            return format_json_response({"error": str(e)})

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
                "description": "Get a list of all YouTrack projects, optionally including archived ones. Example: get_projects(include_archived=False)",
                "parameter_descriptions": {
                    "include_archived": "Whether to include archived projects (default: False)"
                },
            },
            "get_project": {
                "description": 'Get detailed information about a specific YouTrack project. Example: get_project(project_id="DEMO")',
                "parameter_descriptions": {
                    "project_id": "Project identifier like 'DEMO' or '0-0'"
                },
            },
            "get_project_by_name": {
                "description": 'Find a project by its name or short name. Example: get_project_by_name(project_name="DEMO")',
                "parameter_descriptions": {
                    "project_name": "Project name or short name like 'DEMO'"
                },
            },
            "get_project_issues": {
                "description": 'Get all issues belonging to a specific project. Example: get_project_issues(project_id="DEMO", limit=20)',
                "parameter_descriptions": {
                    "project_id": "Project identifier like 'DEMO'",
                    "limit": "Maximum number of issues to return (default: 50)",
                },
            },
            "get_custom_fields": {
                "description": 'Get custom field definitions for a specific project. Example: get_custom_fields(project_id="DEMO")',
                "parameter_descriptions": {
                    "project_id": "Project identifier like 'DEMO'"
                },
            },
            "create_project": {
                "description": 'Create a new YouTrack project with specified name, key, and leader. Example: create_project(name="Demo Project", short_name="DEMO", lead_id="admin")',
                "parameter_descriptions": {
                    "name": "Full project name like 'Demo Project'",
                    "short_name": "Short key for issue prefixes like 'DEMO'",
                    "lead_id": "User ID who will lead the project",
                    "description": "Optional project description",
                },
            },
            "update_project": {
                "description": 'Update an existing YouTrack project settings. Example: update_project(project_id="DEMO", name="Updated Demo Project")',
                "parameter_descriptions": {
                    "project_id": "Project identifier like 'DEMO'",
                    "name": "New project name (optional)",
                    "description": "New project description (optional)",
                    "archived": "Whether to archive the project (optional)",
                    "lead_id": "New project leader ID (optional)",
                    "short_name": "New short name for issue prefixes (optional)",
                },
            },
        }
