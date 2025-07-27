"""
YouTrack Issues API client.
"""

from typing import Any, Dict, List, Optional
import json
import logging
import re

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
                fields = "id,idReadable,summary,description,created,updated,project(id,shortName),reporter,assignee,customFields,attachments(id,name,url,mimeType,size)"
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
        use_commands: bool = False,  # Changed default to False - direct API works better
    ) -> Dict[str, Any]:
        """
        Update multiple custom fields on an issue using proven working approach.

        Based on successful testing with this YouTrack instance:
        - Direct Field Update API works reliably for state transitions  
        - Command API may be blocked by workflow restrictions
        - Uses direct API as primary method with command fallback

        Args:
            issue_id: The issue identifier
            custom_fields: Dictionary of field names and values to update
            validate: Whether to validate field values before updating
            use_commands: Whether to try command-based approach as fallback (default: False)

        Returns:
            Updated issue data
        """
        try:
            # First, get current issue state to detect state machine workflows
            issue_data = self.get_issue(issue_id)
            
            # Check if we're updating State field and if it uses state machines
            state_field_update = None
            other_fields = {}
            
            for field_name, field_value in custom_fields.items():
                if field_name.lower() == 'state':
                    state_field_update = (field_name, field_value)
                else:
                    other_fields[field_name] = field_value
            
            # Handle state transitions with enhanced workflow support
            if state_field_update:
                field_name, target_state = state_field_update
                success = self._handle_state_transition(issue_id, target_state, use_commands)
                
                # Only try command-based fallback if we haven't already tried it
                if not success and not use_commands:
                    logger.info(f"Direct state update failed, trying command-based approach for issue {issue_id}")
                    success = self._handle_state_transition(issue_id, target_state, use_commands=True)
                
                if not success:
                    raise YouTrackAPIError(f"Failed to transition issue {issue_id} to state '{target_state}'. This may be due to workflow restrictions, permissions, or state machine guard conditions.")
            
            # Handle other custom fields using existing logic
            if other_fields:
                self._update_other_custom_fields(issue_id, other_fields, validate, use_commands)
            
            # Return updated issue data
            return self.get_issue(issue_id)

        except Exception as e:
            logger.exception(f"Error updating custom fields for issue {issue_id}")
            raise YouTrackAPIError(f"Failed to update custom fields: {str(e)}")
    
    def _handle_state_transition(self, issue_id: str, target_state: str, use_commands: bool = False) -> bool:
        """
        Handle state transitions using multiple approaches based on YouTrack configuration.
        
        This method tries different approaches in order:
        1. Direct Field Update API (works for some fields, may fail due to workflow restrictions)
        2. Command-based approach (more reliable but can be blocked by permissions)
        3. Event-based transitions for state machine workflows
        
        Args:
            issue_id: The issue identifier
            target_state: Target state name
            use_commands: Whether to prioritize command-based approach
            
        Returns:
            True if transition succeeded, False otherwise
        """
        try:
            # Method 1: Direct Field Update (PROVEN TO WORK in testing)
            logger.info(f"Attempting direct field update for issue {issue_id} to state '{target_state}'")
            success = self._apply_direct_state_update(issue_id, target_state)
            
            if success:
                logger.info(f"Direct field update succeeded for issue {issue_id}")
                return True
            
            # Method 2: Fallback to command-based approach if enabled
            if use_commands:
                logger.info(f"Direct update failed, trying command-based approach for issue {issue_id}")
                try:
                    command_data = {
                        "query": f"State \"{target_state}\"",
                        "issues": [{"id": issue_id}]
                    }
                    
                    logger.info(f"Applying state transition command 'State \"{target_state}\"' to issue {issue_id}")
                    self.client.post("commands", data=command_data)
                    logger.info(f"Command-based transition succeeded for issue {issue_id}")
                    return True
                    
                except Exception as cmd_error:
                    logger.warning(f"Command-based approach failed: {cmd_error}")
            
            # Method 3: Try state machine detection and event-based transitions
            logger.info(f"Trying state machine event-based approach for issue {issue_id}")
            try:
                # Query possible transitions (as recommended in analysis)
                issue_fields = self.client.get(f"issues/{issue_id}/customFields?fields=name,possibleEvents(id,presentation),value(name),$type")
                
                state_field = None
                for field in issue_fields:
                    if field.get('name', '').lower() == 'state':
                        state_field = field
                        break
                
                if state_field:
                    field_type = state_field.get('$type', '')
                    possible_events = state_field.get('possibleEvents', [])
                    
                    # Check if this is a state machine workflow
                    if field_type == 'StateMachineIssueCustomField' and possible_events:
                        # Use event-based transition
                        logger.info(f"Detected state machine workflow for issue {issue_id}")
                        return self._apply_state_machine_transition(issue_id, target_state, possible_events)
                
            except Exception as sm_error:
                logger.warning(f"State machine detection failed: {sm_error}")
            
            # All methods failed
            logger.error(f"All state transition methods failed for issue {issue_id} to state '{target_state}'")
            return False
                     
        except Exception as e:
            logger.error(f"State transition failed for issue {issue_id} to state '{target_state}': {e}")
            return False
    
    def _apply_state_machine_transition(self, issue_id: str, target_state: str, possible_events: List[Dict]) -> bool:
        """
        Apply state machine-based transition using events.
        
        Args:
            issue_id: The issue identifier
            target_state: Target state name
            possible_events: Available transition events
            
        Returns:
            True if transition succeeded, False otherwise
        """
        try:
            # Find the event that leads to the target state
            target_event = None
            for event in possible_events:
                # This would need more sophisticated matching logic
                # based on the actual event structure in your YouTrack instance
                event_presentation = event.get('presentation', '').lower()
                if target_state.lower() in event_presentation:
                    target_event = event
                    break
            
            if target_event:
                # Apply event-based transition
                update_data = {
                    "customFields": [{
                        "$type": "StateMachineIssueCustomField",
                        "name": "State",
                        "event": {
                            "$type": "Event",
                            "id": target_event.get('id')
                        }
                    }]
                }
                
                self.client.post(f"issues/{issue_id}", data=update_data)
                logger.info(f"Applied state machine event '{target_event.get('id')}' to issue {issue_id}")
                return True
            else:
                logger.warning(f"No suitable event found for state transition to '{target_state}'")
                return False
                    
        except Exception as e:
            logger.error(f"State machine transition failed: {e}")
            return False
    
    def _apply_direct_state_update(self, issue_id: str, target_state: str) -> bool:
        """
        Apply direct state field update using proven working format.
        
        Based on successful testing, the working format is:
        {"customFields": [{"name": "State", "value": "In Progress"}]}
        
        NOT complex objects or ID references.
        """
        try:
            # Use the proven simple string format that works
            update_data = {
                "customFields": [{
                    "name": "State",
                    "value": target_state  # Simple string value - this is what works!
                }]
            }
            
            logger.info(f"Applying direct state update to issue {issue_id}: State -> '{target_state}'")
            self.client.post(f"issues/{issue_id}", data=update_data)
            
            logger.info(f"Direct state update successful for issue {issue_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Direct state update failed for issue {issue_id}: {e}")
            return False
    
    def _update_other_custom_fields(self, issue_id: str, custom_fields: Dict[str, Any], validate: bool, use_commands: bool) -> None:
        """
        Update non-state custom fields, prioritizing direct field updates.
        
        Based on successful testing, uses simple values where possible:
        - Strings: "Critical", "admin", "Bug"  
        - NOT complex objects: {"name": "Critical", "id": "123"}
        
        Args:
            issue_id: Issue identifier
            custom_fields: Dictionary of field names and values
            validate: Whether to validate field values  
            use_commands: Whether to try command-based approach as fallback
        """
        # Method 1: Direct field update approach (primary method)
        try:
            # Always get issue data to extract project ID for schema lookups
            issue_data = self.get_issue(issue_id)
            
            # Validate fields if requested
            if validate:
                project_id = None
                if hasattr(issue_data, 'project') and issue_data.project:
                    if isinstance(issue_data.project, dict):
                        project_id = issue_data.project.get('id')
                    else:
                        project_id = getattr(issue_data.project, 'id', None)
                
                if project_id:
                    for field_name, field_value in custom_fields.items():
                        is_valid = self._validate_custom_field_value(project_id, field_name, field_value)
                        if not is_valid:
                            raise YouTrackAPIError(f"Custom field validation failed for '{field_name}': '{field_value}' is not a valid value")
                else:
                    logger.warning("Could not get project ID for validation, skipping validation")
            
            # YouTrack requires proper object types with actual IDs for custom field updates
            # Try to get project ID for schema lookups (optional for enhanced object creation)
            project_id = None
            
            if hasattr(issue_data, 'project') and issue_data.project:
                if isinstance(issue_data.project, dict):
                    project_id = issue_data.project.get('id')
                else:
                    project_id = getattr(issue_data.project, 'id', None)
            
            # If we can't get project ID, fall back to simple $type approach
            if not project_id:
                logger.warning("Could not determine project ID for enhanced object creation, using simple $type approach")
                use_simple_approach = True
            else:
                use_simple_approach = False
            
            update_data = {"customFields": []}
            
            for field_name, field_value in custom_fields.items():
                # Determine field type and construct proper object with actual ID
                if use_simple_approach:
                    # Fallback to simple $type approach when project ID is not available
                    if field_name.lower() in ['state']:
                        field_type = "StateIssueCustomField"
                    elif field_name.lower() in ['priority', 'type']:
                        field_type = "SingleEnumIssueCustomField"
                    elif field_name.lower() in ['assignee', 'reporter']:
                        field_type = "SingleUserIssueCustomField"
                    elif field_name.lower() in ['estimation', 'spent time']:
                        field_type = "PeriodIssueCustomField"
                    else:
                        field_type = "SingleEnumIssueCustomField"
                    
                    field_data = {
                        "$type": field_type,
                        "name": field_name,
                        "value": field_value
                    }
                else:
                    # Enhanced approach with proper YouTrack objects and actual IDs
                    # Handle Estimation with proper PeriodValue format
                    if field_name.lower() in ['estimation']:
                        # Estimation REQUIRES PeriodValue format, not simple strings
                        field_data = self._create_period_field_object(field_name, field_value)
                    elif field_name.lower() in ['state']:
                        field_data = self._create_state_field_object(project_id, field_name, field_value)
                    elif field_name.lower() in ['priority', 'type']:
                        field_data = self._create_enum_field_object(project_id, field_name, field_value)
                    elif field_name.lower() in ['assignee', 'reporter']:
                        field_data = self._create_user_field_object(field_name, field_value)
                    elif field_name.lower() in ['spent time']:
                        field_data = self._create_period_field_object(field_name, field_value)
                    else:
                        # Default to enum for unknown fields
                        field_data = self._create_enum_field_object(project_id, field_name, field_value)
                
                if field_data:
                    update_data["customFields"].append(field_data)
            
            logger.info(f"Updating custom fields for issue {issue_id} using proper YouTrack objects")
            logger.info(f"Update payload: {json.dumps(update_data, indent=2)}")
            self.client.post(f"issues/{issue_id}", data=update_data)
            logger.info(f"Direct field update succeeded for issue {issue_id}")
            
        except Exception as direct_error:
            logger.warning(f"Direct field update failed: {direct_error}")
            
            # Method 2: Fallback to command-based approach if enabled
            if use_commands:
                logger.info(f"Trying command-based approach as fallback for issue {issue_id}")
                try:
                    self._apply_commands_update(issue_id, custom_fields)
                    logger.info(f"Command-based update succeeded for issue {issue_id}")
                    return
                except Exception as cmd_error:
                    logger.warning(f"Command-based approach also failed: {cmd_error}")
            
            # If both direct and command approaches fail, raise the original error with full details
            error_msg = f"Direct field update failed"
            if hasattr(direct_error, 'response') and hasattr(direct_error.response, 'json'):
                try:
                    error_details = direct_error.response.json()
                    if 'error_description' in error_details:
                        error_msg += f": {error_details['error_description']}"
                    elif 'error' in error_details:
                        error_msg += f": {error_details['error']}"
                    else:
                        error_msg += f": {str(direct_error)}"
                except:
                    error_msg += f": {str(direct_error)}"
            else:
                error_msg += f": {str(direct_error)}"
            
            raise YouTrackAPIError(error_msg)

    def _create_enum_field_object(self, project_id: str, field_name: str, field_value: str) -> Dict[str, Any]:
        """Create proper EnumBundleElement object with actual ID."""
        try:
            # Get allowed values to find the actual ID
            from youtrack_mcp.api.projects import ProjectsClient
            projects_client = ProjectsClient(self.client)
            allowed_values = projects_client.get_custom_field_allowed_values(project_id, field_name)
            
            # Find the matching value by name (case-insensitive)
            value_id = None
            for value in allowed_values:
                if value.get('name', '').lower() == field_value.lower():
                    value_id = value.get('id')
                    break
            
            if value_id:
                return {
                    "$type": "SingleEnumIssueCustomField",
                    "name": field_name,
                    "value": {
                        "$type": "EnumBundleElement",
                        "id": value_id,
                        "name": field_value
                    }
                }
            else:
                logger.warning(f"Could not find ID for enum value '{field_value}' in field '{field_name}', using simple value")
                return {
                    "$type": "SingleEnumIssueCustomField",
                    "name": field_name,
                    "value": field_value
                }
        except Exception as e:
            logger.warning(f"Error creating enum field object for '{field_name}': {e}, using simple value")
            return {
                "$type": "SingleEnumIssueCustomField",
                "name": field_name,
                "value": field_value
            }

    def _create_state_field_object(self, project_id: str, field_name: str, field_value: str) -> Dict[str, Any]:
        """Create proper StateBundleElement object with actual ID."""
        try:
            # Get allowed values to find the actual ID
            from youtrack_mcp.api.projects import ProjectsClient
            projects_client = ProjectsClient(self.client)
            allowed_values = projects_client.get_custom_field_allowed_values(project_id, field_name)
            
            # Find the matching state by name (case-insensitive)
            state_id = None
            for value in allowed_values:
                if value.get('name', '').lower() == field_value.lower():
                    state_id = value.get('id')
                    break
            
            if state_id:
                return {
                    "$type": "StateIssueCustomField",
                    "name": field_name,
                    "value": {
                        "$type": "StateBundleElement",
                        "id": state_id,
                        "name": field_value
                    }
                }
            else:
                logger.warning(f"Could not find ID for state value '{field_value}' in field '{field_name}', using simple value")
                return {
                    "$type": "StateIssueCustomField",
                    "name": field_name,
                    "value": field_value
                }
        except Exception as e:
            logger.warning(f"Error creating state field object for '{field_name}': {e}, using simple value")
            return {
                "$type": "StateIssueCustomField",
                "name": field_name,
                "value": field_value
            }

    def _create_user_field_object(self, field_name: str, field_value: str) -> Dict[str, Any]:
        """Create proper User object with actual ID."""
        try:
            # Get user ID by login
            from youtrack_mcp.api.users import UsersClient
            users_client = UsersClient(self.client)
            user_data = users_client.get_user(field_value)
            
            if user_data and hasattr(user_data, 'id') and user_data.id:
                return {
                    "$type": "SingleUserIssueCustomField",
                    "name": field_name,
                    "value": {
                        "$type": "User",
                        "id": user_data.id,
                        "login": field_value
                    }
                }
            else:
                logger.warning(f"Could not find user ID for login '{field_value}', using simple value")
                return {
                    "$type": "SingleUserIssueCustomField",
                    "name": field_name,
                    "value": field_value
                }
        except Exception as e:
            logger.warning(f"Error creating user field object for '{field_name}': {e}, using simple value")
            return {
                "$type": "SingleUserIssueCustomField",
                "name": field_name,
                "value": field_value
            }

    def _create_period_field_object(self, field_name: str, field_value: str) -> Dict[str, Any]:
        """Create proper period field object with PeriodValue format."""
        try:
            # Convert simple time strings to proper PeriodValue format
            # Examples: "4h" -> 240 minutes, "30m" -> 30 minutes, "2h 30m" -> 150 minutes
            
            minutes = self._parse_time_to_minutes(field_value)
            
            if minutes is not None:
                return {
                    "$type": "PeriodIssueCustomField",
                    "name": field_name,
                    "value": {
                        "$type": "PeriodValue",
                        "minutes": minutes
                    }
                }
            else:
                # Fallback to simple value if parsing fails
                logger.warning(f"Could not parse period value '{field_value}' for field '{field_name}', using simple value")
                return {
                    "$type": "PeriodIssueCustomField",
                    "name": field_name,
                    "value": field_value
                }
        except Exception as e:
            logger.warning(f"Error creating period field object for '{field_name}': {e}, using simple value")
            return {
                "$type": "PeriodIssueCustomField",
                "name": field_name,
                "value": field_value
            }
    
    def _parse_time_to_minutes(self, time_str: str) -> Optional[int]:
        """Parse time string to minutes for PeriodValue."""
        try:
            time_str = time_str.strip().lower()
            total_minutes = 0
            
            # Handle formats like "4h", "30m", "2h 30m", "1h30m"
            
            # Extract hours
            hours_match = re.search(r'(\d+)\s*h', time_str)
            if hours_match:
                total_minutes += int(hours_match.group(1)) * 60
            
            # Extract minutes
            minutes_match = re.search(r'(\d+)\s*m', time_str)
            if minutes_match:
                total_minutes += int(minutes_match.group(1))
            
            # If no h or m found, assume it's just minutes
            if not hours_match and not minutes_match:
                # Try to parse as plain number (minutes)
                if time_str.isdigit():
                    total_minutes = int(time_str)
                else:
                    return None
            
            return total_minutes if total_minutes > 0 else None
            
        except Exception as e:
            logger.debug(f"Failed to parse time string '{time_str}': {e}")
            return None

    def _apply_commands_update(self, issue_id: str, custom_fields: Dict[str, Any]) -> None:
        """
        Apply custom field updates using the command-based approach.
        This method is a fallback and might not be as reliable as direct field updates.
        """
        try:
            command_data = {"query": "updateCustomFields"}
            for field_name, field_value in custom_fields.items():
                command_data["query"] += f" {field_name} {field_value}"
            
            command_data["issues"] = [{"id": issue_id}]
            
            logger.info(f"Applying command-based update for issue {issue_id} with query: {command_data['query']}")
            self.client.post("commands", data=command_data)
            logger.info(f"Command-based update succeeded for issue {issue_id}")
        except Exception as e:
            logger.warning(f"Command-based update failed: {e}")
            raise

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

    def _determine_field_type(self, field_name: str, value_type: str, bundle_type: str) -> str:
        """
        Determine the correct $type field for YouTrack custom field updates.
        
        Args:
            field_name: Name of the field
            value_type: Type from schema (enum, state, user, period, etc.)
            bundle_type: Bundle type from schema
            
        Returns:
            The appropriate $type string for the API
        """
        # Map field types to YouTrack $type values
        type_mapping = {
            "enum": "SingleEnumIssueCustomField",
            "state": "StateIssueCustomField", 
            "user": "SingleUserIssueCustomField",
            "period": "PeriodIssueCustomField",
            "ownedField": "SingleOwnedIssueCustomField",  # Subsystem
            "version": "SingleVersionIssueCustomField",   # Fix/Affected versions
            "build": "SingleBuildIssueCustomField",       # Fixed in build
            "string": "SingleStringIssueCustomField",
            "text": "TextIssueCustomField",
            "integer": "SingleIntegerIssueCustomField",
            "float": "SingleFloatIssueCustomField",
            "date": "SingleDateIssueCustomField",
            "datetime": "SingleDateTimeIssueCustomField"
        }
        
        # Get the appropriate type, defaulting to enum if not found
        field_type = type_mapping.get(value_type.lower(), "SingleEnumIssueCustomField")
        
        logger.debug(f"Field '{field_name}' (type: {value_type}, bundle: {bundle_type}) mapped to $type: {field_type}")
        
        return field_type
