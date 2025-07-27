"""
YouTrack Issue Utilities Module.

This module contains utility functions for the issues tools:
- Resource cleanup and connection management
- Tool definitions consolidation from all modules
- Integration support for the modular architecture

These functions provide infrastructure support for the issue management system.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class Utilities:
    """Utility functions for issue tools infrastructure."""

    def __init__(self, issues_api, projects_api):
        """Initialize with API clients."""
        self.issues_api = issues_api
        self.projects_api = projects_api
        self.client = issues_api.client  # Direct access for cleanup operations

    def close(self) -> None:
        """Close the API client and clean up resources."""
        try:
            if hasattr(self.client, 'close'):
                self.client.close()
                logger.info("API client closed successfully")
        except Exception as e:
            logger.warning(f"Error closing API client: {e}")

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get consolidated tool definitions from all issue modules.
        
        This method consolidates tool definitions from all modular components,
        providing a comprehensive registry of available tools and their configurations.
        In the modular architecture, each module maintains its own tool definitions
        which are aggregated here for system-wide access.

        Returns:
            Dictionary mapping tool names to their configuration
        """
        # Import the modules to get their tool definitions
        try:
            from .dedicated_updates import DedicatedUpdates
            from .diagnostics import Diagnostics
            from .custom_fields import CustomFields
            from .basic_operations import BasicOperations
            from .linking import Linking
            from .attachments import Attachments
        except ImportError as e:
            logger.error(f"Failed to import issue modules: {e}")
            return {}

        # Initialize module instances (they need the API clients for tool definitions)
        modules = [
            DedicatedUpdates(self.issues_api, self.projects_api),
            Diagnostics(self.issues_api, self.projects_api),
            CustomFields(self.issues_api, self.projects_api),
            BasicOperations(self.issues_api, self.projects_api),
            Linking(self.issues_api, self.projects_api),
            Attachments(self.issues_api, self.projects_api),
        ]

        # Consolidate tool definitions from all modules
        consolidated_definitions = {}
        
        for module in modules:
            try:
                module_definitions = module.get_tool_definitions()
                consolidated_definitions.update(module_definitions)
            except Exception as e:
                logger.warning(f"Failed to get tool definitions from {module.__class__.__name__}: {e}")

        logger.info(f"Consolidated {len(consolidated_definitions)} tool definitions from {len(modules)} modules")
        return consolidated_definitions

    def get_tool_definitions_legacy(self) -> Dict[str, Dict[str, Any]]:
        """
        Get tool definitions in the legacy monolithic format for backward compatibility.
        
        This method provides the original monolithic tool definitions structure
        for systems that may depend on the legacy format. It includes all the
        enhanced functions that were added during the refactoring process.

        Returns:
            Dictionary mapping tool names to their configuration (legacy format)
        """
        return {
            # Basic Operations
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
            "update_issue": {
                "description": 'Update an existing YouTrack issue with new summary, description or custom fields. Example: update_issue(issue_id="DEMO-123", summary="New title", description="Updated description")',
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123'",
                    "summary": "New issue title/summary (optional)",
                    "description": "New issue description (optional)",
                    "additional_fields": "Dictionary of additional custom fields to update (optional)",
                },
            },
            "add_comment": {
                "description": 'Add a text comment to an existing YouTrack issue. Example: add_comment(issue_id="DEMO-123", text="This has been fixed")',
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123'",
                    "text": "Text content of the comment to add",
                },
            },

            # Dedicated Updates (Enhanced)
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
            "update_issue_assignee": {
                "description": "Update an issue's assignee using the proven working REST API approach. Example: update_issue_assignee(issue_id='DEMO-123', assignee='admin')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'",
                    "assignee": "The user login name (e.g., 'admin', 'john.doe', 'jane.smith')"
                }
            },
            "update_issue_type": {
                "description": "Update an issue's type using the proven working REST API approach. Example: update_issue_type(issue_id='DEMO-123', issue_type='Bug')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'",
                    "issue_type": "The issue type (e.g., 'Bug', 'Feature', 'Task', 'Story')"
                }
            },
            "update_issue_estimation": {
                "description": "Update an issue's time estimation using the proven working REST API approach. Example: update_issue_estimation(issue_id='DEMO-123', estimation='4h')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'",
                    "estimation": "Time estimate (e.g., '4h', '2d', '30m', '1w', '3d 5h')"
                }
            },

            # Diagnostics (Enhanced)
            "diagnose_workflow_restrictions": {
                "description": "Diagnose workflow restrictions and available state transitions for an issue. Analyzes state machine workflows, permissions, and provides actionable recommendations. Example: diagnose_workflow_restrictions(issue_id='DEMO-123')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'"
                }
            },
            "get_help": {
                "description": "Get interactive help with live YouTrack data and working examples. Unlike static tool descriptions, this provides dynamic help based on your actual YouTrack configuration, showing real project IDs, available values, and copy-paste ready examples.",
                "parameter_descriptions": {
                    "topic": "Help topic - 'all', 'state', 'priority', 'fields', 'projects', 'examples'. Defaults to 'all'"
                }
            },

            # Custom Fields
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

            # Linking
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

            # Attachments
            "get_issue_raw": {
                "description": 'Get raw issue information bypassing model processing. Example: get_issue_raw(issue_id="DEMO-123")',
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123'"
                },
            },
            "get_attachment_content": {
                "description": 'Get attachment content as base64-encoded string (max 10MB). Example: get_attachment_content(issue_id="DEMO-123", attachment_id="1-123")',
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123'",
                    "attachment_id": "Attachment ID like '1-123'",
                },
            },
        } 