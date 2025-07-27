"""
YouTrack Issue Basic Operations Module.

This module contains the core CRUD (Create, Read, Update, Delete) operations for YouTrack issues:
- Issue retrieval with comprehensive field data
- Issue search using YouTrack query language
- Issue creation with project validation
- Issue updates for summary and description
- Comment addition to issues

These functions form the foundation of issue management and are used by other modules
for building more complex workflows and operations.
"""

import json
import logging
from typing import Any, Dict, Optional

from youtrack_mcp.mcp_wrappers import sync_wrapper
from youtrack_mcp.utils import format_json_response

logger = logging.getLogger(__name__)


class BasicOperations:
    """Core CRUD operations for YouTrack issues."""

    def __init__(self, issues_api, projects_api):
        """Initialize with API clients."""
        self.issues_api = issues_api
        self.projects_api = projects_api
        self.client = issues_api.client  # Direct access for complex queries

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

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for basic operation functions."""
        return {
            "get_issue": {
                "description": "Get complete information about a YouTrack issue including custom fields and metadata. Returns comprehensive issue data with project, reporter, assignee, and custom field details. Example: get_issue(issue_id='DEMO-123')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'"
                }
            },
            "search_issues": {
                "description": "Search for issues using YouTrack query syntax. Supports filters like project, status, assignee, and custom fields. Example: search_issues(query='project: DEMO #Unresolved', limit=5)",
                "parameter_descriptions": {
                    "query": "YouTrack search query string (e.g., 'project: DEMO', '#Unresolved', 'assignee: admin')",
                    "limit": "Maximum number of results to return (default: 10)"
                }
            },
            "create_issue": {
                "description": "Create a new issue in YouTrack with automatic project validation. Accepts both project short names (DEMO) and project IDs (0-1). Example: create_issue(project='DEMO', summary='Bug in login', description='Users cannot log in')",
                "parameter_descriptions": {
                    "project": "Project identifier (short name like 'DEMO' or ID like '0-1')",
                    "summary": "Issue title/summary (required)",
                    "description": "Detailed description of the issue (optional)"
                }
            },
            "update_issue": {
                "description": "Update an existing issue's summary, description, or additional fields. Use for basic issue metadata updates - for custom fields use update_custom_fields. Example: update_issue(issue_id='DEMO-123', summary='Updated title', description='New description')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'",
                    "summary": "New issue summary/title (optional)",
                    "description": "New issue description (optional)",
                    "additional_fields": "Additional fields to update as dictionary (optional)"
                }
            },
            "add_comment": {
                "description": "Add a text comment to an issue. Comments are visible to all users with access to the issue. Example: add_comment(issue_id='DEMO-123', text='This has been fixed and tested')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'",
                    "text": "Comment text content"
                }
            }
        } 