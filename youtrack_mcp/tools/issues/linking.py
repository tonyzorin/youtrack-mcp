"""
YouTrack Issue Linking Module.

This module contains functions for managing issue relationships and dependencies:
- Generic issue linking with various link types
- Issue dependency management (depends on/blocks relationships)
- Specialized relationship creation (relates, duplicates)
- Link retrieval and available link types discovery
- Dependency removal with command-based operations

These functions enable complex issue workflows and relationship tracking within YouTrack projects.
"""

import json
import logging
from typing import Any, Dict

from youtrack_mcp.mcp_wrappers import sync_wrapper
from youtrack_mcp.utils import format_json_response

logger = logging.getLogger(__name__)


class Linking:
    """Issue relationship and dependency management functions."""

    def __init__(self, issues_api, projects_api):
        """Initialize with API clients."""
        self.issues_api = issues_api
        self.projects_api = projects_api
        self.client = issues_api.client  # Direct access for complex operations

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

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for linking functions."""
        return {
            "link_issues": {
                "description": "Link two issues together with a specified relationship type. Supports various link types like 'Relates', 'Duplicates', 'Depends on', 'Blocks'. Example: link_issues(source_issue_id='DEMO-123', target_issue_id='DEMO-456', link_type='Relates')",
                "parameter_descriptions": {
                    "source_issue_id": "Source issue identifier like 'DEMO-123' or 'PROJECT-456'",
                    "target_issue_id": "Target issue identifier like 'DEMO-789' or 'PROJECT-012'",
                    "link_type": "Type of relationship ('Relates', 'Duplicates', 'Depends on', 'Blocks', etc.)"
                }
            },
            "get_issue_links": {
                "description": "Get all inward and outward links for an issue, showing all relationships and dependencies. Returns comprehensive link data including link types and target issues. Example: get_issue_links(issue_id='DEMO-123')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'"
                }
            },
            "get_available_link_types": {
                "description": "Get all available issue link types configured in YouTrack, including their properties and directional information. Use this to discover valid link_type values for other linking functions. Example: get_available_link_types()",
                "parameter_descriptions": {}
            },
            "add_dependency": {
                "description": "Create a dependency relationship where one issue depends on another (blocks/depends on). The dependent issue cannot be resolved until the dependency is completed. Example: add_dependency(dependent_issue_id='DEMO-123', dependency_issue_id='DEMO-456')",
                "parameter_descriptions": {
                    "dependent_issue_id": "Issue that depends on another (will be blocked)",
                    "dependency_issue_id": "Issue that must be completed first (blocking issue)"
                }
            },
            "remove_dependency": {
                "description": "Remove a dependency relationship between two issues using YouTrack commands. This breaks the blocking relationship between issues. Example: remove_dependency(dependent_issue_id='DEMO-123', dependency_issue_id='DEMO-456')",
                "parameter_descriptions": {
                    "dependent_issue_id": "Issue that currently depends on another",
                    "dependency_issue_id": "Issue that is currently blocking the dependent issue"
                }
            },
            "add_relates_link": {
                "description": "Add a 'Relates' relationship between two issues, indicating they are connected but without blocking dependencies. This is a general-purpose relationship type. Example: add_relates_link(source_issue_id='DEMO-123', target_issue_id='DEMO-456')",
                "parameter_descriptions": {
                    "source_issue_id": "Source issue identifier like 'DEMO-123'",
                    "target_issue_id": "Related issue identifier like 'DEMO-456'"
                }
            },
            "add_duplicate_link": {
                "description": "Mark one issue as a duplicate of another, typically used to close duplicate reports and redirect attention to the original issue. Example: add_duplicate_link(duplicate_issue_id='DEMO-123', original_issue_id='DEMO-456')",
                "parameter_descriptions": {
                    "duplicate_issue_id": "Issue to mark as duplicate (usually will be closed)",
                    "original_issue_id": "Original issue that should be used instead"
                }
            }
        } 