"""
YouTrack Issue Custom Fields Module.

This module contains custom field management functions for YouTrack issues:
- Field value updates with validation and bulk operations
- Field validation against project schemas
- Available value retrieval for enum/state fields
- Comprehensive error handling and user guidance

These functions provide robust custom field management with support for
both simple and complex field types, including enum, state, user, and period fields.
"""

import json
import logging
from typing import Any, Dict, List

from youtrack_mcp.mcp_wrappers import sync_wrapper
from youtrack_mcp.utils import format_json_response

logger = logging.getLogger(__name__)


class CustomFields:
    """Custom field management functions for YouTrack issues."""

    def __init__(self, issues_api, projects_api):
        """Initialize with API clients."""
        self.issues_api = issues_api
        self.projects_api = projects_api

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
        issues: List[str] = None,
        custom_fields: Dict[str, Any] = None,
        updates: List[Dict[str, Any]] = None
    ) -> str:
        """
        Update custom fields for multiple issues in a single operation.

        FLEXIBLE FORMATS:
        1. List format: batch_update_custom_fields([{"issue_id": "DEMO-123", "fields": {"Priority": "High"}}])
        2. Bulk format: batch_update_custom_fields(issues=["DEMO-123", "DEMO-124"], custom_fields={"Priority": "High"})

        Args:
            issues: List of issue IDs (for bulk format)
            custom_fields: Dictionary of fields to apply to all issues (for bulk format)  
            updates: List of update dictionaries (for list format)

        Returns:
            JSON string with batch update results
        """
        try:
            logger.info(f"Batch update called with: updates={updates}, issues={issues}, custom_fields={custom_fields}")
            
            # Handle different input formats
            if updates:
                # Format 1: List of update dictionaries
                final_updates = updates
                logger.info(f"Using list format with {len(updates)} updates")
            elif issues and custom_fields:
                # Format 2: Bulk update same fields for multiple issues
                final_updates = [
                    {"issue_id": issue_id, "fields": custom_fields}
                    for issue_id in issues
                ]
                logger.info(f"Using bulk format: {len(issues)} issues with fields {list(custom_fields.keys())}")
            else:
                logger.warning(f"Invalid parameters: updates={updates}, issues={issues}, custom_fields={custom_fields}")
                return format_json_response({
                    "status": "error",
                    "error": "Either 'updates' list or both 'issues' and 'custom_fields' parameters are required",
                    "received_params": {
                        "updates": updates is not None,
                        "issues": issues is not None, 
                        "custom_fields": custom_fields is not None
                    }
                })

            if not final_updates:
                return format_json_response({
                    "status": "error",
                    "error": "No updates to process",
                    "final_updates": final_updates
                })

            # Process batch updates
            results = self.issues_api.batch_update_custom_fields(final_updates)

            # Summarize results
            success_count = len([r for r in results if r.get("status") == "success"])
            error_count = len([r for r in results if r.get("status") == "error"])
            skipped_count = len([r for r in results if r.get("status") == "skipped"])

            response = {
                "status": "completed",
                "summary": {
                    "total": len(final_updates),
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
                "attempted_updates": len(final_updates) if 'final_updates' in locals() else 0
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

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for custom field functions."""
        return {
            "update_custom_fields": {
                "description": "Update custom fields on an issue with comprehensive validation. Use proven simple string formats: Priority='Critical', State='In Progress', Assignee='admin'. Example: update_custom_fields(issue_id='DEMO-123', custom_fields={'Priority': 'Critical', 'Assignee': 'admin'})",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'",
                    "custom_fields": "Dictionary of field name-value pairs using simple string formats",
                    "validate": "Whether to validate field values (default: True)"
                }
            },
            "batch_update_custom_fields": {
                "description": "Update custom fields for multiple issues in a single operation. Supports two formats: 1) List format with update dictionaries, 2) Bulk format with issue list and common fields. Examples: batch_update_custom_fields([{'issue_id': 'DEMO-123', 'fields': {'Priority': 'High'}}]) or batch_update_custom_fields(issues=['DEMO-123', 'DEMO-124'], custom_fields={'Priority': 'High'})",
                "parameter_descriptions": {
                    "issues": "List of issue IDs (for bulk format) - optional",
                    "custom_fields": "Dictionary of fields to apply to all issues (for bulk format) - optional", 
                    "updates": "List of update dictionaries with 'issue_id' and 'fields' keys (for list format) - optional"
                }
            },
            "get_custom_fields": {
                "description": "Get all custom fields for a specific issue, including their current values and metadata. Example: get_custom_fields(issue_id='DEMO-123')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'"
                }
            },
            "validate_custom_field": {
                "description": "Validate a custom field value against project schema to check if it's allowed. Example: validate_custom_field(project_id='DEMO', field_name='Priority', field_value='Critical')",
                "parameter_descriptions": {
                    "project_id": "Project identifier like 'DEMO' or '0-0'",
                    "field_name": "Custom field name like 'Priority', 'State', 'Assignee'",
                    "field_value": "Value to validate against field schema"
                }
            },
            "get_available_custom_field_values": {
                "description": "Get available values for enum/state custom fields to see what values are allowed. Example: get_available_custom_field_values(project_id='DEMO', field_name='Priority')",
                "parameter_descriptions": {
                    "project_id": "Project identifier like 'DEMO' or '0-0'",
                    "field_name": "Custom field name like 'Priority', 'State', 'Type'"
                }
            }
        } 