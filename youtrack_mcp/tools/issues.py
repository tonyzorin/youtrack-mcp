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
from youtrack_mcp.utils import format_json_response

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
                raw_issue["summary"] = f"Issue {issue_id}"  # Provide a default summary

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
                return format_json_response({"error": "Project is required", "status": "error"})
            if not summary:
                return format_json_response({"error": "Summary is required", "status": "error"})

            # Check if project is a project ID or short name
            project_id = project
            if project and not project.startswith("0-"):
                # Try to get the project ID from the short name (e.g., "DEMO")
                try:
                    logger.info(f"Looking up project ID for: {project}")
                    projects_api = ProjectsClient(self.client)
                    project_obj = projects_api.get_project_by_name(project)
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
                        {"error": f"Error finding project: {str(e)}", "status": "error"}
                    )

            logger.info(f"Creating issue in project {project_id}: {summary}")

            # Call the API client to create the issue
            try:
                issue = self.issues_api.create_issue(project_id, summary, description)

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
                            return format_json_response(detailed_issue.model_dump(), indent=2)
                        else:
                            return format_json_response(detailed_issue)
                    except Exception as e:
                        logger.warning(f"Could not retrieve detailed issue: {str(e)}")
                if hasattr(issue, "model_dump"):
                    return format_json_response(issue.model_dump(), indent=2)
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
                    except:
                        pass
                logger.error(f"API error creating issue: {error_msg}")
                return format_json_response({"error": error_msg, "status": "error"})

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
                    "link_type": "Type of link like 'Relates', 'Duplicates', 'Depends on'"
                },
            },
            "get_issue_links": {
                "description": 'Get all links (relationships) for a YouTrack issue. Example: get_issue_links(issue_id="SP-123")',
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'SP-123'"
                },
            },
            "get_available_link_types": {
                "description": 'Get all available issue link types that can be used to connect issues. Example: get_available_link_types()',
                "parameter_descriptions": {},
            },
            "update_issue": {
                "description": 'Update an existing YouTrack issue with new summary, description or custom fields. Example: update_issue(issue_id="DEMO-123", summary="New title", description="Updated description")',
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123'",
                    "summary": "New issue title/summary (optional)",
                    "description": "New issue description (optional)",
                    "additional_fields": "Dictionary of additional custom fields to update (optional)"
                },
            },
            "add_dependency": {
                "description": 'Create a dependency relationship where one issue depends on another. Example: add_dependency(dependent_issue_id="DEMO-123", dependency_issue_id="DEMO-456")',
                "parameter_descriptions": {
                    "dependent_issue_id": "Issue that depends on another (e.g. 'DEMO-123')",
                    "dependency_issue_id": "Issue that is depended upon (e.g. 'DEMO-456')"
                },
            },
            "remove_dependency": {
                "description": 'Remove a dependency relationship between two issues. Example: remove_dependency(dependent_issue_id="DEMO-123", dependency_issue_id="DEMO-456")',
                "parameter_descriptions": {
                    "dependent_issue_id": "Issue that depends on another (e.g. 'DEMO-123')",
                    "dependency_issue_id": "Issue that is depended upon (e.g. 'DEMO-456')"
                },
            },
            "add_relates_link": {
                "description": 'Add a general "Relates" relationship between two issues. Example: add_relates_link(source_issue_id="DEMO-123", target_issue_id="DEMO-456")',
                "parameter_descriptions": {
                    "source_issue_id": "Source issue identifier (e.g. 'DEMO-123')",
                    "target_issue_id": "Target issue identifier (e.g. 'DEMO-456')"
                },
            },
            "add_duplicate_link": {
                "description": 'Mark one issue as a duplicate of another. Example: add_duplicate_link(duplicate_issue_id="DEMO-123", original_issue_id="DEMO-456")',
                "parameter_descriptions": {
                    "duplicate_issue_id": "Issue that is a duplicate (e.g. 'DEMO-123')",
                    "original_issue_id": "Original issue (e.g. 'DEMO-456')"
                },
            },
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
            raw_issue = self.client.get(f"issues/{issue_id}")
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

            content = self.issues_api.get_attachment_content(issue_id, attachment_id)
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
                        attachment_metadata.get("name") if attachment_metadata else None
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
    def link_issues(self, source_issue_id: str, target_issue_id: str, link_type: str) -> str:
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
            result = self.issues_api.link_issues(source_issue_id, target_issue_id, link_type)
            return format_json_response(result)
        except Exception as e:
            logger.exception(f"Error linking issues {source_issue_id} -> {target_issue_id}")
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
                additional_fields=additional_fields
            )
            # Convert Issue object to dict if needed
            if hasattr(result, 'model_dump'):
                result = result.model_dump()
            elif hasattr(result, '__dict__'):
                result = result.__dict__
            return format_json_response(result)
        except Exception as e:
            logger.exception(f"Error updating issue {issue_id}")
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def add_dependency(self, dependent_issue_id: str, dependency_issue_id: str) -> str:
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
            result = self.link_issues(dependent_issue_id, dependency_issue_id, "Depends on")
            return result
        except Exception as e:
            logger.exception(f"Error adding dependency between {dependent_issue_id} and {dependency_issue_id}")
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def remove_dependency(self, dependent_issue_id: str, dependency_issue_id: str) -> str:
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
            command = f"unlink {dependency_issue_id} depends on"
            
            command_data = {
                "query": command,
                "issues": [{"id": dependent_issue_id}]
            }
            
            response = self.client.post("commands", data=command_data)
            
            if isinstance(response, dict):
                return format_json_response({
                    "status": "success",
                    "message": f"Successfully removed dependency between {dependent_issue_id} and {dependency_issue_id}",
                    "command": command
                })
            
            return format_json_response(response)
        except Exception as e:
            logger.exception(f"Error removing dependency between {dependent_issue_id} and {dependency_issue_id}")
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def add_relates_link(self, source_issue_id: str, target_issue_id: str) -> str:
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
            result = self.link_issues(source_issue_id, target_issue_id, "Relates")
            return result
        except Exception as e:
            logger.exception(f"Error adding relates link between {source_issue_id} and {target_issue_id}")
            return format_json_response({"error": str(e), "status": "error"})

    @sync_wrapper
    def add_duplicate_link(self, duplicate_issue_id: str, original_issue_id: str) -> str:
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
            result = self.link_issues(duplicate_issue_id, original_issue_id, "Duplicates")
            return result
        except Exception as e:
            logger.exception(f"Error adding duplicate link between {duplicate_issue_id} and {original_issue_id}")
            return format_json_response({"error": str(e), "status": "error"})
