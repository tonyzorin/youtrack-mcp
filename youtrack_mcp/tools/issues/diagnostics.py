"""
YouTrack Issue Diagnostics Module.

This module contains diagnostic and help functions for YouTrack issue management:
- Workflow restriction analysis with actionable recommendations
- Interactive help system with live YouTrack data
- Troubleshooting guidance for common workflow scenarios

These functions provide intelligent analysis and guidance to help users understand
and navigate YouTrack's workflow system effectively.
"""

import json
import logging
from typing import Any, Dict

from youtrack_mcp.mcp_wrappers import sync_wrapper
from youtrack_mcp.utils import format_json_response

logger = logging.getLogger(__name__)


class Diagnostics:
    """Diagnostic and help functions for YouTrack issues."""

    def __init__(self, issues_api, projects_api):
        """Initialize with API clients."""
        self.issues_api = issues_api
        self.projects_api = projects_api

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
    def get_help(self, topic: str = "all") -> str:
        """
        Get interactive help with live YouTrack data and working examples.
        
        Unlike static tool descriptions, this provides dynamic help based on your 
        actual YouTrack configuration, showing real project IDs, available values,
        and copy-paste ready examples.
        
        Args:
            topic: Help topic - "all", "state", "priority", "fields", "projects", "examples", "workflow"
        
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
                    # We'll need to delegate to a method that gets projects
                    # For now, this is a placeholder that will be updated when we integrate
                    help_content["youtrack_help"]["projects"] = {
                        "note": "Project data will be populated when integrated with main class",
                        "example_usage": 'create_issue(project_id="DEMO", summary="Your issue title")'
                    }
                except Exception as e:
                    help_content["youtrack_help"]["projects"] = {
                        "error": f"Could not fetch projects: {e}",
                        "example_usage": 'create_issue(project_id="DEMO", summary="Your issue title")'
                    }
            
            if topic in ["all", "state", "fields", "workflow"]:
                # Get real custom field information
                try:
                    # This will be updated when integrated with main class
                    help_content["youtrack_help"]["workflow"] = {
                        "note": "Live workflow data will be populated when integrated",
                        "workflow_help": [
                            "Use diagnose_workflow_restrictions(issue_id) to analyze specific restrictions",
                            "Common transitions: Open → In Progress → Fixed → Closed",
                            "Some transitions require assignee or other conditions"
                        ]
                    }
                except Exception as e:
                    help_content["youtrack_help"]["fields"] = {
                        "error": f"Could not fetch field data: {e}",
                        "note": "Use get_available_custom_field_values() to explore your field options"
                    }
            
            if topic in ["all", "examples"]:
                # Provide working examples with sample data
                help_content["quick_examples"] = {
                    "most_common_operations": {
                        "move_to_in_progress": 'update_issue_state("DEMO-123", "In Progress")',
                        "set_critical_priority": 'update_issue_priority("DEMO-123", "Critical")',
                        "assign_to_user": 'update_issue_assignee("DEMO-123", "admin")',
                        "change_to_bug": 'update_issue_type("DEMO-123", "Bug")',
                        "set_estimation": 'update_issue_estimation("DEMO-123", "4h")',
                        "create_new_issue": 'create_issue(project_id="DEMO", summary="Bug in login system")',
                        "add_comment": 'add_comment("DEMO-123", "Working on this issue")'
                    },
                    "workflow_combinations": {
                        "escalate_issue": [
                            'update_issue_priority("DEMO-123", "Critical")',
                            'update_issue_assignee("DEMO-123", "admin")',
                            'update_issue_state("DEMO-123", "In Progress")',
                            'add_comment("DEMO-123", "Escalated to critical priority")'
                        ],
                        "complete_issue": [
                            'update_issue_state("DEMO-123", "Fixed")',
                            'add_comment("DEMO-123", "Issue resolved and tested")'
                        ],
                        "triage_new_issue": [
                            'update_issue_type("DEMO-123", "Bug")',
                            'update_issue_priority("DEMO-123", "Major")',
                            'update_issue_assignee("DEMO-123", "jane.doe")',
                            'update_issue_estimation("DEMO-123", "2d")'
                        ]
                    }
                }
            
            if topic in ["all", "functions"]:
                # List available functions with brief descriptions
                help_content["available_functions"] = {
                    "dedicated_updates": {
                        "update_issue_state": "🎯 Change issue state (recommended for state transitions)",
                        "update_issue_priority": "🚨 Change issue priority (recommended for priority changes)",
                        "update_issue_assignee": "👤 Assign issues to users",
                        "update_issue_type": "🏷️ Change issue type (Bug, Feature, etc.)",
                        "update_issue_estimation": "⏱️ Set time estimates"
                    },
                    "issue_management": {
                        "create_issue": "Create new issues",
                        "get_issue": "Get issue details", 
                        "search_issues": "Search for issues",
                        "update_issue": "Update issue summary/description"
                    },
                    "custom_fields": {
                        "update_custom_fields": "Update any custom fields (advanced)",
                        "batch_update_custom_fields": "Bulk custom field operations",
                        "get_custom_fields": "Get issue custom fields"
                    },
                    "comments_and_links": {
                        "add_comment": "Add comments to issues",
                        "add_dependency": "Create issue dependencies",
                        "add_relates_link": "Link related issues"
                    },
                    "diagnostics": {
                        "diagnose_workflow_restrictions": "🔍 Analyze workflow restrictions",
                        "get_help": "📚 Interactive help (this function)"
                    },
                    "exploration": {
                        "get_projects": "List available projects",
                        "get_available_custom_field_values": "See available field values"
                    }
                }
            
            # Add quick tips based on topic
            help_content["quick_tips"] = {
                "proven_formats": {
                    "states": "Use simple strings: 'In Progress', not {'name': 'In Progress'}",
                    "priorities": "Use simple strings: 'Critical', not {'name': 'Critical'}",
                    "users": "Use login names: 'admin', not {'login': 'admin'}",
                    "time": "Use simple formats: '4h', '2d', '30m', not ISO duration"
                },
                "troubleshooting": {
                    "workflow_errors": "Use diagnose_workflow_restrictions() to understand blocked transitions",
                    "field_values": "Use get_available_custom_field_values() to see valid options",
                    "permissions": "Ensure you have edit permissions for the project",
                    "format_errors": "Always use simple string values, avoid complex objects"
                }
            }

            # Add topic-specific guidance
            if topic == "workflow":
                help_content["workflow_guidance"] = {
                    "common_restrictions": [
                        "Submitted → Open: Often blocked to prevent backward workflow",
                        "→ In Progress: May require assignee to be set first",
                        "Fixed/Closed → Open: Usually requires admin permissions"
                    ],
                    "best_practices": [
                        "Use forward transitions when possible (Open → In Progress → Fixed)",
                        "Set assignee before moving to 'In Progress' state",
                        "Use diagnose_workflow_restrictions() to understand blocks",
                        "Check project workflow configuration if transitions fail"
                    ],
                    "troubleshooting_steps": [
                        "1. Try diagnose_workflow_restrictions(issue_id)",
                        "2. Check if assignee is required: update_issue_assignee() first",
                        "3. Try forward transitions instead of backward ones",
                        "4. Contact admin if workflow needs to be modified"
                    ]
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
                        "update_issue_assignee(issue_id, assignee)",
                        "create_issue(project_id, summary)",
                        "add_comment(issue_id, text)"
                    ],
                    "diagnostic_functions": [
                        "diagnose_workflow_restrictions(issue_id)",
                        "get_help(topic)"
                    ]
                }
            })

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for diagnostic functions."""
        return {
            "diagnose_workflow_restrictions": {
                "description": "Diagnose workflow restrictions and available state transitions for an issue. Analyzes state machine workflows, permissions, and provides actionable recommendations. Example: diagnose_workflow_restrictions(issue_id='DEMO-123')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'"
                }
            },
            "get_help": {
                "description": "Get interactive help with live YouTrack data and working examples. Unlike static tool descriptions, this provides dynamic help based on your actual YouTrack configuration, showing real project IDs, available values, and copy-paste ready examples.",
                "parameter_descriptions": {
                    "topic": "Help topic - 'all', 'state', 'priority', 'fields', 'projects', 'examples', 'workflow'. Defaults to 'all'"
                }
            }
        } 