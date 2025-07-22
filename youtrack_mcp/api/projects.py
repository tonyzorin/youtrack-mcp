"""
YouTrack Projects API client.
"""

from typing import Any, Dict, List, Optional
import json

from pydantic import BaseModel, Field

from youtrack_mcp.api.client import YouTrackClient
import logging

logger = logging.getLogger(__name__)


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

    def get_custom_field_schema(
        self, project_id: str, field_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed schema for a specific custom field.

        Args:
            project_id: The project ID
            field_name: The custom field name

        Returns:
            Custom field schema with type information and constraints
        """
        try:
            # Use detailed fields query to get complete information
            fields_query = "field(id,name,fieldType($type,valueType,id)),canBeEmpty,autoAttached"
            fields = self.client.get(f"admin/projects/{project_id}/customFields?fields={fields_query}")
            
            for field in fields:
                if field.get("field", {}).get("name") == field_name:
                    field_schema = field.get("field", {})
                    field_type = field_schema.get("fieldType", {})
                    
                    enhanced_schema = {
                        "name": field_name,
                        "type": field_type.get("valueType", "string"),
                        "bundle_type": field_type.get("$type", ""),
                        "required": field.get("canBeEmpty", True) == False,
                        "multi_value": field_schema.get("isMultiValue", False),
                        "auto_attach": field.get("autoAttached", False),
                        "field_id": field_schema.get("id"),
                        "bundle_id": field_type.get("id")
                    }
                    
                    logger.info(f"Found schema for field '{field_name}': {enhanced_schema}")
                    
                    # Add allowed values for enum/state fields
                    if field_type.get("valueType") in ["enum", "state"]:
                        try:
                            enhanced_schema["allowed_values"] = self.get_custom_field_allowed_values(project_id, field_name)
                        except Exception as e:
                            logger.warning(f"Could not get allowed values for {field_name}: {str(e)}")
                            enhanced_schema["allowed_values"] = []
                    
                    return enhanced_schema
            
            logger.warning(f"Field '{field_name}' not found in project {project_id} custom fields")
            return None
        except Exception as e:
            logger.error(f"Error getting custom field schema for '{field_name}': {str(e)}")
            return None

    def get_custom_field_allowed_values(
        self, project_id: str, field_name: str
    ) -> List[Dict[str, Any]]:
        """
        Get allowed values for enum/state custom fields.

        Args:
            project_id: The project ID
            field_name: The custom field name

        Returns:
            List of allowed values with details
        """
        try:
            # Get field information directly with detailed query
            fields_query = "field(id,name,fieldType($type,valueType,id)),canBeEmpty,autoAttached"
            fields = self.client.get(f"admin/projects/{project_id}/customFields?fields={fields_query}")
            
            field_info = None
            for field in fields:
                if field.get("field", {}).get("name") == field_name:
                    field_info = field
                    break
            
            if not field_info:
                logger.warning(f"Field '{field_name}' not found in project {project_id}")
                return []
            
            field_schema = field_info.get("field", {})
            field_type = field_schema.get("fieldType", {})
            bundle_type = field_type.get("$type", "")
            bundle_id = field_type.get("id")
            
            logger.info(f"Field '{field_name}' bundle type: {bundle_type}, bundle ID: {bundle_id}")
            
            if not bundle_id:
                logger.warning(f"No bundle ID found for field '{field_name}'")
                return []
            
            # Get bundle values based on type with detailed queries
            if "EnumBundle" in bundle_type:
                try:
                    bundle_data = self.client.get(f"admin/customFieldSettings/bundles/enum/{bundle_id}?fields=values(id,name,description,color)")
                    values = bundle_data.get("values", [])
                    logger.info(f"Found {len(values)} enum values for field '{field_name}'")
                    return [
                        {
                            "name": value.get("name", ""),
                            "description": value.get("description", ""),
                            "id": value.get("id"),
                            "color": value.get("color", {})
                        }
                        for value in values
                    ]
                except Exception as e:
                    logger.error(f"Error getting enum bundle {bundle_id}: {str(e)}")
                    return []
            
            elif "StateBundle" in bundle_type or "StateMachineBundle" in bundle_type:
                try:
                    # Try different endpoints for state bundles
                    bundle_endpoint = f"admin/customFieldSettings/bundles/state/{bundle_id}"
                    try:
                        bundle_data = self.client.get(f"{bundle_endpoint}?fields=values(id,name,description,isResolved,color)")
                    except:
                        # Fallback to simpler query
                        bundle_data = self.client.get(bundle_endpoint)
                    
                    values = bundle_data.get("values", [])
                    logger.info(f"Found {len(values)} state values for field '{field_name}'")
                    return [
                        {
                            "name": value.get("name", ""),
                            "description": value.get("description", ""),
                            "id": value.get("id"),
                            "resolved": value.get("isResolved", False),
                            "color": value.get("color", {})
                        }
                        for value in values
                    ]
                except Exception as e:
                    logger.error(f"Error getting state bundle {bundle_id}: {str(e)}")
                    return []
            
            elif "UserBundle" in bundle_type:
                try:
                    # For user fields, get available users
                    users_data = self.client.get("users?fields=id,login,name,email")
                    logger.info(f"Found {len(users_data)} users for field '{field_name}'")
                    return [
                        {
                            "name": user.get("name", ""),
                            "login": user.get("login", ""),
                            "id": user.get("id"),
                            "email": user.get("email", "")
                        }
                        for user in users_data
                    ]
                except Exception as e:
                    logger.error(f"Error getting users: {str(e)}")
                    return []
            
            else:
                logger.info(f"Field '{field_name}' type '{bundle_type}' doesn't support allowed values")
                return []
            
        except Exception as e:
            logger.error(f"Error getting custom field allowed values for '{field_name}': {str(e)}")
            return []

    def get_all_custom_fields_schemas(
        self, project_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get schemas for all custom fields in a project.

        Args:
            project_id: The project ID

        Returns:
            Dictionary mapping field names to their schemas
        """
        try:
            # Use the same detailed query that works in other methods
            fields_query = "field(id,name,fieldType($type,valueType,id)),canBeEmpty,autoAttached"
            fields = self.client.get(f"admin/projects/{project_id}/customFields?fields={fields_query}")
            schemas = {}
            
            logger.info(f"Got {len(fields)} custom fields for project {project_id}")
            
            for field in fields:
                # Extract field name from the correct structure
                field_info = field.get("field", {})
                field_name = field_info.get("name")
                
                if field_name:
                    logger.info(f"Processing field: {field_name}")
                    # Build schema directly from the field data we already have
                    field_type = field_info.get("fieldType", {})
                    
                    enhanced_schema = {
                        "name": field_name,
                        "type": field_type.get("valueType", "string"),
                        "bundle_type": field_type.get("$type", ""),
                        "required": field.get("canBeEmpty", True) == False,
                        "multi_value": field_info.get("isMultiValue", False),
                        "auto_attach": field.get("autoAttached", False),
                        "field_id": field_info.get("id"),
                        "bundle_id": field_type.get("id")
                    }
                    
                    # Add allowed values for enum/state fields
                    if field_type.get("valueType") in ["enum", "state"]:
                        try:
                            enhanced_schema["allowed_values"] = self.get_custom_field_allowed_values(project_id, field_name)
                        except Exception as e:
                            logger.warning(f"Could not get allowed values for {field_name}: {str(e)}")
                            enhanced_schema["allowed_values"] = []
                    
                    schemas[field_name] = enhanced_schema
                    logger.info(f"Added schema for field '{field_name}': {enhanced_schema}")
                else:
                    logger.warning(f"Field missing name: {field}")
            
            logger.info(f"Returning {len(schemas)} schemas for project {project_id}")
            return schemas
        except Exception as e:
            logger.error(f"Error getting all custom field schemas: {str(e)}")
            return {}

    def validate_custom_field_for_project(
        self, 
        project_id: str, 
        field_name: str, 
        field_value: Any
    ) -> Dict[str, Any]:
        """
        Validate a custom field value against project schema.
        
        Args:
            project_id: The project ID
            field_name: The custom field name
            field_value: The value to validate
            
        Returns:
            Dictionary with validation result
        """
        try:
            # Get field schema directly using the same approach as issues.py
            field_schema = self.get_custom_field_schema(project_id, field_name)
            if not field_schema:
                return {
                    "valid": False,
                    "error": f"Custom field '{field_name}' not found in project {project_id}",
                    "suggestion": "Check field name spelling and project configuration"
                }
            
            field_type = field_schema.get("type", "")  # This is the valueType
            bundle_type = field_schema.get("bundle_type", "")  # This is the $type
            
            # Type-specific validation using the same logic as issues.py
            if field_type == "state" or "StateBundle" in bundle_type or "StateMachine" in bundle_type:
                # State field - validate against available states
                allowed_values = self.get_custom_field_allowed_values(project_id, field_name)
                allowed_names = [v.get("name", "") for v in allowed_values if isinstance(v, dict)]
                if str(field_value) not in allowed_names:
                    return {
                        "valid": False,
                        "error": f"Invalid state value '{field_value}' for field '{field_name}'",
                        "suggestion": f"Use one of: {', '.join(allowed_names)}" if allowed_names else "Check field configuration"
                    }
            
            elif field_type == "enum" or "EnumBundle" in bundle_type:
                # Enum field - validate against enum values
                allowed_values = self.get_custom_field_allowed_values(project_id, field_name)
                allowed_names = [v.get("name", "") for v in allowed_values if isinstance(v, dict)]
                if str(field_value) not in allowed_names:
                    return {
                        "valid": False,
                        "error": f"Invalid enum value '{field_value}' for field '{field_name}'",
                        "suggestion": f"Use one of: {', '.join(allowed_names)}" if allowed_names else "Check field configuration"
                    }
            
            elif field_type == "user" or "UserBundle" in bundle_type:
                # User field - validate user exists
                try:
                    self.client.get(f"users/{field_value}")
                except:
                    return {
                        "valid": False,
                        "error": f"User '{field_value}' not found",
                        "suggestion": "Use valid user login or ID"
                    }
            
            elif field_type in ["integer", "float"]:
                try:
                    if field_type == "integer":
                        int(field_value)
                    else:
                        float(field_value)
                except (ValueError, TypeError):
                    return {
                        "valid": False,
                        "error": f"Invalid {field_type} value: {field_value}",
                        "suggestion": f"Provide a valid {field_type} number"
                    }
            
            elif field_type == "period":
                # Period field validation
                if not isinstance(field_value, str) or not field_value.startswith("PT"):
                    return {
                        "valid": False,
                        "error": f"Invalid period format: {field_value}",
                        "suggestion": "Use ISO 8601 duration format like 'PT2H30M' for 2 hours 30 minutes"
                    }
            
            # Multi-value field validation
            if field_schema.get("multi_value", False) and not isinstance(field_value, list):
                return {
                    "valid": False,
                    "error": f"Field '{field_name}' expects multiple values (array)",
                    "suggestion": "Provide value as an array, e.g., ['value1', 'value2']"
                }
            
            # If we reach here, validation passed
            return {
                "valid": True,
                "field": field_name,
                "value": field_value,
                "message": "Valid"
            }
            
        except Exception as e:
            logger.error(f"Error validating field '{field_name}': {str(e)}")
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}",
                "suggestion": "Check field name and project configuration"
            }
