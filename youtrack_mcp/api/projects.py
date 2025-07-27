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

    def get_custom_field_allowed_values(self, project_id: str, field_name: str) -> List[Dict[str, Any]]:
        """
        Get allowed values for a custom field in a specific project.

        Args:
            project_id: The project identifier
            field_name: The custom field name

        Returns:
            List of allowed values with id, name, and other properties
        """
        try:
            # Get field information directly to avoid recursion with get_custom_field_schema
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
            
            # Extract field type information
            field_schema = field_info.get("field", {})
            field_type = field_schema.get("fieldType", {})
            value_type = field_type.get("valueType", "")  # enum, state, user, etc.
            bundle_id = field_type.get("id")  # enum[1], state[1], etc.
            
            logger.info(f"Field '{field_name}' - valueType: {value_type}, bundleId: {bundle_id}")
            
            if not bundle_id:
                logger.warning(f"No bundle ID found for field '{field_name}'")
                return []
            
            # For enum fields, we need to resolve the correct bundle
            if value_type == "enum":
                # First, try to extract the actual bundle ID from bundle_id string (e.g., "enum[1]" -> "1")
                actual_bundle_id = None
                if "[" in bundle_id and "]" in bundle_id:
                    # Extract index from "enum[1]" format
                    bundle_index = bundle_id.split("[")[1].split("]")[0]
                    
                    # Get all enum bundles and find the one at this index
                    try:
                        all_enum_bundles = self.client.get('admin/customFieldSettings/bundles/enum?fields=id,name,values(id,name,description)')
                        if bundle_index.isdigit():
                            index = int(bundle_index)
                            if 0 <= index < len(all_enum_bundles):
                                target_bundle = all_enum_bundles[index]
                                actual_bundle_id = target_bundle.get('id')
                                logger.info(f"Resolved bundle index {index} to bundle ID {actual_bundle_id} ({target_bundle.get('name')})")
                                
                                # Return values from the correct bundle
                                values = target_bundle.get('values', [])
                                logger.info(f"Found {len(values)} values for field '{field_name}' in bundle '{target_bundle.get('name')}'")
                                return [
                                    {
                                        "name": value.get("name", ""),
                                        "description": value.get("description", ""),
                                        "id": value.get("id"),
                                        "bundle_name": target_bundle.get('name')
                                    }
                                    for value in values
                                ]
                    except Exception as e:
                        logger.error(f"Error resolving enum bundle index: {str(e)}")
                
                # Fallback: try the bundle_id directly
                if not actual_bundle_id:
                    actual_bundle_id = bundle_id.replace("enum[", "").replace("]", "")
                
                try:
                    bundle_data = self.client.get(f"admin/customFieldSettings/bundles/enum/{actual_bundle_id}?fields=id,name,values(id,name,description)")
                    values = bundle_data.get("values", [])
                    logger.info(f"Found {len(values)} values for enum field '{field_name}'")
                    return [
                        {
                            "name": value.get("name", ""),
                            "description": value.get("description", ""),
                            "id": value.get("id")
                        }
                        for value in values
                    ]
                except Exception as e:
                    logger.error(f"Error getting enum bundle {actual_bundle_id}: {str(e)}")
                    # Return enhanced guidance instead of empty array
                    return [
                        {
                            "name": "__ENUM_ACCESS_ERROR__",
                            "description": f"Could not access enum values for field '{field_name}'. This may be due to permissions or configuration issues.",
                            "id": "access-error",
                            "type": "guidance",
                            "bundle_id": actual_bundle_id,
                            "troubleshooting": [
                                "Check if you have admin permissions",
                                "Verify the field is properly configured",
                                "Try accessing through YouTrack UI: Administration → Custom Fields"
                            ]
                        }
                    ]
            
            elif value_type == "state":
                try:
                    # Handle both indexed format (state[1]) and direct bundle ID (state-bundle-123)
                    if "[" in bundle_id and "]" in bundle_id:
                        # Index-based format: state[1] means the first state bundle (0-based index)
                        all_bundles = self.client.get("admin/customFieldSettings/bundles/state?fields=id,name,values(id,name,description,isResolved,color)")
                        
                        bundle_index = int(bundle_id.split("[")[1].split("]")[0]) - 1  # Convert to 0-based index
                        if 0 <= bundle_index < len(all_bundles):
                            target_bundle = all_bundles[bundle_index]
                            values = target_bundle.get("values", [])
                            logger.info(f"Found {len(values)} state values for field '{field_name}' from bundle '{target_bundle.get('name')}'")
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
                        else:
                            logger.error(f"Bundle index {bundle_index} out of range for {len(all_bundles)} state bundles")
                            return []
                    else:
                        # Direct bundle ID format: get specific bundle
                        bundle_data = self.client.get(f"admin/customFieldSettings/bundles/state/{bundle_id}?fields=values(id,name,description,isResolved,color)")
                    
                    values = bundle_data.get("values", [])
                    logger.info(f"Found {len(values)} state values for field '{field_name}' from bundle '{bundle_data.get('name', 'unknown')}'")
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
            
            elif value_type == "user":
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
            
            elif value_type == "ownedField":
                try:
                    # For subsystem/owned fields, get subsystems for this project
                    subsystems_data = self.client.get(f"admin/projects/{project_id}/subsystems?fields=id,name,description")
                    logger.info(f"Found {len(subsystems_data)} subsystems for field '{field_name}'")
                    return [
                        {
                            "name": subsystem.get("name", ""),
                            "description": subsystem.get("description", ""),
                            "id": subsystem.get("id")
                        }
                        for subsystem in subsystems_data
                    ]
                except Exception as e:
                    logger.error(f"Error getting subsystems: {str(e)}")
                    # Return comprehensive guidance instead of empty array
                    return [
                        {
                            "name": "__CONFIGURATION_NEEDED__",
                            "description": f"No subsystems configured for project {project_id}. To enable subsystem custom fields:",
                            "id": "config-required",
                            "type": "guidance",
                            "action": "create_subsystems",
                            "steps": [
                                "1. Go to YouTrack project settings",
                                "2. Navigate to 'Subsystems' section", 
                                "3. Click 'New Subsystem'",
                                "4. Enter subsystem name and description",
                                "5. Save to enable subsystem custom fields"
                            ],
                            "alternative": "Use the create_subsystem() MCP tool if you have admin permissions"
                        }
                    ]
            
            elif value_type == "version":
                try:
                    # For version fields, get versions for this project
                    versions_data = self.client.get(f"admin/projects/{project_id}/versions?fields=id,name,description,released,releaseDate")
                    logger.info(f"Found {len(versions_data)} versions for field '{field_name}'")
                    return [
                        {
                            "name": version.get("name", ""),
                            "description": version.get("description", ""),
                            "id": version.get("id"),
                            "released": version.get("released", False),
                            "releaseDate": version.get("releaseDate")
                        }
                        for version in versions_data
                    ]
                except Exception as e:
                    logger.error(f"Error getting versions: {str(e)}")
                    # Return comprehensive guidance instead of empty array
                    return [
                        {
                            "name": "__CONFIGURATION_NEEDED__",
                            "description": f"No versions configured for project {project_id}. To enable version custom fields:",
                            "id": "config-required",
                            "type": "guidance",
                            "action": "create_versions",
                            "steps": [
                                "1. Go to YouTrack project settings",
                                "2. Navigate to 'Versions' section",
                                "3. Click 'New Version'", 
                                "4. Enter version name (e.g., 'v1.0.0')",
                                "5. Set release status and dates",
                                "6. Save to enable version custom fields"
                            ],
                            "alternative": "Use the create_version() MCP tool if you have admin permissions",
                            "examples": ["v1.0.0", "2024.1", "Sprint-1", "Release-Jan-2024"]
                        },
                        {
                            "name": "__FALLBACK_OPTION__",
                            "description": "Alternative: Use text fields or comments to track version information until versions are configured",
                            "id": "fallback-text",
                            "type": "workaround",
                            "suggested_approach": "Use description field or comments to mention version information"
                        }
                    ]
            
            elif value_type == "build":
                try:
                    # For build fields, get builds for this project
                    builds_data = self.client.get(f"admin/projects/{project_id}/builds?fields=id,name,description")
                    logger.info(f"Found {len(builds_data)} builds for field '{field_name}'")
                    return [
                        {
                            "name": build.get("name", ""),
                            "description": build.get("description", ""),
                            "id": build.get("id")
                        }
                        for build in builds_data
                    ]
                except Exception as e:
                    logger.error(f"Error getting builds: {str(e)}")
                    # Return comprehensive guidance instead of empty array
                    return [
                        {
                            "name": "__CONFIGURATION_NEEDED__",
                            "description": f"No builds configured for project {project_id}. To enable build custom fields:",
                            "id": "config-required", 
                            "type": "guidance",
                            "action": "create_builds",
                            "steps": [
                                "1. Go to YouTrack project settings",
                                "2. Navigate to 'Builds' section",
                                "3. Click 'New Build'",
                                "4. Enter build name (e.g., 'build-123')",
                                "5. Add description and metadata",
                                "6. Save to enable build custom fields"
                            ],
                            "alternative": "Use the create_build() MCP tool if you have admin permissions",
                            "examples": ["build-123", "nightly-2024-01-15", "release-1.0", "hotfix-001"]
                        }
                    ]
            
            else:
                logger.info(f"Field '{field_name}' type '{value_type}' doesn't support allowed values")
                return []
            
        except Exception as e:
            logger.error(f"Error getting custom field allowed values for '{field_name}': {str(e)}")
            return []

    def get_available_custom_field_values(
        self, project_id: str, field_name: str
    ) -> List[Dict[str, Any]]:
        """
        Alias for get_custom_field_allowed_values for backward compatibility.
        
        Args:
            project_id: The project ID
            field_name: The custom field name

        Returns:
            List of allowed values with details
        """
        return self.get_custom_field_allowed_values(project_id, field_name)

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
            
            value_type = field_schema.get("type", "")  # This is the valueType from API
            bundle_type = field_schema.get("bundle_type", "")  # This is the $type
            
            # Check if field is required and value is empty
            if field_schema.get("required", False) and (field_value is None or str(field_value).strip() == ""):
                return {
                    "valid": False,
                    "error": f"Field '{field_name}' is required and cannot be empty",
                    "suggestion": "Provide a valid value for this required field"
                }
            
            # Type-specific validation using the correct valueType
            if value_type == "state":
                # State field - validate against available states
                allowed_values = self.get_custom_field_allowed_values(project_id, field_name)
                allowed_names = [v.get("name", "") for v in allowed_values if isinstance(v, dict)]
                if str(field_value) not in allowed_names:
                    return {
                        "valid": False,
                        "error": f"Invalid state value '{field_value}' for field '{field_name}'",
                        "suggestion": f"Use one of: {', '.join(allowed_names)}" if allowed_names else "Check field configuration"
                    }
            
            elif value_type == "enum":
                # Enum field - validate against enum values
                allowed_values = self.get_custom_field_allowed_values(project_id, field_name)
                allowed_names = [v.get("name", "") for v in allowed_values if isinstance(v, dict)]
                if str(field_value) not in allowed_names:
                    return {
                        "valid": False,
                        "error": f"Invalid enum value '{field_value}' for field '{field_name}'",
                        "suggestion": f"Use one of: {', '.join(allowed_names)}" if allowed_names else "Check field configuration"
                    }
            
            elif value_type == "user":
                # User field - validate against available users
                allowed_values = self.get_custom_field_allowed_values(project_id, field_name)
                allowed_logins = [v.get("login", "") for v in allowed_values if isinstance(v, dict)]
                allowed_names = [v.get("name", "") for v in allowed_values if isinstance(v, dict)]
                if str(field_value) not in allowed_logins and str(field_value) not in allowed_names:
                    return {
                        "valid": False,
                        "error": f"User '{field_value}' not found",
                        "suggestion": f"Use valid user login: {', '.join(allowed_logins[:5])}" if allowed_logins else "Check user exists"
                    }
            
            elif value_type == "ownedField":
                # Subsystem field - validate against available subsystems
                allowed_values = self.get_custom_field_allowed_values(project_id, field_name)
                allowed_names = [v.get("name", "") for v in allowed_values if isinstance(v, dict)]
                if str(field_value) not in allowed_names:
                    return {
                        "valid": False,
                        "error": f"Invalid subsystem '{field_value}' for field '{field_name}'",
                        "suggestion": f"Use one of: {', '.join(allowed_names)}" if allowed_names else "Create subsystem first"
                    }
            
            elif value_type == "version":
                # Version field - validate against available versions
                allowed_values = self.get_custom_field_allowed_values(project_id, field_name)
                allowed_names = [v.get("name", "") for v in allowed_values if isinstance(v, dict)]
                if str(field_value) not in allowed_names:
                    return {
                        "valid": False,
                        "error": f"Invalid version '{field_value}' for field '{field_name}'",
                        "suggestion": f"Use one of: {', '.join(allowed_names)}" if allowed_names else "Create version first"
                    }
            
            elif value_type == "build":
                # Build field - validate against available builds
                allowed_values = self.get_custom_field_allowed_values(project_id, field_name)
                allowed_names = [v.get("name", "") for v in allowed_values if isinstance(v, dict)]
                if str(field_value) not in allowed_names:
                    return {
                        "valid": False,
                        "error": f"Invalid build '{field_value}' for field '{field_name}'",
                        "suggestion": f"Use one of: {', '.join(allowed_names)}" if allowed_names else "Create build first"
                    }
            
            elif value_type == "period":
                # Period field - validate format (e.g., "4h", "30m", "1h45m")
                import re
                period_pattern = r'^\d+[mhwd]$|^\d+h\d+m$'  # Simple pattern for periods
                if not re.match(period_pattern, str(field_value)):
                    return {
                        "valid": False,
                        "error": f"Invalid period format '{field_value}' for field '{field_name}'",
                        "suggestion": "Use format like '4h', '30m', '1h45m', or '2d'"
                    }
            
            elif value_type == "integer":
                # Integer field - validate that value can be converted to int
                try:
                        int(field_value)
                except (ValueError, TypeError):
                    return {
                        "valid": False,
                        "error": f"Invalid integer value '{field_value}' for field '{field_name}'",
                        "suggestion": "Provide a valid integer number"
                    }
            
            elif value_type == "float":
                # Float field - validate that value can be converted to float
                try:
                        float(field_value)
                except (ValueError, TypeError):
                    return {
                        "valid": False,
                        "error": f"Invalid float value '{field_value}' for field '{field_name}'",
                        "suggestion": "Provide a valid decimal number"
                    }
            
            # Multi-value field validation (if applicable, after type-specific)
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
                "suggestion": "Check field configuration and API connectivity"
            }
