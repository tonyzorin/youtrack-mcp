"""
YouTrack Issues API client.
"""

from typing import Any, Dict, List, Optional
import json
import logging

from pydantic import BaseModel, Field

from youtrack_mcp.api.client import YouTrackClient, YouTrackAPIError

logger = logging.getLogger(__name__)


class Issue(BaseModel):
    """Model for a YouTrack issue."""

    id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    created: Optional[int] = None
    updated: Optional[int] = None
    project: Optional[Dict[str, Any]] = Field(default_factory=dict)
    reporter: Optional[Dict[str, Any]] = None
    assignee: Optional[Dict[str, Any]] = None
    custom_fields: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    attachments: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    model_config = {
        "extra": "allow",  # Allow extra fields from the API
        "populate_by_name": True,  # Allow population by field name (helps with aliases)
        "validate_assignment": False,  # Less strict validation for attribute assignment
        "protected_namespaces": (),  # Don't protect any namespaces
    }

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        """Override model_validate to handle various input formats."""
        try:
            # Try standard validation
            return super().model_validate(obj, *args, **kwargs)
        except Exception as e:
            # Fall back to more permissive validation
            if isinstance(obj, dict):
                # Ensure ID is present
                if "id" not in obj and obj.get("$type") == "Issue":
                    # Try to find an ID from other fields or generate placeholder
                    obj["id"] = obj.get(
                        "idReadable", str(obj.get("created", "unknown-id"))
                    )

                # Create issue with minimal validated data
                return cls(
                    id=obj.get("id", "unknown"),
                    summary=obj.get("summary", "No summary"),
                    description=obj.get("description", ""),
                    created=obj.get("created"),
                    updated=obj.get("updated"),
                    project=obj.get("project", {}),
                    reporter=obj.get("reporter"),
                    assignee=obj.get("assignee"),
                    custom_fields=obj.get("customFields", []),
                )

            # If obj isn't even a dict, raise the original error
            raise


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
        try:
            # Get issue data
            response = self.client.get(f"issues/{issue_id}")

            # If the response doesn't have all needed fields, fetch more details
            if (
                isinstance(response, dict)
                and response.get("$type") == "Issue"
                and "summary" not in response
            ):
                # Get additional fields we need including attachments
                fields = "id,idReadable,summary,description,created,updated,project,reporter,assignee,customFields,attachments(id,name,url,mimeType,size)"
                try:
                    detailed_response = self.client.get(
                        f"issues/{issue_id}?fields={fields}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to get detailed issue data: {e}")
                    detailed_response = response
            else:
                detailed_response = response

            # Ensure the ID field is present
            if (
                isinstance(detailed_response, dict)
                and "id" not in detailed_response
                and detailed_response.get("$type") == "Issue"
            ):
                detailed_response["id"] = issue_id

            try:
                # Try to validate the model
                return Issue.model_validate(detailed_response)
            except Exception as validation_error:
                # If validation fails, create a more flexible issue object
                logger.warning(
                    f"Issue validation error: {validation_error}. Creating issue with minimal data."
                )

                if isinstance(detailed_response, dict):
                    # Extract key fields if possible
                    summary = detailed_response.get(
                        "summary", "Unknown summary"
                    )
                    description = detailed_response.get("description", "")

                    # Create a basic issue with the available data
                    issue = Issue(
                        id=issue_id, summary=summary, description=description
                    )

                    # Add any other fields that might be useful
                    for field in [
                        "created",
                        "updated",
                        "project",
                        "reporter",
                        "assignee",
                        "attachments",
                    ]:
                        if field in detailed_response:
                            setattr(issue, field, detailed_response[field])

                    return issue
                else:
                    # If response is not even a dict, create a minimal issue
                    return Issue(id=issue_id, summary=f"Issue {issue_id}")

        except Exception as e:
            # Log the full error with traceback
            logger.exception(f"Error retrieving issue {issue_id}")
            # Create minimal issue to avoid breaking calls
            return Issue(id=issue_id, summary=f"Error: {str(e)[:100]}...")

    def create_issue(
        self,
        project_id: str,
        summary: str,
        description: Optional[str] = None,
        additional_fields: Optional[Dict[str, Any]] = None,
    ) -> Issue:
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
        # Make sure we have valid input data
        if not project_id:
            raise ValueError("Project ID is required")
        if not summary:
            raise ValueError("Summary is required")

        # Format request data according to YouTrack API requirements
        # Note: YouTrack API requires a specific format for some fields
        data = {"project": {"id": project_id}, "summary": summary}

        if description:
            data["description"] = description

        if additional_fields:
            data.update(additional_fields)

        try:
            # For debugging
            logger.info(f"Creating issue with data: {json.dumps(data)}")

            # Post directly with the json parameter to ensure correct format
            url = "issues"
            response = self.client.session.post(
                f"{self.client.base_url}/{url}",
                json=data,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )

            # Handle the response
            if response.status_code >= 400:
                error_msg = f"Error creating issue: {response.status_code}"
                try:
                    error_content = response.json()
                    error_msg += f" - {json.dumps(error_content)}"
                except Exception:
                    error_msg += f" - {response.text}"

                logger.error(error_msg)
                raise YouTrackAPIError(
                    error_msg, response.status_code, response
                )

            # Process successful response
            try:
                result = response.json()
                return Issue.model_validate(result)
            except Exception as e:
                logger.error(f"Error parsing response: {str(e)}")
                # Return raw response if we can't parse it
                return Issue(
                    id=str(response.status_code),
                    summary="Created successfully",
                )

        except Exception as e:
            import logging

            logging.getLogger(__name__).error(
                f"Error creating issue: {str(e)}, Data: {data}"
            )
            raise

    def update_issue(
        self,
        issue_id: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        additional_fields: Optional[Dict[str, Any]] = None,
    ) -> Issue:
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

    def update_issue_custom_fields(
        self,
        issue_id: str,
        custom_fields: Dict[str, Any],
        validate: bool = True,
    ) -> Issue:
        """
        Update multiple custom fields on an issue using YouTrack Commands API.

        Args:
            issue_id: The issue ID or readable ID
            custom_fields: Dictionary of custom field name-value pairs
            validate: Whether to validate field values against project schema

        Returns:
            The updated issue data

        Raises:
            YouTrackAPIError: If validation fails or API call fails
        """
        if not custom_fields:
            return self.get_issue(issue_id)

        # Get current issue to determine project for validation
        project_id = None
        if validate:
            try:
                # Get issue with explicit project field to ensure we have project ID
                fields = "id,idReadable,project(id,shortName)"
                issue_response = self.client.get(f"issues/{issue_id}?fields={fields}")
                project_id = issue_response.get("project", {}).get("id") if issue_response.get("project") else None
                
                if not project_id:
                    # Fallback: try to extract project from issue ID format (e.g., DEMO-123 -> DEMO)
                    if "-" in issue_id and not issue_id.replace("-", "").isdigit():
                        project_short_name = issue_id.split("-")[0]
                        logger.info(f"Extracting project short name '{project_short_name}' from issue ID '{issue_id}'")
                        # Get project ID from short name
                        try:
                            projects_response = self.client.get(f"admin/projects?fields=id,shortName")
                            for proj in projects_response:
                                if proj.get("shortName") == project_short_name:
                                    project_id = proj.get("id")
                                    logger.info(f"Found project ID '{project_id}' for short name '{project_short_name}'")
                                    break
                        except Exception as e:
                            logger.warning(f"Could not find project by short name '{project_short_name}': {str(e)}")
                
                if not project_id:
                    logger.error(f"Could not determine project ID for issue '{issue_id}'. Issue response: {issue_response}")
                    
            except Exception as e:
                logger.error(f"Error getting issue project info: {str(e)}")
                project_id = None

        if validate and project_id:
            # Validate each field before updating
            validation_errors = []
            for field_name, field_value in custom_fields.items():
                try:
                    if not self._validate_custom_field_value(project_id, field_name, field_value):
                        validation_errors.append(f"Invalid value for field '{field_name}': {field_value}")
                except Exception as e:
                    validation_errors.append(f"Validation error for field '{field_name}': {str(e)}")
            
            if validation_errors:
                raise YouTrackAPIError(f"Custom field validation failed: {'; '.join(validation_errors)}")

        # Use YouTrack Commands API to update custom fields
        # This is the CORRECT way to update custom fields according to YouTrack documentation
        
        # Build command query from custom fields
        command_parts = []
        for field_name, field_value in custom_fields.items():
            # Format field value for commands API
            if isinstance(field_value, str):
                # If value contains spaces, wrap in quotes if needed
                if " " in field_value and not (field_value.startswith('"') and field_value.endswith('"')):
                    formatted_value = f'"{field_value}"'
                else:
                    formatted_value = field_value
            else:
                formatted_value = str(field_value)
            
            command_parts.append(f"{field_name} {formatted_value}")
        
        command_query = " ".join(command_parts)
        logger.info(f"Executing command: {command_query}")
        
        # Execute the command using Commands API
        command_data = {
            "query": command_query,
            "issues": [{"idReadable": issue_id}]
        }
        
        try:
            self.client.post("commands", data=command_data)
            logger.info(f"Successfully applied command to issue {issue_id}")
            
            # Return the updated issue
            return self.get_issue(issue_id)
            
        except Exception as e:
            logger.error(f"Failed to apply command '{command_query}' to issue {issue_id}: {str(e)}")
            raise YouTrackAPIError(f"Failed to update custom fields: {str(e)}")

    def get_issue_custom_fields(self, issue_id: str) -> Dict[str, Any]:
        """
        Get all custom fields for a specific issue.

        Args:
            issue_id: The issue ID or readable ID

        Returns:
            Dictionary of custom field name-value pairs
        """
        fields = "customFields(id,name,value($type,name,text,id,login))"
        response = self.client.get(f"issues/{issue_id}?fields={fields}")
        
        custom_fields = {}
        if "customFields" in response:
            for field in response["customFields"]:
                field_name = field.get("name", "")
                field_value = self._extract_custom_field_value(field.get("value"))
                custom_fields[field_name] = field_value
        
        return custom_fields

    def validate_custom_field_value(
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
            Dictionary with validation result and details
        """
        try:
            is_valid = self._validate_custom_field_value(project_id, field_name, field_value)
            
            if is_valid:
                return {
                    "valid": True,
                    "field": field_name,
                    "value": field_value,
                    "message": "Valid"
                }
            else:
                # Get available values for better error messages
                available_values = self._get_custom_field_allowed_values(project_id, field_name)
                suggestion = f"Available values: {', '.join(map(str, available_values))}" if available_values else "Check field configuration"
                
                return {
                    "valid": False,
                    "field": field_name,
                    "value": field_value,
                    "error": f"Invalid value '{field_value}' for field '{field_name}'",
                    "suggestion": suggestion
                }
        except Exception as e:
            return {
                "valid": False,
                "field": field_name,
                "value": field_value,
                "error": f"Validation error: {str(e)}",
                "suggestion": "Check field name and project configuration"
            }

    def batch_update_custom_fields(
        self,
        updates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Update custom fields for multiple issues in a single operation.

        Args:
            updates: List of update dictionaries with format:
                    [{"issue_id": "DEMO-123", "fields": {"Priority": "High"}}]

        Returns:
            List of update results with success/error status
        """
        results = []
        
        for update in updates:
            issue_id = update.get("issue_id")
            fields = update.get("fields", {})
            
            if not issue_id:
                results.append({
                    "issue_id": None,
                    "status": "error",
                    "error": "Missing issue_id in update"
                })
                continue
            
            if not fields:
                results.append({
                    "issue_id": issue_id,
                    "status": "skipped",
                    "message": "No fields to update"
                })
                continue
            
            try:
                updated_issue = self.update_issue_custom_fields(
                    issue_id=issue_id,
                    custom_fields=fields,
                    validate=update.get("validate", True)
                )
                
                results.append({
                    "issue_id": issue_id,
                    "status": "success",
                    "updated_fields": list(fields.keys()),
                    "issue_data": updated_issue.model_dump() if hasattr(updated_issue, 'model_dump') else updated_issue
                })
                
            except Exception as e:
                results.append({
                    "issue_id": issue_id,
                    "status": "error",
                    "error": str(e),
                    "attempted_fields": list(fields.keys())
                })
        
        return results

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
        fields = "id,idReadable,summary,description,created,updated,project,reporter,assignee,customFields"
        params = {"query": query, "$top": limit, "fields": fields}
        response = self.client.get("issues", params=params)

        issues = []
        if isinstance(response, list):
            for issue_data in response:
                try:
                    issues.append(Issue.model_validate(issue_data))
                except Exception as e:
                    logger.warning(f"Error validating issue: {e}")
                    # Create a basic issue with id
                    issue_id = issue_data.get(
                        "id", str(issue_data.get("created", "unknown"))
                    )
                    issues.append(
                        Issue(
                            id=issue_id,
                            summary=issue_data.get(
                                "summary", f"Issue {issue_id}"
                            ),
                        )
                    )

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

    def get_attachment_content(
        self, issue_id: str, attachment_id: str
    ) -> bytes:
        """
        Get the content of an attachment with file size validation.

        Args:
            issue_id: The issue ID or readable ID
            attachment_id: The attachment ID

        Returns:
            The attachment content as bytes

        Raises:
            ValueError: If attachment not found or file too large
            YouTrackAPIError: If API request fails
        """
        # First, get the attachment metadata to get the URL and size
        issue_response = self.client.get(
            f"issues/{issue_id}?fields=attachments(id,url,size,name,mimeType)"
        )

        # Find the attachment with the matching ID
        attachment_info = None
        if "attachments" in issue_response:
            for attachment in issue_response["attachments"]:
                if attachment.get("id") == attachment_id:
                    attachment_info = attachment
                    break

        if not attachment_info:
            raise ValueError(
                f"Attachment {attachment_id} not found in issue {issue_id}"
            )

        # Check file size limit for base64 encoding
        # Base64 encoding increases size by ~33%, so for 1MB base64 limit, max original size is ~750KB
        MAX_ORIGINAL_SIZE = 750 * 1024  # 750KB original file
        MAX_BASE64_SIZE = (
            1024 * 1024
        )  # 1MB after base64 encoding (Claude Desktop limit)

        file_size = attachment_info.get("size", 0)
        filename = attachment_info.get("name", attachment_id)
        mime_type = attachment_info.get("mimeType", "unknown")

        if file_size > MAX_ORIGINAL_SIZE:
            # Calculate what the base64 size would be
            estimated_base64_size = int(file_size * 1.33)
            raise ValueError(
                f"Attachment '{filename}' ({mime_type}) is too large "
                f"({file_size:,} bytes → ~{estimated_base64_size:,} bytes after base64 encoding). "
                f"Maximum allowed: {MAX_ORIGINAL_SIZE:,} bytes original (~{MAX_BASE64_SIZE:,} bytes base64)."
            )

        attachment_url = attachment_info.get("url")
        if not attachment_url:
            raise ValueError(
                f"No download URL found for attachment {attachment_id}"
            )

        # The URL in the attachment data is relative to the base URL
        if attachment_url.startswith("/"):
            attachment_url = attachment_url[1:]  # Remove leading slash

        # Construct the full URL
        base_url = self.client.base_url
        if base_url.endswith("/api"):
            base_url = base_url[:-4]  # Remove '/api' suffix

        full_url = f"{base_url}/{attachment_url}"

        # Make the request to get the attachment content
        from youtrack_mcp.api.client import YouTrackAPIError

        response = self.client.session.get(full_url)

        # Check for errors
        if response.status_code >= 400:
            error_msg = (
                f"Error getting attachment content: {response.status_code}"
            )
            raise YouTrackAPIError(error_msg, response.status_code, response)

        # Double-check the actual content size
        content_length = len(response.content)
        if content_length > MAX_ORIGINAL_SIZE:
            estimated_base64_size = int(content_length * 1.33)
            raise ValueError(
                f"Downloaded content size ({content_length:,} bytes → ~{estimated_base64_size:,} bytes base64) "
                f"exceeds maximum allowed size ({MAX_ORIGINAL_SIZE:,} bytes original). "
                f"The file may have been modified since metadata was fetched."
            )

        # Return the binary content
        return response.content

    def _get_internal_id(self, issue_id: str) -> str:
        """Convert issue ID to internal format if needed."""
        try:
            internal_id = self.client.get(f"issues/{issue_id}?fields=id")["id"]
            return internal_id
        except Exception:
            # If that fails, assume the issue_id is already internal
            return issue_id

    def _get_readable_id(self, issue_id: str) -> str:
        """
        Convert an internal issue ID (like 3-37) to readable ID (like DEMO-37).
        If it's already a readable ID, return as-is.

        Args:
            issue_id: Issue ID (internal like '3-41' or readable like 'DEMO-123')

        Returns:
            Readable project ID (like 'DEMO-41')
        """
        try:
            # If it doesn't look like an internal ID, return as-is
            if not ("-" in issue_id and issue_id.replace("-", "").isdigit()):
                return issue_id

            # Fetch the issue to get its readable ID
            issue = self.client.get(f"issues/{issue_id}?fields=idReadable")
            return issue.get("idReadable", issue_id)
        except Exception:
            # If we can't get the readable ID, return the original
            return issue_id

    def link_issues(
        self, source_issue_id: str, target_issue_id: str, link_type: str
    ) -> dict:
        """
        Link two issues together using Commands API.

        Args:
            source_issue_id: The ID of the source issue
            target_issue_id: The ID of the target issue
            link_type: The type of link (e.g., 'Relates', 'Duplicates', 'Depends on')

        Returns:
            The created link data
        """
        # Map link types to correct YouTrack command syntax
        link_command_map = {
            "relates": "relates to",
            "depends on": "depends on",
            "duplicates": "duplicates",
            "is duplicated by": "is duplicated by",
            "is required for": "is required for",
            "parent for": "parent for",
            "subtask": "subtask of",
            "subtask of": "subtask of",
        }

        # Get internal IDs for both issues (Commands API requires internal IDs in issues array)
        source_internal_id = self._get_internal_id(source_issue_id)
        target_internal_id = self._get_internal_id(target_issue_id)
        
        # Get readable IDs for command text (Commands API expects readable IDs in command)
        target_readable_id = self._get_readable_id(target_issue_id)

        # Normalize the link_type to lowercase and map to command
        link_type_lower = link_type.lower()
        command_phrase = link_command_map.get(link_type_lower, link_type_lower)

        # Build the command using correct YouTrack syntax with readable target ID
        # Commands expect readable IDs like "DEMO-37" in command text, but internal IDs in issues array
        command = f"{command_phrase} {target_readable_id}"

        command_data = {
            "query": command,
            "issues": [{"id": source_internal_id}],
        }

        response = self.client.post("commands", data=command_data)

        # Return success response if the command executed
        if isinstance(response, dict):
            return {
                "status": "success",
                "message": f"Successfully linked {source_issue_id} to {target_issue_id} with relationship '{link_type}'",
                "command": command,
                "source_issue": source_issue_id,
                "target_issue": target_issue_id,
                "link_type": link_type,
                "internal_ids": {
                    "source": source_internal_id,
                    "target": target_internal_id,
                },
            }

        return response

    def get_issue_links(self, issue_id: str) -> dict:
        """
        Get all links for an issue.

        Args:
            issue_id: The ID of the issue

        Returns:
            Dictionary containing inward and outward issue links
        """
        fields = "id,summary,linkType(name,localizedName),direction"
        response = self.client.get(f"issues/{issue_id}/links?fields={fields}")
        return response

    def get_available_link_types(self) -> dict:
        """
        Get all available issue link types.

        Returns:
            List of available link types with their properties
        """
        fields = "name,localizedName,sourceToTarget,targetToSource"
        response = self.client.get(f"issueLinkTypes?fields={fields}")
        return response

    def _validate_custom_field_value(
        self, 
        project_id: str, 
        field_name: str, 
        field_value: Any
    ) -> bool:
        """
        Internal method to validate a custom field value.

        Args:
            project_id: The project ID
            field_name: The custom field name  
            field_value: The value to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            # Get field schema from project
            field_schema = self._get_custom_field_schema(project_id, field_name)
            if not field_schema:
                # If we can't get schema, assume valid (fallback)
                return True
            
            field_type = field_schema.get("type", "")
            
            # Type-specific validation
            if field_type in ["StateMachineBundle", "StateBundle"]:
                # State field - validate against available states
                allowed_values = self._get_custom_field_allowed_values(project_id, field_name)
                return str(field_value) in [str(v) for v in allowed_values]
            
            elif field_type in ["EnumBundle", "OwnedBundle"]:
                # Enum field - validate against enum values
                allowed_values = self._get_custom_field_allowed_values(project_id, field_name)
                return str(field_value) in [str(v) for v in allowed_values]
            
            elif field_type == "UserBundle":
                # User field - validate user exists
                return self._validate_user_exists(field_value)
            
            elif field_type == "DateTimeBundle":
                # Date field - validate format
                return self._validate_date_format(field_value)
            
            elif field_type in ["IntegerBundle", "FloatBundle"]:
                # Numeric field - validate numeric value
                return self._validate_numeric_value(field_value, field_type)
            
            else:
                # String or unknown type - minimal validation
                return field_value is not None
                
        except Exception:
            # If validation fails due to API errors, assume valid (fallback)
            return True

    def _get_custom_field_schema(self, project_id: str, field_name: str) -> Optional[Dict[str, Any]]:
        """Get custom field schema from project."""
        try:
            fields = self.client.get(f"admin/projects/{project_id}/customFields")
            for field in fields:
                if field.get("field", {}).get("name") == field_name:
                    return field.get("field", {})
            return None
        except Exception:
            return None

    def _get_custom_field_allowed_values(self, project_id: str, field_name: str) -> List[Any]:
        """Get allowed values for enum/state fields."""
        try:
            field_schema = self._get_custom_field_schema(project_id, field_name)
            if not field_schema:
                return []
            
            field_type = field_schema.get("fieldType", {}).get("valueType")
            if field_type in ["enum", "state"]:
                # Get bundle values
                bundle_id = field_schema.get("fieldType", {}).get("id")
                if bundle_id:
                    bundle = self.client.get(f"admin/customFieldSettings/bundles/{field_type}/{bundle_id}")
                    return [value.get("name", "") for value in bundle.get("values", [])]
            
            return []
        except Exception:
            return []

    def _validate_user_exists(self, user_value: str) -> bool:
        """Validate that a user exists."""
        try:
            # Try to get user by login or ID
            self.client.get(f"users/{user_value}")
            return True
        except Exception:
            return False

    def _validate_date_format(self, date_value: Any) -> bool:
        """Validate date format."""
        if isinstance(date_value, int):
            # Unix timestamp
            return date_value > 0
        elif isinstance(date_value, str):
            # ISO date string or other formats
            import datetime
            try:
                datetime.datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return True
            except ValueError:
                return False
        return False

    def _validate_numeric_value(self, value: Any, field_type: str) -> bool:
        """Validate numeric value."""
        try:
            if field_type == "IntegerBundle":
                int(value)
                return True
            elif field_type == "FloatBundle":
                float(value)
                return True
        except (ValueError, TypeError):
            return False
        return False

    def _format_custom_field_value(self, field_name: str, field_value: Any) -> Dict[str, Any]:
        """Format custom field value for YouTrack API."""
        # YouTrack API expects different formats for different field types
        # The key issue: we need to use field ID, not name, and proper value format
        
        if field_value is None:
            return {
                "name": field_name,
                "value": None
            }
        
        # For most string-based fields (State, Enum, etc.)
        if isinstance(field_value, str):
            return {
                "name": field_name,
                "value": {"name": field_value}
            }
        # For user fields, expect login format
        elif isinstance(field_value, dict) and "login" in field_value:
            return {
                "name": field_name,
                "value": {"login": field_value["login"]}
            }
        # For user fields as string (login)
        elif isinstance(field_value, str) and field_name.lower() in ["assignee", "reporter"]:
            return {
                "name": field_name,
                "value": {"login": field_value}
            }
        # For numeric fields (Period, Integer, Float)
        elif isinstance(field_value, (int, float)):
            return {
                "name": field_name,
                "value": field_value
            }
        # For period fields (time tracking)
        elif isinstance(field_value, str) and field_value.startswith("PT"):
            return {
                "name": field_name,
                "value": {"presentation": field_value}
            }
        # For complex objects (already formatted)
        elif isinstance(field_value, dict):
            return {
                "name": field_name,
                "value": field_value
            }
        # Default fallback
        else:
            return {
                "name": field_name,
                "value": {"name": str(field_value)}
            }

    def _get_custom_field_id(self, project_id: str, field_name: str) -> Optional[str]:
        """Get the field ID for a custom field by name."""
        try:
            # Use detailed fields query to get complete field information
            fields_query = "field(id,name,fieldType($type,valueType,id)),canBeEmpty,autoAttached"
            fields = self.client.get(f"admin/projects/{project_id}/customFields?fields={fields_query}")
            for field in fields:
                if field.get("field", {}).get("name") == field_name:
                    return field.get("field", {}).get("id")
            return None
        except Exception as e:
            logger.warning(f"Error getting field ID for '{field_name}': {str(e)}")
            return None

    def _get_field_type_info(self, project_id: str, field_id: str) -> Dict[str, Any]:
        """Get field type information for proper $type formatting."""
        try:
            fields_query = "field(id,name,fieldType($type,valueType,id)),canBeEmpty,autoAttached"
            fields = self.client.get(f"admin/projects/{project_id}/customFields?fields={fields_query}")
            
            for field in fields:
                if field.get("field", {}).get("id") == field_id:
                    field_type = field.get("field", {}).get("fieldType", {})
                    return {
                        "bundle_type": field_type.get("$type", ""),
                        "value_type": field_type.get("valueType", ""),
                        "bundle_id": field_type.get("id")
                    }
            return {}
        except Exception as e:
            logger.warning(f"Error getting field type info for field ID '{field_id}': {str(e)}")
            return {}

    def _format_custom_field_value_with_id(self, field_id: str, field_value: Any, project_id: str = None) -> Dict[str, Any]:
        """Format custom field value with field ID for YouTrack API."""
        # YouTrack API format: Complete IssueCustomField object with proper $type
        
        # Get field type information to determine the correct IssueCustomField $type
        field_type_info = self._get_field_type_info(project_id, field_id) if project_id else {}
        bundle_type = field_type_info.get("bundle_type", "")
        value_type = field_type_info.get("value_type", "")
        
        # Determine the IssueCustomField $type based on the bundle type and value type
        issue_field_type = self._get_issue_custom_field_type(bundle_type, value_type, field_id)
        
        # Format the value based on type
        formatted_value = self._format_field_value(field_value, bundle_type, value_type, field_id)
        
        return {
            "id": field_id,
            "value": formatted_value,
            "$type": issue_field_type
        }
    
    def _get_issue_custom_field_type(self, bundle_type: str, value_type: str, field_id: str) -> str:
        """Determine the correct IssueCustomField $type based on field information."""
        
        # Check for user fields first (special case)
        if any(keyword in field_id.lower() for keyword in ["assignee", "reporter", "user"]) or "UserBundle" in bundle_type:
            return "SingleUserIssueCustomField"
        
        # Map based on value type and bundle type
        if value_type == "enum":
            return "SingleEnumIssueCustomField"
        elif value_type == "state":
            return "StateIssueCustomField"
        elif value_type == "user":
            return "SingleUserIssueCustomField"
        elif value_type == "period":
            return "PeriodIssueCustomField"
        elif value_type in ["integer", "float", "string", "date"]:
            return "SimpleIssueCustomField"
        elif value_type == "text":
            return "TextIssueCustomField"
        elif "StateBundle" in bundle_type or "StateMachine" in bundle_type:
            return "StateIssueCustomField"
        elif "EnumBundle" in bundle_type:
            return "SingleEnumIssueCustomField"
        elif "UserBundle" in bundle_type:
            return "SingleUserIssueCustomField"
        elif "PeriodBundle" in bundle_type:
            return "PeriodIssueCustomField"
        else:
            # Default fallback based on common field names
            if "priority" in field_id.lower() or "type" in field_id.lower():
                return "SingleEnumIssueCustomField"
            elif "state" in field_id.lower():
                return "StateIssueCustomField"
            else:
                return "SingleEnumIssueCustomField"  # Most common type
    
    def _format_field_value(self, field_value: Any, bundle_type: str, value_type: str, field_id: str) -> Any:
        """Format the field value based on type information."""
        
        if field_value is None:
            return None
        
        # For user fields
        if any(keyword in field_id.lower() for keyword in ["assignee", "reporter", "user"]) or "UserBundle" in bundle_type or value_type == "user":
            if isinstance(field_value, str):
                return {
                    "login": field_value,
                    "$type": "User"
                }
            elif isinstance(field_value, dict) and "login" in field_value:
                return {
                    "login": field_value["login"],
                    "$type": "User"
                }
        
        # For period fields
        elif value_type == "period" or (isinstance(field_value, str) and field_value.startswith("PT")):
            return {
                "presentation": str(field_value),
                "$type": "PeriodValue"
            }
        
        # For state fields
        elif value_type == "state" or "StateBundle" in bundle_type or "StateMachine" in bundle_type or "state" in field_id.lower():
            return {
                "name": str(field_value),
                "$type": "StateBundleElement"
            }
        
        # For enum fields
        elif value_type == "enum" or "EnumBundle" in bundle_type:
            return {
                "name": str(field_value),
                "$type": "EnumBundleElement"
            }
        
        # For numeric fields
        elif value_type in ["integer", "float"] and isinstance(field_value, (int, float)):
            return field_value
        
        # For text/string fields
        elif value_type in ["string", "text"]:
            return str(field_value)
        
        # For date fields
        elif value_type == "date":
            return field_value  # Assume it's already properly formatted
        
        # Default: treat as enum
        else:
            return {
                "name": str(field_value),
                "$type": "EnumBundleElement"
            }

    def _extract_custom_field_value(self, field_value_data: Any) -> Any:
        """Extract readable value from YouTrack custom field value data."""
        if not field_value_data:
            return None
        
        if isinstance(field_value_data, dict):
            # Try different value formats
            if "name" in field_value_data:
                return field_value_data["name"]
            elif "login" in field_value_data:
                return field_value_data["login"]
            elif "text" in field_value_data:
                return field_value_data["text"]
            elif "id" in field_value_data:
                return field_value_data["id"]
        
        return field_value_data
