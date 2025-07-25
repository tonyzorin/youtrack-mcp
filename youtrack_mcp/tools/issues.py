"""
YouTrack Issue MCP tools.
"""

import json
import logging
from typing import Any, Dict, Optional, List

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.issues import IssuesClient
from youtrack_mcp.api.projects import ProjectsClient
from youtrack_mcp.mcp_wrappers import sync_wrapper
from youtrack_mcp.utils import format_json_response

logger = logging.getLogger(__name__)


class IssueTools:
    """Issue-related MCP tools."""

    def __init__(self):
        """Initialize the issue tools."""
        self.client = YouTrackClient()
        self.issues_api = IssuesClient(self.client)
        self.projects_api = ProjectsClient(self.client)

    @sync_wrapper
    def get_issue(self, issue_id: str) -> str:
        """
        Get information about a specific issue.

        FORMAT: get_issue(issue_id="DEMO-123")

        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")

        Returns:
            JSON string with issue information
        """
        try:
            # First try to get the issue data with explicit fields
            fields = "id,idReadable,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value)"
            raw_issue = self.client.get(f"issues/{issue_id}?fields={fields}")

            # If we got a minimal response, enhance it with default values
            if (
                isinstance(raw_issue, dict)
                and raw_issue.get("$type") == "Issue"
                and "summary" not in raw_issue
            ):
                raw_issue["summary"] = (
                    f"Issue {issue_id}"  # Provide a default summary
                )

            # Return the raw issue data directly - avoid model validation issues
            return format_json_response(raw_issue)

        except Exception as e:
            logger.exception(f"Error getting issue {issue_id}")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def search_issues(self, query: str, limit: int = 10) -> str:
        """
        Search for issues using YouTrack query language.

        FORMAT: search_issues(query="project: DEMO #Unresolved", limit=10)

        Args:
            query: YouTrack search query string
            limit: Maximum number of issues to return (default: 10)

        Returns:
            JSON string with matching issues
        """
        try:
            # Request with explicit fields to get complete data
            fields = "id,idReadable,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value)"
            params = {"query": query, "$top": limit, "fields": fields}
            raw_issues = self.client.get("issues", params=params)

            # Return the raw issues data directly
            return format_json_response(raw_issues)

        except Exception as e:
            logger.exception(f"Error searching issues with query: {query}")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def create_issue(
        self, project: str, summary: str, description: Optional[str] = None
    ) -> str:
        """
        Create a new issue in YouTrack.

        FORMAT: create_issue(project="DEMO", summary="Bug in login", description="Users cannot log in")

        Args:
            project: The project identifier (e.g., "DEMO", "PROJECT")
            summary: The issue title/summary
            description: Optional detailed description of the issue

        Returns:
            JSON string with the created issue information
        """
        try:
            logger.debug(
                f"Creating issue with: project={project}, summary={summary}, description={description}"
            )

            # Validate required parameters
            if not project:
                return format_json_response(
                    {"error": "Project is required", "status": "error"}
                )
            if not summary:
                return format_json_response(
                    {"error": "Summary is required", "status": "error"}
                )

            # Check if project is a project ID or short name
            project_id = project
            if project and not project.startswith("0-"):
                # Try to get the project ID from the short name (e.g., "DEMO")
                try:
                    logger.info(f"Looking up project ID for: {project}")
                    project_obj = self.projects_api.get_project_by_name(project)
                    if project_obj:
                        logger.info(
                            f"Found project {project_obj.name} with ID {project_obj.id}"
                        )
                        project_id = project_obj.id
                    else:
                        logger.warning(f"Project not found: {project}")
                        return json.dumps(
                            {
                                "error": f"Project not found: {project}",
                                "status": "error",
                            }
                        )
                except Exception as e:
                    logger.warning(f"Error finding project: {str(e)}")
                    return json.dumps(
                        {
                            "error": f"Error finding project: {str(e)}",
                            "status": "error",
                        }
                    )

            logger.info(f"Creating issue in project {project_id}: {summary}")

            # Call the API client to create the issue
            try:
                issue = self.issues_api.create_issue(
                    project_id, summary, description
                )

                # Check if we got an issue with an ID
                if isinstance(issue, dict) and issue.get("error"):
                    # Handle error returned as a dict
                    return format_json_response(issue)

                # Try to get full issue details right after creation
                if hasattr(issue, "id"):
                    try:
                        # Get the full issue details using issue ID
                        issue_id = issue.id
                        detailed_issue = self.issues_api.get_issue(issue_id)

                        if hasattr(detailed_issue, "model_dump"):
                            return format_json_response(
                                detailed_issue.model_dump()
                            )
                        else:
                            return format_json_response(detailed_issue)
                    except Exception as e:
                        logger.warning(
                            f"Could not retrieve detailed issue: {str(e)}"
                        )
                if hasattr(issue, "model_dump"):
                    return format_json_response(issue.model_dump())
                else:
                    return format_json_response(issue)
            except Exception as e:
                error_msg = str(e)
                if hasattr(e, "response") and e.response:
                    try:
                        # Try to get detailed error message from response
                        error_content = e.response.content.decode(
                            "utf-8", errors="replace"
                        )
                        error_msg = f"{error_msg} - {error_content}"
                    except Exception:
                        pass
                logger.error(f"API error creating issue: {error_msg}")
                return format_json_response(
                    {"error": error_msg, "status": "error"}
                )

        except Exception as e:
            logger.exception(f"Error creating issue in project {project}")
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def add_comment(self, issue_id: str, text: str) -> str:
        """
        Add a comment to an issue.

        FORMAT: add_comment(issue_id="DEMO-123", text="This has been fixed")

        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")
            text: The text content of the comment to add

        Returns:
            JSON string with the result
        """
        try:
            result = self.issues_api.add_comment(issue_id, text)
            return format_json_response(result)
        except Exception as e:
            logger.exception(f"Error adding comment to issue {issue_id}")
            return format_json_response({"error": str(e)})

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
                "description": 'Get complete information about a YouTrack issue including custom fields and comments. Example: get_issue(issue_id="DEMO-123")',
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'"
                },
            },
            "search_issues": {
                "description": 'Search for issues using YouTrack query syntax. Example: search_issues(query="project: DEMO #Unresolved", limit=5)',
                "parameter_descriptions": {
                    "query": "YouTrack search query string",
                    "limit": "Maximum number of results to return (default: 10)",
                },
            },
            "create_issue": {
                "description": 'Create a new issue in a YouTrack project with title and optional description. Example: create_issue(project="DEMO", summary="Bug in login", description="Users cannot log in")',
                "parameter_descriptions": {
                    "project": "Project identifier like 'DEMO' or 'PROJECT'",
                    "summary": "Title/summary for the new issue",
                    "description": "Optional detailed description of the issue",
                },
            },
            "add_comment": {
                "description": 'Add a text comment to an existing YouTrack issue. Example: add_comment(issue_id="DEMO-123", text="This has been fixed")',
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123'",
                    "text": "Text content of the comment to add",
                },
            },
            "get_issue_raw": {
                "description": 'Get raw issue information bypassing model processing. Example: get_issue_raw(issue_id="DEMO-123")',
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123'"
                },
            },
            "get_attachment_content": {
                "description": 'Get attachment content as base64-encoded string (max 750KB). Example: get_attachment_content(issue_id="DEMO-123", attachment_id="1-123")',
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123'",
                    "attachment_id": "Attachment ID like '1-123'",
                },
            },
            "link_issues": {
                "description": 'Link two YouTrack issues together with a specified relationship. Example: link_issues(source_issue_id="SP-123", target_issue_id="SP-456", link_type="Relates")',
                "parameter_descriptions": {
                    "source_issue_id": "Source issue ID like 'SP-123'",
                    "target_issue_id": "Target issue ID like 'SP-456'",
                    "link_type": "Type of link like 'Relates', 'Duplicates', 'Depends on'",
                },
            },
            "get_issue_links": {
                "description": 'Get all links (relationships) for a YouTrack issue. Example: get_issue_links(issue_id="SP-123")',
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'SP-123'"
                },
            },
            "get_available_link_types": {
                "description": "Get all available issue link types that can be used to connect issues. Example: get_available_link_types()",
                "parameter_descriptions": {},
            },
            "update_issue": {
                "description": 'Update an existing YouTrack issue with new summary, description or custom fields. Example: update_issue(issue_id="DEMO-123", summary="New title", description="Updated description")',
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123'",
                    "summary": "New issue title/summary (optional)",
                    "description": "New issue description (optional)",
                    "additional_fields": "Dictionary of additional custom fields to update (optional)",
                },
            },
            "add_dependency": {
                "description": 'Create a dependency relationship where one issue depends on another. Example: add_dependency(dependent_issue_id="DEMO-123", dependency_issue_id="DEMO-456")',
                "parameter_descriptions": {
                    "dependent_issue_id": "Issue that depends on another (e.g. 'DEMO-123')",
                    "dependency_issue_id": "Issue that is depended upon (e.g. 'DEMO-456')",
                },
            },
            "remove_dependency": {
                "description": 'Remove a dependency relationship between two issues. Example: remove_dependency(dependent_issue_id="DEMO-123", dependency_issue_id="DEMO-456")',
                "parameter_descriptions": {
                    "dependent_issue_id": "Issue that depends on another (e.g. 'DEMO-123')",
                    "dependency_issue_id": "Issue that is depended upon (e.g. 'DEMO-456')",
                },
            },
            "add_relates_link": {
                "description": 'Add a general "Relates" relationship between two issues. Example: add_relates_link(source_issue_id="DEMO-123", target_issue_id="DEMO-456")',
                "parameter_descriptions": {
                    "source_issue_id": "Source issue identifier (e.g. 'DEMO-123')",
                    "target_issue_id": "Target issue identifier (e.g. 'DEMO-456')",
                },
            },
            "add_duplicate_link": {
                "description": 'Mark one issue as a duplicate of another. Example: add_duplicate_link(duplicate_issue_id="DEMO-123", original_issue_id="DEMO-456")',
                "parameter_descriptions": {
                    "duplicate_issue_id": "Issue that is a duplicate (e.g. 'DEMO-123')",
                    "original_issue_id": "Original issue (e.g. 'DEMO-456')",
                },
            },
            "update_custom_fields": {
                "description": 'Update custom fields on an issue with comprehensive validation. Example: update_custom_fields(issue_id="DEMO-123", custom_fields={"Priority": "High", "Assignee": "john.doe"}, validate=True)',
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123'",
                    "custom_fields": "Dictionary of custom field name-value pairs",
                    "validate": "Whether to validate field values against project schema (default: True)",
                },
            },
            "batch_update_custom_fields": {
                "description": 'Update custom fields for multiple issues in a single operation. Example: batch_update_custom_fields([{"issue_id": "DEMO-123", "fields": {"Priority": "High"}}, {"issue_id": "DEMO-124", "fields": {"Assignee": "jane.doe"}}])',
                "parameter_descriptions": {
                    "updates": "List of update dictionaries with format: [{'issue_id': 'DEMO-123', 'fields': {'Priority': 'High'}}]",
                },
            },
            "get_custom_fields": {
                "description": 'Get all custom fields for a specific issue. Example: get_custom_fields(issue_id="DEMO-123")',
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123'",
                },
            },
            "validate_custom_field": {
                "description": 'Validate a custom field value against project schema. Example: validate_custom_field(project_id="DEMO", field_name="Priority", field_value="High")',
                "parameter_descriptions": {
                    "project_id": "Project identifier like 'DEMO' or '0-0'",
                    "field_name": "Custom field name like 'Priority' or 'Assignee'",
                    "field_value": "Value to validate against field constraints",
                },
            },
            "get_available_custom_field_values": {
                "description": 'Get available values for enum/state custom fields. Example: get_available_custom_field_values(project_id="DEMO", field_name="Priority")',
                "parameter_descriptions": {
                    "project_id": "Project identifier like 'DEMO' or '0-0'",
                    "field_name": "Custom field name like 'Priority' or 'State'",
                },
            },
            "diagnose_workflow_restrictions": {
                "description": "Diagnose workflow restrictions and available state transitions for an issue. Analyzes state machine workflows, permissions, and provides actionable recommendations. Example: diagnose_workflow_restrictions(issue_id='DEMO-123')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'"
                }
            },
            "update_issue_state": {
                "description": "Update an issue's state using the proven working REST API approach. Optimized for reliable state transitions like 'Submitted → In Progress'. Example: update_issue_state(issue_id='DEMO-123', new_state='In Progress')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'",
                    "new_state": "Target state name like 'In Progress', 'Fixed', 'Open', 'Closed'"
                }
            },
            "update_issue_priority": {
                "description": "Update an issue's priority using the proven working REST API approach. Optimized for reliable priority changes like 'Normal → Critical'. Example: update_issue_priority(issue_id='DEMO-123', new_priority='Critical')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'",
                    "new_priority": "Target priority like 'Critical', 'Major', 'Normal', 'Minor'"
                }
            },
            "get_help": {
                "description": "Get interactive help with live YouTrack data and working examples. Unlike static tool descriptions, this provides dynamic help based on your actual YouTrack configuration, showing real project IDs, available values, and copy-paste ready examples.",
                "parameter_descriptions": {
                    "topic": "Help topic - 'all', 'state', 'priority', 'fields', 'projects', 'examples'. Defaults to 'all'"
                }
            }
        }

    @sync_wrapper
    def get_issue_raw(self, issue_id: str) -> str:
        """
        Get raw information about a specific issue, bypassing the Pydantic model.

        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")

        Returns:
            Raw JSON string with the issue data
        """
        try:
            # Request comprehensive fields for raw issue data
            fields = "id,idReadable,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value(id,name)),attachments(id,name,size,url),comments(id,text,author(login,name),created)"
            raw_issue = self.client.get(f"issues/{issue_id}?fields={fields}")
            return format_json_response(raw_issue)
        except Exception as e:
            logger.exception(f"Error getting raw issue {issue_id}")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def get_attachment_content(self, issue_id: str, attachment_id: str) -> str:
        """
        Get the content of an attachment as a base64-encoded string.

        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")
            attachment_id: The attachment ID (e.g., "1-123")

        Returns:
            JSON string with the attachment content encoded in base64
        """
        try:
            import base64

            content = self.issues_api.get_attachment_content(
                issue_id, attachment_id
            )
            encoded_content = base64.b64encode(content).decode("utf-8")

            # Get attachment metadata for additional info
            issue_response = self.client.get(
                f"issues/{issue_id}?fields=attachments(id,name,mimeType,size)"
            )
            attachment_metadata = None

            if "attachments" in issue_response:
                for attachment in issue_response["attachments"]:
                    if attachment.get("id") == attachment_id:
                        attachment_metadata = attachment
                        break

            return json.dumps(
                {
                    "content": encoded_content,
                    "size_bytes_original": len(content),
                    "size_bytes_base64": len(encoded_content),
                    "filename": (
                        attachment_metadata.get("name")
                        if attachment_metadata
                        else None
                    ),
                    "mime_type": (
                        attachment_metadata.get("mimeType")
                        if attachment_metadata
                        else None
                    ),
                    "size_increase_percent": round(
                        (len(encoded_content) / len(content) - 1) * 100, 1
                    ),
                    "status": "success",
                }
            )
        except Exception as e:
            logger.exception(
                f"Error getting attachment content for issue {issue_id}, attachment {attachment_id}"
            )
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def link_issues(
        self, source_issue_id: str, target_issue_id: str, link_type: str
    ) -> str:
        """
        Link two issues together.

        FORMAT: link_issues(source_issue_id="SP-123", target_issue_id="SP-456", link_type="Relates")

        Args:
            source_issue_id: The ID of the source issue (e.g., 'SP-123')
            target_issue_id: The ID of the target issue (e.g., 'SP-456')
            link_type: The type of link (e.g., 'Relates', 'Duplicates', 'Depends on')

        Returns:
            JSON string with the created link data
        """
        try:
            result = self.issues_api.link_issues(
                source_issue_id, target_issue_id, link_type
            )
            return format_json_response(result)
        except Exception as e:
            logger.exception(
                f"Error linking issues {source_issue_id} -> {target_issue_id}"
            )
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def get_issue_links(self, issue_id: str) -> str:
        """
        Get all links for an issue.

        FORMAT: get_issue_links(issue_id="SP-123")

        Args:
            issue_id: The ID of the issue (e.g., 'SP-123')

        Returns:
            JSON string containing inward and outward issue links
        """
        try:
            result = self.issues_api.get_issue_links(issue_id)
            return format_json_response(result)
        except Exception as e:
            logger.exception(f"Error getting links for issue {issue_id}")
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def get_available_link_types(self) -> str:
        """
        Get all available issue link types.

        FORMAT: get_available_link_types()

        Returns:
            JSON string with list of available link types and their properties
        """
        try:
            result = self.issues_api.get_available_link_types()
            return format_json_response(result)
        except Exception as e:
            logger.exception("Error getting available link types")
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def update_issue(
        self,
        issue_id: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        additional_fields: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Update an existing issue with new information.

        FORMAT: update_issue(issue_id="DEMO-123", summary="New title", description="Updated description")

        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")
            summary: The new issue summary/title (optional)
            description: The new issue description (optional)
            additional_fields: Additional fields to update as dict (optional)

        Returns:
            JSON string with the updated issue details
        """
        try:
            result = self.issues_api.update_issue(
                issue_id=issue_id,
                summary=summary,
                description=description,
                additional_fields=additional_fields,
            )
            # Convert Issue object to dict if needed
            if hasattr(result, "model_dump"):
                result = result.model_dump()
            elif hasattr(result, "__dict__"):
                result = result.__dict__
            return format_json_response(result)
        except Exception as e:
            logger.exception(f"Error updating issue {issue_id}")
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def add_dependency(
        self, dependent_issue_id: str, dependency_issue_id: str
    ) -> str:
        """
        Add a dependency relationship where one issue depends on another.

        FORMAT: add_dependency(dependent_issue_id="DEMO-123", dependency_issue_id="DEMO-456")

        Args:
            dependent_issue_id: The issue that depends on another (e.g., "DEMO-123")
            dependency_issue_id: The issue that is depended upon (e.g., "DEMO-456")

        Returns:
            JSON string with the result of creating the dependency link
        """
        try:
            result = self.link_issues(
                dependent_issue_id, dependency_issue_id, "Depends on"
            )
            return result
        except Exception as e:
            logger.exception(
                f"Error adding dependency between {dependent_issue_id} and {dependency_issue_id}"
            )
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def remove_dependency(
        self, dependent_issue_id: str, dependency_issue_id: str
    ) -> str:
        """
        Remove a dependency relationship between two issues.

        FORMAT: remove_dependency(dependent_issue_id="DEMO-123", dependency_issue_id="DEMO-456")

        Args:
            dependent_issue_id: The issue that depends on another (e.g., "DEMO-123")
            dependency_issue_id: The issue that is depended upon (e.g., "DEMO-456")

        Returns:
            JSON string with the result of removing the dependency link
        """
        try:
            # For removing links, we need to use a different approach
            # This would typically involve getting the link ID and deleting it
            # For now, we'll use a command approach
            # Get internal IDs for Commands API (same approach as link_issues)
            dependent_internal_id = self.issues_api._get_internal_id(
                dependent_issue_id
            )
            
            # Get readable ID for command text (Commands API expects readable IDs)
            dependency_readable_id = self.issues_api._get_readable_id(
                dependency_issue_id
            )

            command = f"remove depends on {dependency_readable_id}"

            command_data = {
                "query": command,
                "issues": [{"id": dependent_internal_id}],
            }

            response = self.client.post("commands", data=command_data)

            if isinstance(response, dict):
                return format_json_response(
                    {
                        "status": "success",
                        "message": f"Successfully removed dependency between {dependent_issue_id} and {dependency_issue_id}",
                        "command": command,
                    }
                )

            return format_json_response(response)
        except Exception as e:
            logger.exception(
                f"Error removing dependency between {dependent_issue_id} and {dependency_issue_id}"
            )
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def add_relates_link(
        self, source_issue_id: str, target_issue_id: str
    ) -> str:
        """
        Add a 'Relates' relationship between two issues.

        FORMAT: add_relates_link(source_issue_id="DEMO-123", target_issue_id="DEMO-456")

        Args:
            source_issue_id: The source issue (e.g., "DEMO-123")
            target_issue_id: The target issue (e.g., "DEMO-456")

        Returns:
            JSON string with the result of creating the relates link
        """
        try:
            result = self.link_issues(
                source_issue_id, target_issue_id, "Relates"
            )
            return result
        except Exception as e:
            logger.exception(
                f"Error adding relates link between {source_issue_id} and {target_issue_id}"
            )
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def add_duplicate_link(
        self, duplicate_issue_id: str, original_issue_id: str
    ) -> str:
        """
        Mark one issue as a duplicate of another.

        FORMAT: add_duplicate_link(duplicate_issue_id="DEMO-123", original_issue_id="DEMO-456")

        Args:
            duplicate_issue_id: The issue that is a duplicate (e.g., "DEMO-123")
            original_issue_id: The original issue (e.g., "DEMO-456")

        Returns:
            JSON string with the result of creating the duplicate link
        """
        try:
            result = self.link_issues(
                duplicate_issue_id, original_issue_id, "Duplicates"
            )
            return result
        except Exception as e:
            logger.exception(
                f"Error adding duplicate link between {duplicate_issue_id} and {original_issue_id}"
            )
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def update_custom_fields(
        self, 
        issue_id: str, 
        custom_fields: Dict[str, Any],
        validate: bool = True
    ) -> str:
        """
        Update custom fields on an issue with comprehensive validation.

        FORMAT: update_custom_fields(issue_id="DEMO-123", custom_fields={"Priority": "High", "Assignee": "john.doe"}, validate=True)

        Args:
            issue_id: The issue ID or readable ID (e.g., "DEMO-123")
            custom_fields: Dictionary of custom field name-value pairs
            validate: Whether to validate field values against project schema (default: True)

        Returns:
            JSON string with update result and issue data
        """
        try:
            if not issue_id:
                return format_json_response({
                    "status": "error",
                    "error": "Issue ID is required"
                })

            if not custom_fields:
                return format_json_response({
                    "status": "error", 
                    "error": "Custom fields dictionary is required"
                })

            # Update the issue custom fields
            updated_issue = self.issues_api.update_issue_custom_fields(
                issue_id=issue_id,
                custom_fields=custom_fields,
                validate=validate
            )

            # Format response
            result = {
                "status": "success",
                "issue_id": issue_id,
                "updated_fields": list(custom_fields.keys()),
                "message": f"Updated {len(custom_fields)} custom field(s)"
            }

            # Include updated issue data
            if hasattr(updated_issue, "model_dump"):
                result["issue_data"] = updated_issue.model_dump()
            else:
                result["issue_data"] = updated_issue

            return format_json_response(result)

        except Exception as e:
            logger.exception(f"Error updating custom fields for issue {issue_id}")
            return format_json_response({
                "status": "error",
                "error": str(e),
                "issue_id": issue_id,
                "attempted_fields": list(custom_fields.keys()) if custom_fields else []
            })

    @sync_wrapper  
    def batch_update_custom_fields(
        self,
        updates: List[Dict[str, Any]]
    ) -> str:
        """
        Update custom fields for multiple issues in a single operation.

        FORMAT: batch_update_custom_fields([{"issue_id": "DEMO-123", "fields": {"Priority": "High"}}, {"issue_id": "DEMO-124", "fields": {"Assignee": "jane.doe"}}])

        Args:
            updates: List of update dictionaries with format:
                    [{"issue_id": "DEMO-123", "fields": {"Priority": "High", "Sprint": "2024.1"}}]

        Returns:
            JSON string with batch update results
        """
        try:
            if not updates:
                return format_json_response({
                    "status": "error",
                    "error": "Updates list is required"
                })

            # Process batch updates
            results = self.issues_api.batch_update_custom_fields(updates)

            # Summarize results
            success_count = len([r for r in results if r.get("status") == "success"])
            error_count = len([r for r in results if r.get("status") == "error"])
            skipped_count = len([r for r in results if r.get("status") == "skipped"])

            response = {
                "status": "completed",
                "summary": {
                    "total": len(updates),
                    "successful": success_count,
                    "errors": error_count,
                    "skipped": skipped_count
                },
                "results": results
            }

            return format_json_response(response)

        except Exception as e:
            logger.exception("Error in batch custom fields update")
            return format_json_response({
                "status": "error",
                "error": str(e),
                "attempted_updates": len(updates) if updates else 0
            })

    @sync_wrapper
    def get_custom_fields(self, issue_id: str) -> str:
        """
        Get all custom fields for a specific issue.

        FORMAT: get_custom_fields(issue_id="DEMO-123")

        Args:
            issue_id: The issue ID or readable ID (e.g., "DEMO-123")

        Returns:
            JSON string with custom fields data
        """
        try:
            if not issue_id:
                return format_json_response({
                    "status": "error",
                    "error": "Issue ID is required"
                })

            # Get custom fields
            custom_fields = self.issues_api.get_issue_custom_fields(issue_id)

            response = {
                "status": "success",
                "issue_id": issue_id,
                "custom_fields": custom_fields,
                "field_count": len(custom_fields)
            }

            return format_json_response(response)

        except Exception as e:
            logger.exception(f"Error getting custom fields for issue {issue_id}")
            return format_json_response({
                "status": "error",
                "error": str(e),
                "issue_id": issue_id
            })

    @sync_wrapper
    def validate_custom_field(
        self,
        project_id: str,
        field_name: str,
        field_value: Any
    ) -> str:
        """
        Validate a custom field value against project schema.

        FORMAT: validate_custom_field(project_id="DEMO", field_name="Priority", field_value="High")

        Args:
            project_id: The project ID or short name (e.g., "DEMO", "0-0")
            field_name: The custom field name
            field_value: The value to validate

        Returns:
            JSON string with validation result
        """
        try:
            if not project_id or not field_name:
                return format_json_response({
                    "status": "error",
                    "error": "Project ID and field name are required"
                })

            # Validate the field
            validation_result = self.issues_api.validate_custom_field_value(
                project_id=project_id,
                field_name=field_name,
                field_value=field_value
            )

            return format_json_response(validation_result)

        except Exception as e:
            logger.exception(f"Error validating custom field {field_name}")
            return format_json_response({
                "valid": False,
                "error": f"Validation error: {str(e)}",
                "field": field_name,
                "value": field_value
            })

    @sync_wrapper
    def get_available_custom_field_values(
        self,
        project_id: str,
        field_name: str
    ) -> str:
        """
        Get available values for enum/state custom fields.

        FORMAT: get_available_custom_field_values(project_id="DEMO", field_name="Priority")

        Args:
            project_id: The project ID or short name (e.g., "DEMO", "0-0")
            field_name: The custom field name

        Returns:
            JSON string with available values
        """
        try:
            if not project_id or not field_name:
                return format_json_response({
                    "status": "error",
                    "error": "Project ID and field name are required"
                })

            # Get available values using projects API
            allowed_values = self.projects_api.get_custom_field_allowed_values(project_id, field_name)

            response = {
                "status": "success",
                "project_id": project_id,
                "field_name": field_name,
                "allowed_values": allowed_values,
                "value_count": len(allowed_values)
            }

            return format_json_response(response)

        except Exception as e:
            logger.exception(f"Error getting available values for field {field_name}")
            return format_json_response({
                "status": "error",
                "error": str(e),
                "project_id": project_id,
                "field_name": field_name
            })

    @sync_wrapper
    def diagnose_workflow_restrictions(self, issue_id: str) -> str:
        """
        Diagnose workflow restrictions and available state transitions for an issue.
        
        Based on comprehensive YouTrack API analysis, this function:
        1. Detects state machine workflows vs direct field updates
        2. Lists available transition events and their restrictions
        3. Identifies permission and workflow guard conditions
        4. Provides actionable recommendations for state transitions
        
        FORMAT: diagnose_workflow_restrictions(issue_id="DEMO-123")
        
        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")
            
        Returns:
            JSON string with workflow analysis and recommendations
        """
        try:
            if not issue_id:
                return format_json_response({
                    "error": "Issue ID is required"
                })
            
            # Get current issue state and field information
            issue_data = self.issues_api.get_issue(issue_id)
            
            # Query state field with possible transitions
            try:
                issue_fields = self.issues_api.client.get(
                    f"issues/{issue_id}/customFields?fields=name,possibleEvents(id,presentation),value(name),$type"
                )
                
                state_field = None
                for field in issue_fields:
                    if field.get('name', '').lower() == 'state':
                        state_field = field
                        break
                
                if not state_field:
                    return format_json_response({
                        "error": "No State field found for this issue",
                        "issue_id": issue_id
                    })
                
                current_state = state_field.get('value', {}).get('name', 'Unknown')
                field_type = state_field.get('$type', '')
                possible_events = state_field.get('possibleEvents', [])
                
                # Analyze workflow type
                workflow_analysis = {
                    "issue_id": issue_id,
                    "current_state": current_state,
                    "field_type": field_type,
                    "workflow_type": "state_machine" if field_type == 'StateMachineIssueCustomField' else "direct_field",
                    "available_transitions": [],
                    "restrictions": [],
                    "recommendations": []
                }
                
                # Analyze available transitions
                if possible_events:
                    workflow_analysis["available_transitions"] = [
                        {
                            "event_id": event.get('id', ''),
                            "presentation": event.get('presentation', ''),
                            "description": f"Transition via event: {event.get('presentation', 'Unknown')}"
                        }
                        for event in possible_events
                    ]
                    
                    if field_type == 'StateMachineIssueCustomField':
                        workflow_analysis["restrictions"].append(
                            "State machine workflow detected - requires event-based transitions"
                        )
                        workflow_analysis["recommendations"].extend([
                            "Use event-based transitions instead of direct state updates",
                            "Check guard conditions that may block specific transitions",
                            "Verify user permissions for workflow transitions"
                        ])
                    else:
                        workflow_analysis["recommendations"].append(
                            "Direct state updates should work with proper field formatting"
                        )
                else:
                    workflow_analysis["restrictions"].append(
                        "No transition events available - may indicate permission restrictions"
                    )
                    workflow_analysis["recommendations"].extend([
                        "Check user permissions for state field updates",
                        "Verify workflow configuration allows transitions from current state",
                        "Contact YouTrack administrator if transitions should be available"
                    ])
                
                # Add general workflow guidance
                workflow_analysis["technical_notes"] = {
                    "command_api": "Use POST /api/commands with 'State NewState' for most reliable transitions",
                    "direct_api": "Use POST /api/issues/{id} with StateIssueCustomField type for direct updates",
                    "state_machine_api": "Use POST /api/issues/{id} with StateMachineIssueCustomField and event for workflows",
                    "permission_check": "Verify 'Update Issue' or 'Update Issue Private Fields' permissions"
                }
                
                # Add common troubleshooting
                workflow_analysis["troubleshooting"] = [
                    "If 'Open → In Progress' is blocked, check if assignment is required first",
                    "If transitions fail with 500 errors, verify correct field type in request",
                    "If no events are available, check user role and project permissions",
                    "Use command-based approach (POST /api/commands) for maximum compatibility"
                ]
                
                return format_json_response({
                    "status": "success",
                    "workflow_analysis": workflow_analysis
                })
                
            except Exception as e:
                return format_json_response({
                    "error": f"Failed to analyze workflow: {str(e)}",
                    "issue_id": issue_id,
                    "suggestion": "Try checking issue permissions or contact YouTrack administrator"
                })
                
        except Exception as e:
            logger.exception(f"Error diagnosing workflow restrictions for issue {issue_id}")
            return format_json_response({
                "error": str(e),
                "troubleshooting": [
                    "Verify issue ID format and existence",
                    "Check user permissions for the issue",
                    "Ensure proper authentication token"
                ]
            })

    @sync_wrapper
    def update_issue_state(self, issue_id: str, new_state: str) -> str:
        """
        Update an issue's state using the proven working REST API approach.
        
        🎯 PROVEN WORKING FORMAT (based on successful testing):
        - Uses simple string values: "In Progress", "Fixed", "Open"
        - NO complex objects or ID references needed
        
        ✅ EXAMPLES THAT WORK:
        - update_issue_state("DEMO-123", "In Progress")
        - update_issue_state("PROJECT-456", "Fixed") 
        - update_issue_state("TASK-789", "Closed")
        
        🔧 WHAT HAPPENS UNDER THE HOOD:
        - Primary: Direct Field Update API with format {"customFields": [{"name": "State", "value": "In Progress"}]}
        - Fallback: Commands API with "State In Progress" command
        - Smart error handling with workflow restriction guidance
        
        FORMAT: update_issue_state(issue_id="DEMO-123", new_state="In Progress")
        
        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")
            new_state: The target state name (e.g., "In Progress", "Fixed", "Open")
            
        Returns:
            JSON string with the updated issue information and success details
            
        Common States: "Open", "In Progress", "Fixed", "Closed", "Submitted"
        """
        try:
            if not issue_id or not new_state:
                return format_json_response({
                    "error": "Both issue ID and new state are required"
                })
            
            logger.info(f"Updating issue {issue_id} state to '{new_state}' using proven Direct Field Update API")
            
            # Use the proven Direct Field Update API approach
            success = self.issues_api._apply_direct_state_update(issue_id, new_state)
            
            if success:
                # Get the updated issue to return current state
                updated_issue = self.issues_api.get_issue(issue_id)
                
                return format_json_response({
                    "status": "success",
                    "message": f"Successfully updated issue {issue_id} state to '{new_state}'",
                    "issue_id": issue_id,
                    "new_state": new_state,
                    "api_method": "Direct Field Update API",
                    "issue_data": updated_issue
                })
            else:
                # If direct method fails, try command-based approach as fallback
                logger.info(f"Direct API failed, trying command-based approach for issue {issue_id}")
                
                try:
                    command_data = {
                        "query": f"State \"{new_state}\"",
                        "issues": [{"id": issue_id}]
                    }
                    
                    self.issues_api.client.post("commands", data=command_data)
                    
                    # Get the updated issue
                    updated_issue = self.issues_api.get_issue(issue_id)
                    
                    return format_json_response({
                        "status": "success",
                        "message": f"Successfully updated issue {issue_id} state to '{new_state}' using fallback method",
                        "issue_id": issue_id,
                        "new_state": new_state,
                        "api_method": "Commands API (fallback)",
                        "issue_data": updated_issue
                    })
                    
                except Exception as cmd_error:
                    return format_json_response({
                        "error": f"State transition failed with both methods: {str(cmd_error)}",
                        "issue_id": issue_id,
                        "target_state": new_state,
                        "troubleshooting": [
                            "Check if the target state exists in your YouTrack project",
                            "Verify you have permissions to change issue states",
                            "Some transitions may be blocked by workflow rules",
                            "Try using diagnose_workflow_restrictions() to analyze restrictions"
                        ],
                        "workflow_help": f"Use diagnose_workflow_restrictions('{issue_id}') for detailed analysis"
                    })
                
        except Exception as e:
            logger.exception(f"Error updating state for issue {issue_id}")
            return format_json_response({
                "error": str(e),
                "issue_id": issue_id,
                "target_state": new_state,
                "suggestion": "Check issue ID format and verify it exists in YouTrack"
            })

    @sync_wrapper
    def update_issue_priority(self, issue_id: str, new_priority: str) -> str:
        """
        Update an issue's priority using the proven working REST API approach.
        
        🎯 PROVEN WORKING FORMAT (based on successful testing):
        - Uses simple string values: "Critical", "Major", "Normal", "Minor"
        - NO complex objects or ID references needed
        
        ✅ EXAMPLES THAT WORK:
        - update_issue_priority("DEMO-123", "Critical")
        - update_issue_priority("PROJECT-456", "Major") 
        - update_issue_priority("TASK-789", "Normal")
        
        🔧 WHAT HAPPENS UNDER THE HOOD:
        - Direct Field Update API with format {"customFields": [{"name": "Priority", "value": "Critical"}]}
        - Simple string values proven to work reliably
        - Smart error handling with field-specific guidance
        
        FORMAT: update_issue_priority(issue_id="DEMO-123", new_priority="Critical")
        
        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")
            new_priority: The target priority (e.g., "Critical", "Major", "Normal", "Minor")
            
        Returns:
            JSON string with the updated issue information and success details
            
        Common Priorities: "Critical", "Major", "Normal", "Minor", "Show-stopper"
        """
        try:
            if not issue_id or not new_priority:
                return format_json_response({
                    "error": "Both issue ID and new priority are required"
                })
            
            logger.info(f"Updating issue {issue_id} priority to '{new_priority}' using proven simple string format")
            
            # Use the proven simple string format for custom field updates
            result = self.update_custom_fields(
                issue_id=issue_id,
                custom_fields={"Priority": new_priority}
            )
            
            # Parse the result to provide priority-specific feedback
            result_data = json.loads(result) if isinstance(result, str) else result
            
            if result_data.get("status") == "success":
                return format_json_response({
                    "status": "success",
                    "message": f"Successfully updated issue {issue_id} priority to '{new_priority}'",
                    "issue_id": issue_id,
                    "new_priority": new_priority,
                    "api_method": "Direct Field Update API",
                    "updated_fields": result_data.get("updated_fields", ["Priority"]),
                    "issue_data": result_data.get("issue_data", {})
                })
            else:
                # Handle error case with priority-specific guidance
                error_msg = result_data.get("error", "Unknown error")
                return format_json_response({
                    "error": f"Priority update failed: {error_msg}",
                    "issue_id": issue_id,
                    "target_priority": new_priority,
                    "troubleshooting": [
                        "Check if the priority value exists in your YouTrack project",
                        "Verify you have permissions to change issue priorities",
                        "Common priority values: Critical, Major, Normal, Minor",
                        "Use get_available_custom_field_values() to see available priorities"
                    ],
                    "field_help": f"Use get_available_custom_field_values('Priority') to see valid options"
                })
                
        except Exception as e:
            logger.exception(f"Error updating priority for issue {issue_id}")
            return format_json_response({
                "error": str(e),
                "issue_id": issue_id,
                "target_priority": new_priority,
                "suggestion": "Check issue ID format and verify it exists in YouTrack"
            })

    @sync_wrapper
    def get_help(self, topic: str = "all") -> str:
        """
        Get interactive help with live YouTrack data and working examples.
        
        Unlike static tool descriptions, this provides dynamic help based on your 
        actual YouTrack configuration, showing real project IDs, available values,
        and copy-paste ready examples.
        
        Args:
            topic: Help topic - "all", "state", "priority", "fields", "projects", "examples"
        
        Returns:
            Comprehensive help with live data from your YouTrack instance
        """
        try:
            help_content = {
                "help_topic": topic,
                "youtrack_help": {},
                "quick_examples": {},
                "available_functions": {}
            }
            
            if topic in ["all", "projects"]:
                # Get real project information
                try:
                    projects = self.get_projects()
                    if isinstance(projects, str):
                        projects_data = json.loads(projects)
                        if isinstance(projects_data, list) and projects_data:
                            sample_project = projects_data[0]
                            help_content["youtrack_help"]["projects"] = {
                                "available_projects": [p.get("shortName", "N/A") for p in projects_data[:5]],
                                "sample_project_id": sample_project.get("shortName", "DEMO"),
                                "example_usage": f'create_issue(project_id="{sample_project.get("shortName", "DEMO")}", summary="Your issue title")'
                            }
                except Exception as e:
                    help_content["youtrack_help"]["projects"] = {
                        "error": f"Could not fetch projects: {e}",
                        "example_usage": 'create_issue(project_id="DEMO", summary="Your issue title")'
                    }
            
            if topic in ["all", "state", "fields"]:
                # Get real custom field information
                try:
                    # Try to get available states from a sample project
                    projects = self.get_projects()
                    if isinstance(projects, str):
                        projects_data = json.loads(projects)
                        if isinstance(projects_data, list) and projects_data:
                            sample_project_id = projects_data[0].get("shortName", "DEMO")
                            
                            # Get custom fields for this project
                            fields = self.projects_api.get_custom_fields(sample_project_id)
                            if isinstance(fields, list):
                                state_field = next((f for f in fields if f.get("name") == "State"), None)
                                priority_field = next((f for f in fields if f.get("name") == "Priority"), None)
                                
                                if state_field:
                                    state_values = self.projects_api.get_available_custom_field_values("State", sample_project_id)
                                    help_content["youtrack_help"]["states"] = {
                                        "available_states": state_values[:6] if isinstance(state_values, list) else ["Open", "In Progress", "Fixed"],
                                        "example_usage": f'update_issue_state("{sample_project_id}-123", "In Progress")'
                                    }
                                
                                if priority_field:
                                    priority_values = self.projects_api.get_available_custom_field_values("Priority", sample_project_id)
                                    help_content["youtrack_help"]["priorities"] = {
                                        "available_priorities": priority_values[:6] if isinstance(priority_values, list) else ["Critical", "Major", "Normal"],
                                        "example_usage": f'update_issue_priority("{sample_project_id}-123", "Critical")'
                                    }
                            
                except Exception as e:
                    help_content["youtrack_help"]["fields"] = {
                        "error": f"Could not fetch field data: {e}",
                        "note": "Use get_available_custom_field_values() to explore your field options"
                    }
            
            if topic in ["all", "examples"]:
                # Provide working examples with real or sample data
                sample_project = help_content["youtrack_help"].get("projects", {}).get("sample_project_id", "DEMO")
                sample_states = help_content["youtrack_help"].get("states", {}).get("available_states", ["Open", "In Progress", "Fixed"])
                sample_priorities = help_content["youtrack_help"].get("priorities", {}).get("available_priorities", ["Critical", "Major", "Normal"])
                
                help_content["quick_examples"] = {
                    "most_common_operations": {
                        "move_to_in_progress": f'update_issue_state("{sample_project}-123", "{sample_states[1] if len(sample_states) > 1 else "In Progress"}")',
                        "set_critical_priority": f'update_issue_priority("{sample_project}-123", "{sample_priorities[0] if sample_priorities else "Critical"}")',
                        "create_new_issue": f'create_issue(project_id="{sample_project}", summary="Bug in login system")',
                        "add_comment": f'add_comment("{sample_project}-123", "Working on this issue")'
                    },
                    "workflow_combinations": {
                        "escalate_issue": [
                            f'update_issue_priority("{sample_project}-123", "{sample_priorities[0] if sample_priorities else "Critical"}")',
                            f'update_issue_state("{sample_project}-123", "{sample_states[1] if len(sample_states) > 1 else "In Progress"}")',
                            f'add_comment("{sample_project}-123", "Escalated to critical priority")'
                        ],
                        "complete_issue": [
                            f'update_issue_state("{sample_project}-123", "{sample_states[-1] if sample_states else "Fixed"}")',
                            f'add_comment("{sample_project}-123", "Issue resolved and tested")'
                        ]
                    }
                }
            
            if topic in ["all", "functions"]:
                # List available functions with brief descriptions
                help_content["available_functions"] = {
                    "issue_management": {
                        "create_issue": "Create new issues",
                        "get_issue": "Get issue details", 
                        "search_issues": "Search for issues",
                        "get_project_issues": "Get all issues in a project"
                    },
                    "state_and_priority": {
                        "update_issue_state": "🎯 Change issue state (recommended)",
                        "update_issue_priority": "🚨 Change issue priority (recommended)",
                        "update_custom_fields": "Update any custom fields"
                    },
                    "comments_and_links": {
                        "add_comment": "Add comments to issues",
                        "add_dependency": "Create issue dependencies",
                        "add_relates_link": "Link related issues"
                    },
                    "exploration": {
                        "get_projects": "List available projects",
                        "get_available_custom_field_values": "See available field values",
                        "diagnose_workflow_restrictions": "Analyze workflow restrictions"
                    }
                }
            
            # Add quick tips
            help_content["quick_tips"] = {
                "proven_formats": {
                    "states": "Use simple strings: 'In Progress', not {'name': 'In Progress'}",
                    "priorities": "Use simple strings: 'Critical', not {'name': 'Critical'}",
                    "users": "Use login names: 'admin', not {'login': 'admin'}"
                },
                "troubleshooting": {
                    "workflow_errors": "Use diagnose_workflow_restrictions() to understand blocked transitions",
                    "field_values": "Use get_available_custom_field_values() to see valid options",
                    "permissions": "Ensure you have edit permissions for the project"
                }
            }
            
            return format_json_response(help_content)
            
        except Exception as e:
            logger.exception(f"Error generating help for topic: {topic}")
            return format_json_response({
                "error": str(e),
                "basic_help": {
                    "most_common_functions": [
                        "update_issue_state(issue_id, new_state)",
                        "update_issue_priority(issue_id, new_priority)", 
                        "create_issue(project_id, summary)",
                        "add_comment(issue_id, text)"
                    ],
                    "exploration_functions": [
                        "get_projects()",
                        "get_available_custom_field_values(field_name)",
                        "diagnose_workflow_restrictions(issue_id)"
                    ]
                }
            })
