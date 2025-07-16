"""
YouTrack MCP Resources implementation.

This module implements the Model Context Protocol (MCP) resources for YouTrack.
Resources expose data and content from YouTrack to LLMs through a URI-based system.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import parse_qs, urlparse

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.issues import IssuesClient
from youtrack_mcp.api.projects import ProjectsClient
from youtrack_mcp.mcp_wrappers import sync_wrapper

logger = logging.getLogger(__name__)

# Resource URI scheme for YouTrack
YOUTRACK_URI_SCHEME = "youtrack"

# Resource URI templates
URI_TEMPLATES = {
    "projects": f"{YOUTRACK_URI_SCHEME}://projects",
    "project": f"{YOUTRACK_URI_SCHEME}://projects/{{project_id}}",
    "project_issues": f"{YOUTRACK_URI_SCHEME}://projects/{{project_id}}/issues",
    "issues": f"{YOUTRACK_URI_SCHEME}://issues",
    "issue": f"{YOUTRACK_URI_SCHEME}://issues/{{issue_id}}",
    "issue_comments": f"{YOUTRACK_URI_SCHEME}://issues/{{issue_id}}/comments",
    "users": f"{YOUTRACK_URI_SCHEME}://users",
    "user": f"{YOUTRACK_URI_SCHEME}://users/{{user_id}}",
    "search": f"{YOUTRACK_URI_SCHEME}://search?query={{query}}",
}


class ResourcesTools:
    """MCP Resources implementation for YouTrack."""

    def __init__(self):
        """Initialize the resources tools."""
        self.client = YouTrackClient()
        self.issues_api = IssuesClient(self.client)
        self.projects_api = ProjectsClient(self.client)

        # Cache for resource subscriptions
        self.subscriptions = set()

    @sync_wrapper
    def list_resources(self) -> str:
        """
        List available YouTrack resources.

        Returns:
            JSON string with available resources
        """
        try:
            # Define static resources
            resources = [
                {
                    "uri": URI_TEMPLATES["projects"],
                    "name": "All Projects",
                    "description": "List of all YouTrack projects",
                    "mimeType": "application/json",
                },
                {
                    "uri": URI_TEMPLATES["issues"],
                    "name": "All Issues",
                    "description": "List of all YouTrack issues",
                    "mimeType": "application/json",
                },
                {
                    "uri": URI_TEMPLATES["users"],
                    "name": "All Users",
                    "description": "List of all YouTrack users",
                    "mimeType": "application/json",
                },
            ]

            # Define resource templates
            templates = [
                {
                    "uriTemplate": URI_TEMPLATES["project"],
                    "name": "Project Details",
                    "description": "Details of a specific project",
                    "mimeType": "application/json",
                },
                {
                    "uriTemplate": URI_TEMPLATES["project_issues"],
                    "name": "Project Issues",
                    "description": "Issues in a specific project",
                    "mimeType": "application/json",
                },
                {
                    "uriTemplate": URI_TEMPLATES["issue"],
                    "name": "Issue Details",
                    "description": "Details of a specific issue",
                    "mimeType": "application/json",
                },
                {
                    "uriTemplate": URI_TEMPLATES["issue_comments"],
                    "name": "Issue Comments",
                    "description": "Comments on a specific issue",
                    "mimeType": "application/json",
                },
                {
                    "uriTemplate": URI_TEMPLATES["user"],
                    "name": "User Details",
                    "description": "Details of a specific user",
                    "mimeType": "application/json",
                },
                {
                    "uriTemplate": URI_TEMPLATES["search"],
                    "name": "Search Results",
                    "description": "Results of a YouTrack search query",
                    "mimeType": "application/json",
                },
            ]

            # Dynamically add all projects as resources
            try:
                projects = self.projects_api.get_projects()
                for project in projects:
                    project_id = (
                        project.id if hasattr(project, "id") else project.get("id")
                    )
                    project_name = (
                        project.name
                        if hasattr(project, "name")
                        else project.get("name")
                    )

                    if project_id and project_name:
                        resources.append(
                            {
                                "uri": URI_TEMPLATES["project"].format(
                                    project_id=project_id
                                ),
                                "name": f"Project: {project_name}",
                                "description": f"Details of project {project_name}",
                                "mimeType": "application/json",
                            }
                        )
            except Exception as e:
                logger.warning(f"Could not fetch projects for resources: {e}")

            return json.dumps({"resources": resources, "resourceTemplates": templates})
        except Exception as e:
            logger.exception("Error listing resources")
            return json.dumps({"error": str(e)})

    @sync_wrapper
    def read_resource(self, uri: str) -> str:
        """
        Read a YouTrack resource by URI.

        Args:
            uri: The URI of the resource to read

        Returns:
            JSON string with resource content
        """
        try:
            # Parse the URI
            parsed = urlparse(uri)

            # Validate the scheme
            if parsed.scheme != YOUTRACK_URI_SCHEME:
                return json.dumps(
                    {
                        "error": f"Invalid URI scheme: {parsed.scheme}. Expected: {YOUTRACK_URI_SCHEME}"
                    }
                )

            # Extract path components
            path = parsed.path.strip("/").split("/")

            # Process query parameters
            query_params = parse_qs(parsed.query)

            # Log the parsed URI components for debugging
            logger.debug(
                f"Parsed URI: scheme={parsed.scheme}, path={path}, query={query_params}"
            )

            # Handle different resource types based on path
            if len(path) == 1:
                # Root level resources
                if path[0] == "projects":
                    return self.get_all_projects()
                elif path[0] == "issues":
                    return self.get_all_issues()
                elif path[0] == "users":
                    return self.get_all_users()
                elif path[0] == "search" and "query" in query_params:
                    query = query_params["query"][0]
                    return self.search_issues(query)
            elif len(path) == 2:
                # Resource with ID
                if path[0] == "projects":
                    project_id = path[1]
                    logger.debug(f"Fetching project with ID: {project_id}")
                    return self.get_project(project_id)
                elif path[0] == "issues":
                    issue_id = path[1]
                    logger.debug(f"Fetching issue with ID: {issue_id}")
                    return self.get_issue(issue_id)
                elif path[0] == "users":
                    user_id = path[1]
                    logger.debug(f"Fetching user with ID: {user_id}")
                    return self.get_user(user_id)
            elif len(path) == 3:
                # Sub-resources
                if path[0] == "projects" and path[2] == "issues":
                    project_id = path[1]
                    logger.debug(f"Fetching issues for project: {project_id}")
                    return self.get_project_issues(project_id)
                elif path[0] == "issues" and path[2] == "comments":
                    issue_id = path[1]
                    logger.debug(f"Fetching comments for issue: {issue_id}")
                    try:
                        return self.get_issue_comments(issue_id)
                    except Exception as e:
                        logger.error(
                            f"Error fetching comments for issue {issue_id}: {e}"
                        )
                        # Fall back to direct API call
                        try:
                            comments = self.client.get(f"issues/{issue_id}/comments")
                            return json.dumps(
                                {
                                    "contents": [
                                        {
                                            "uri": URI_TEMPLATES[
                                                "issue_comments"
                                            ].format(issue_id=issue_id),
                                            "mimeType": "application/json",
                                            "text": json.dumps(comments),
                                        }
                                    ]
                                }
                            )
                        except Exception as direct_error:
                            logger.error(
                                f"Error with direct API call for comments: {direct_error}"
                            )
                            raise

            logger.warning(f"Unknown resource URI pattern: {uri}")
            return json.dumps({"error": f"Unknown resource URI: {uri}"})
        except Exception as e:
            logger.exception(f"Error reading resource: {uri}")
            return json.dumps({"error": f"Error processing resource {uri}: {str(e)}"})

    @sync_wrapper
    def subscribe_resource(self, uri: str) -> str:
        """
        Subscribe to updates for a resource.

        Args:
            uri: The URI of the resource to subscribe to

        Returns:
            JSON string confirming subscription
        """
        try:
            # Add URI to subscriptions
            self.subscriptions.add(uri)

            return json.dumps({"subscribed": True, "uri": uri})
        except Exception as e:
            logger.exception(f"Error subscribing to resource: {uri}")
            return json.dumps({"error": str(e)})

    @sync_wrapper
    def unsubscribe_resource(self, uri: str) -> str:
        """
        Unsubscribe from updates for a resource.

        Args:
            uri: The URI of the resource to unsubscribe from

        Returns:
            JSON string confirming unsubscription
        """
        try:
            # Remove URI from subscriptions if it exists
            if uri in self.subscriptions:
                self.subscriptions.remove(uri)

            return json.dumps({"unsubscribed": True, "uri": uri})
        except Exception as e:
            logger.exception(f"Error unsubscribing from resource: {uri}")
            return json.dumps({"error": str(e)})

    def get_all_projects(self) -> str:
        """Get all projects as a resource."""
        try:
            # Fetch projects using the API client
            result = self.projects_api.get_projects()

            return json.dumps(
                {
                    "contents": [
                        {
                            "uri": URI_TEMPLATES["projects"],
                            "mimeType": "application/json",
                            "text": json.dumps(result),
                        }
                    ]
                }
            )
        except Exception as e:
            logger.exception("Error getting all projects")
            return json.dumps({"error": str(e)})

    def get_project(self, project_id: str) -> str:
        """Get a specific project as a resource."""
        try:
            project = self.projects_api.get_project(project_id)

            # Convert to dict if it's a model
            if hasattr(project, "model_dump"):
                project_data = project.model_dump()
            else:
                project_data = project

            return json.dumps(
                {
                    "contents": [
                        {
                            "uri": URI_TEMPLATES["project"].format(
                                project_id=project_id
                            ),
                            "mimeType": "application/json",
                            "text": json.dumps(project_data),
                        }
                    ]
                }
            )
        except Exception as e:
            logger.exception(f"Error getting project: {project_id}")
            return json.dumps({"error": str(e)})

    def get_project_issues(self, project_id: str) -> str:
        """Get issues for a specific project as a resource."""
        try:
            issues = self.projects_api.get_project_issues(project_id)

            return json.dumps(
                {
                    "contents": [
                        {
                            "uri": URI_TEMPLATES["project_issues"].format(
                                project_id=project_id
                            ),
                            "mimeType": "application/json",
                            "text": json.dumps(issues),
                        }
                    ]
                }
            )
        except Exception as e:
            logger.exception(f"Error getting issues for project: {project_id}")
            return json.dumps({"error": str(e)})

    def get_all_issues(self) -> str:
        """Get all issues as a resource."""
        try:
            # This would typically use a search with no filters
            issues = self.client.get("issues", params={"$top": 100})

            return json.dumps(
                {
                    "contents": [
                        {
                            "uri": URI_TEMPLATES["issues"],
                            "mimeType": "application/json",
                            "text": json.dumps(issues),
                        }
                    ]
                }
            )
        except Exception as e:
            logger.exception("Error getting all issues")
            return json.dumps({"error": str(e)})

    def get_issue(self, issue_id: str) -> str:
        """Get a specific issue as a resource."""
        try:
            try:
                # First try to get the issue using the issues_api
                issue = self.issues_api.get_issue(issue_id)

                # Convert to dict if it's a model
                if hasattr(issue, "model_dump"):
                    issue_data = issue.model_dump()
                else:
                    issue_data = issue
            except Exception as api_error:
                logger.warning(f"Error retrieving issue with issues_api: {api_error}")

                # Fall back to direct API call
                try:
                    # Try direct API call to get raw issue data
                    issue_data = self.client.get(f"issues/{issue_id}")

                    # Ensure id is present in the response
                    if (
                        "id" not in issue_data
                        and "$type" in issue_data
                        and issue_data.get("$type") == "Issue"
                    ):
                        # If id is missing but we know it's an issue, add the ID from our parameter
                        issue_data["id"] = issue_id
                except Exception as direct_error:
                    logger.error(f"Error with direct API call: {direct_error}")
                    raise

            return json.dumps(
                {
                    "contents": [
                        {
                            "uri": URI_TEMPLATES["issue"].format(issue_id=issue_id),
                            "mimeType": "application/json",
                            "text": json.dumps(issue_data),
                        }
                    ]
                }
            )
        except Exception as e:
            logger.exception(f"Error getting issue: {issue_id}")
            return json.dumps({"error": str(e)})

    def get_issue_comments(self, issue_id: str) -> str:
        """Get comments for a specific issue as a resource."""
        try:
            # First try to get detailed comments
            try:
                # Attempt to get full comment details with content
                comments_with_details = self.client.get(
                    f"issues/{issue_id}/comments?fields=id,text,created,updated,author(id,login,name)"
                )
                logger.debug(
                    f"Retrieved {len(comments_with_details)} comments for issue: {issue_id}"
                )

                return json.dumps(
                    {
                        "contents": [
                            {
                                "uri": URI_TEMPLATES["issue_comments"].format(
                                    issue_id=issue_id
                                ),
                                "mimeType": "application/json",
                                "text": json.dumps(comments_with_details),
                            }
                        ]
                    }
                )
            except Exception as api_error:
                logger.warning(
                    f"Error retrieving detailed comments with original API: {api_error}"
                )

                # Fall back to basic comment list
                comments = self.client.get(f"issues/{issue_id}/comments")

                return json.dumps(
                    {
                        "contents": [
                            {
                                "uri": URI_TEMPLATES["issue_comments"].format(
                                    issue_id=issue_id
                                ),
                                "mimeType": "application/json",
                                "text": json.dumps(comments),
                            }
                        ]
                    }
                )
        except Exception as e:
            logger.exception(f"Error getting comments for issue: {issue_id}")
            return json.dumps({"error": str(e)})

    def get_all_users(self) -> str:
        """Get all users as a resource."""
        try:
            users = self.client.get("users")

            return json.dumps(
                {
                    "contents": [
                        {
                            "uri": URI_TEMPLATES["users"],
                            "mimeType": "application/json",
                            "text": json.dumps(users),
                        }
                    ]
                }
            )
        except Exception as e:
            logger.exception("Error getting all users")
            return json.dumps({"error": str(e)})

    def get_user(self, user_id: str) -> str:
        """Get a specific user as a resource."""
        try:
            user = self.client.get(f"users/{user_id}")

            return json.dumps(
                {
                    "contents": [
                        {
                            "uri": URI_TEMPLATES["user"].format(user_id=user_id),
                            "mimeType": "application/json",
                            "text": json.dumps(user),
                        }
                    ]
                }
            )
        except Exception as e:
            logger.exception(f"Error getting user: {user_id}")
            return json.dumps({"error": str(e)})

    def search_issues(self, query: str) -> str:
        """Search issues as a resource."""
        try:
            results = self.client.get("issues", params={"query": query, "$top": 100})

            return json.dumps(
                {
                    "contents": [
                        {
                            "uri": URI_TEMPLATES["search"].format(query=query),
                            "mimeType": "application/json",
                            "text": json.dumps(results),
                        }
                    ]
                }
            )
        except Exception as e:
            logger.exception(f"Error searching issues with query: {query}")
            return json.dumps({"error": str(e)})

    def close(self) -> None:
        """Close any resources."""
        self.subscriptions.clear()

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions with descriptions."""
        return {
            "list_resources": {
                "description": "List available YouTrack resources.",
                "parameter_descriptions": {},
            },
            "read_resource": {
                "description": "Read a YouTrack resource by URI.",
                "parameter_descriptions": {
                    "uri": "The URI of the resource to read (e.g., 'youtrack://projects/0-0')"
                },
            },
            "subscribe_resource": {
                "description": "Subscribe to updates for a resource.",
                "parameter_descriptions": {
                    "uri": "The URI of the resource to subscribe to"
                },
            },
            "unsubscribe_resource": {
                "description": "Unsubscribe from updates for a resource.",
                "parameter_descriptions": {
                    "uri": "The URI of the resource to unsubscribe from"
                },
            },
            "get_all_issues": {
                "description": "Get all issues as a resource.",
                "parameter_descriptions": {},
            },
            "get_issue": {
                "description": "Get a specific issue as a resource.",
                "parameter_descriptions": {
                    "issue_id": "The issue ID or readable ID (e.g., PROJECT-123)"
                },
            },
            "get_issue_comments": {
                "description": "Get comments for a specific issue as a resource.",
                "parameter_descriptions": {
                    "issue_id": "The issue ID or readable ID (e.g., PROJECT-123)"
                },
            },
            "get_all_projects": {
                "description": "Get all projects as a resource.",
                "parameter_descriptions": {},
            },
            "get_project": {
                "description": "Get a specific project as a resource.",
                "parameter_descriptions": {
                    "project_id": "The project ID (e.g., '0-0')"
                },
            },
            "get_project_issues": {
                "description": "Get issues for a specific project as a resource.",
                "parameter_descriptions": {
                    "project_id": "The project ID (e.g., '0-0')"
                },
            },
            "get_all_users": {
                "description": "Get all users as a resource.",
                "parameter_descriptions": {},
            },
            "get_user": {
                "description": "Get a specific user as a resource.",
                "parameter_descriptions": {"user_id": "The user ID (e.g., '1-1')"},
            },
            "search_issues": {
                "description": "Search issues as a resource.",
                "parameter_descriptions": {
                    "query": "The search query (e.g., 'project: DEMO #Unresolved')"
                },
            },
        }
