"""
YouTrack Issue Dedicated Updates Module.

This module contains specialized update functions for the most common YouTrack operations:
- State transitions with enhanced workflow error handling
- Priority changes with field-specific guidance  
- Assignment updates with user validation
- Type changes with project-specific validation
- Time estimation updates with format examples

All functions use the proven simple string format and provide enhanced error messages
with specific workflow guidance and troubleshooting steps.
"""

import json
import logging
from typing import Any, Dict

from youtrack_mcp.mcp_wrappers import sync_wrapper
from youtrack_mcp.utils import format_json_response

logger = logging.getLogger(__name__)


class DedicatedUpdates:
    """Specialized update functions for common YouTrack operations."""

    def __init__(self, issues_api, projects_api):
        """Initialize with API clients."""
        self.issues_api = issues_api
        self.projects_api = projects_api

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
                    # Enhanced error handling with specific workflow analysis
                    error_msg = str(cmd_error)
                    
                    # Parse specific workflow failure reasons
                    specific_guidance = []
                    workflow_reason = "Unknown workflow restriction"
                    
                    if "workflow restrictions" in error_msg.lower() or "status 405" in error_msg or "Failed to transition" in error_msg:
                        # Try to get current state for better context
                        try:
                            current_issue = self.issues_api.get_issue(issue_id)
                            current_state = "Unknown"
                            
                            for field in current_issue.get("customFields", []):
                                if field.get("name") == "State":
                                    current_state = field.get("value", {}).get("name", "Unknown")
                                    break
                            
                            workflow_reason = f"Transition from '{current_state}' to '{new_state}' is blocked by workflow rules"
                            
                            # Provide specific guidance based on common workflow patterns
                            if current_state == "Submitted" and new_state == "Open":
                                specific_guidance = [
                                    "🚫 WORKFLOW RESTRICTION: Moving from 'Submitted' back to 'Open' is typically not allowed",
                                    "💡 WHY: Once submitted/reviewed, issues shouldn't go backwards in the workflow", 
                                    "✅ TRY INSTEAD: Move to 'In Progress' to continue work",
                                    "✅ OR: Move to 'Fixed' if the work is complete",
                                    "🔧 IF NEEDED: Contact your YouTrack admin to modify workflow rules"
                                ]
                            elif new_state == "In Progress" and ("assignee" in error_msg.lower() or current_state in ["Open", "Submitted"]):
                                specific_guidance = [
                                    "🚫 WORKFLOW RESTRICTION: 'In Progress' state may require an assignee",
                                    "✅ SOLUTION: Set assignee first with update_issue_assignee()",
                                    f"📝 EXAMPLE: update_issue_assignee('{issue_id}', 'admin')",
                                    f"📝 THEN: update_issue_state('{issue_id}', 'In Progress')"
                                ]
                            elif current_state in ["Fixed", "Closed"] and new_state in ["Open", "In Progress"]:
                                specific_guidance = [
                                    f"🚫 WORKFLOW RESTRICTION: Reopening from '{current_state}' may require special permissions",
                                    "💡 WHY: Completed work typically shouldn't be reopened without approval",
                                    "✅ TRY: Check if you need admin permissions for this transition",
                                    "✅ OR: Create a new issue for additional work instead"
                                ]
                            elif "status 405" in error_msg:
                                specific_guidance = [
                                    "🚫 API RESTRICTION: HTTP 405 indicates this operation is not allowed",
                                    f"💡 COMMON CAUSE: '{current_state}' → '{new_state}' transition violates workflow rules",
                                    "✅ TRY: Forward transitions like 'In Progress' or 'Fixed'", 
                                    "✅ CHECK: Available transitions with diagnose_workflow_restrictions()",
                                    "🔧 NOTE: This may require different permissions or workflow configuration"
                                ]
                            else:
                                specific_guidance = [
                                    f"🚫 WORKFLOW RESTRICTION: '{current_state}' → '{new_state}' transition is not allowed",
                                    "💡 This is enforced by your project's workflow configuration",
                                    "✅ USE: diagnose_workflow_restrictions() to see allowed transitions",
                                    "✅ CHECK: Available target states for your current position"
                                ]
                                
                        except Exception:
                            # Fallback if we can't get current state
                            if "status 405" in error_msg:
                                specific_guidance = [
                                    "🚫 API RESTRICTION: HTTP 405 indicates this operation is not allowed",
                                    f"💡 LIKELY CAUSE: Transition to '{new_state}' violates workflow rules",
                                    "✅ TRY: Forward transitions like 'In Progress' or 'Fixed'",
                                    "✅ USE: diagnose_workflow_restrictions() to analyze the restriction",
                                    "🔧 NOTE: Some transitions require admin permissions"
                                ]
                            else:
                                specific_guidance = [
                                    f"🚫 WORKFLOW RESTRICTION: Transition to '{new_state}' is blocked",
                                    "💡 This is enforced by your project's workflow rules",
                                    "✅ USE: diagnose_workflow_restrictions() to analyze the restriction",
                                    "✅ TRY: Different target states that may be allowed"
                                ]
                    
                    return format_json_response({
                        "error": f"State transition failed: {workflow_reason}",
                        "issue_id": issue_id,
                        "target_state": new_state,
                        "workflow_restriction": True,
                        "specific_guidance": specific_guidance,
                        "general_troubleshooting": [
                            "Check if the target state exists in your YouTrack project",
                            "Verify you have permissions to change issue states",
                            "Some transitions require intermediate steps or conditions"
                        ],
                        "diagnostic_help": f"Use diagnose_workflow_restrictions('{issue_id}') for detailed workflow analysis",
                        "alternative_suggestion": "Try forward transitions like 'In Progress' or 'Fixed' instead of backward ones"
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
            # We need to import the update_custom_fields function - this will be handled by the main class
            from youtrack_mcp.tools.issues.custom_fields import CustomFields
            custom_fields_handler = CustomFields(self.issues_api, self.projects_api)
            
            result = custom_fields_handler.update_custom_fields(
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
    def update_issue_assignee(self, issue_id: str, assignee: str) -> str:
        """
        Update an issue's assignee using the proven working REST API approach.
        
        🎯 PROVEN WORKING FORMAT (based on successful testing):
        - Uses simple string values: "admin", "john.doe", "jane.smith"
        - NO complex objects or ID references needed
        
        ✅ EXAMPLES THAT WORK:
        - update_issue_assignee("DEMO-123", "admin")
        - update_issue_assignee("PROJECT-456", "john.doe") 
        - update_issue_assignee("TASK-789", "jane.smith")
        
        🔧 WHAT HAPPENS UNDER THE HOOD:
        - Direct Field Update API with format {"customFields": [{"name": "Assignee", "value": "admin"}]}
        - Simple string values proven to work reliably
        - Smart error handling with assignee-specific guidance
        
        FORMAT: update_issue_assignee(issue_id="DEMO-123", assignee="admin")
        
        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")
            assignee: The user login name (e.g., "admin", "john.doe", "jane.smith")
            
        Returns:
            JSON string with the updated issue information and success details
            
        Common Usage: Assignment during triage, team member allocation
        """
        try:
            if not issue_id or not assignee:
                return format_json_response({
                    "error": "Both issue ID and assignee are required"
                })
            
            logger.info(f"Updating issue {issue_id} assignee to '{assignee}' using proven simple string format")
            
            # Use the proven simple string format for custom field updates
            from youtrack_mcp.tools.issues.custom_fields import CustomFields
            custom_fields_handler = CustomFields(self.issues_api, self.projects_api)
            
            result = custom_fields_handler.update_custom_fields(
                issue_id=issue_id,
                custom_fields={"Assignee": assignee}
            )
            
            # Parse the result to provide assignee-specific feedback
            result_data = json.loads(result) if isinstance(result, str) else result
            
            if result_data.get("status") == "success":
                return format_json_response({
                    "status": "success",
                    "message": f"Successfully assigned issue {issue_id} to '{assignee}'",
                    "issue_id": issue_id,
                    "assignee": assignee,
                    "api_method": "Direct Field Update API",
                    "updated_fields": result_data.get("updated_fields", ["Assignee"]),
                    "issue_data": result_data.get("issue_data", {})
                })
            else:
                # Handle error case with assignee-specific guidance
                error_msg = result_data.get("error", "Unknown error")
                return format_json_response({
                    "error": f"Assignee update failed: {error_msg}",
                    "issue_id": issue_id,
                    "target_assignee": assignee,
                    "troubleshooting": [
                        "Check if the user exists in your YouTrack instance",
                        "Verify the user has access to this project",
                        "Use login names like 'admin', 'john.doe' (not display names)",
                        "Use get_current_user() to see your login format"
                    ],
                    "user_help": "Use get_current_user() or search_users() to find valid login names"
                })
                
        except Exception as e:
            logger.exception(f"Error updating assignee for issue {issue_id}")
            return format_json_response({
                "error": str(e),
                "issue_id": issue_id,
                "target_assignee": assignee,
                "suggestion": "Check issue ID format and verify user exists in YouTrack"
            })

    @sync_wrapper
    def update_issue_type(self, issue_id: str, issue_type: str) -> str:
        """
        Update an issue's type using the proven working REST API approach.
        
        🎯 PROVEN WORKING FORMAT (based on successful testing):
        - Uses simple string values: "Bug", "Feature", "Task", "Story"
        - NO complex objects or ID references needed
        
        ✅ EXAMPLES THAT WORK:
        - update_issue_type("DEMO-123", "Bug")
        - update_issue_type("PROJECT-456", "Feature") 
        - update_issue_type("TASK-789", "Task")
        
        🔧 WHAT HAPPENS UNDER THE HOOD:
        - Direct Field Update API with format {"customFields": [{"name": "Type", "value": "Bug"}]}
        - Simple string values proven to work reliably
        - Smart error handling with type-specific guidance
        
        FORMAT: update_issue_type(issue_id="DEMO-123", issue_type="Bug")
        
        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")
            issue_type: The issue type (e.g., "Bug", "Feature", "Task", "Story")
            
        Returns:
            JSON string with the updated issue information and success details
            
        Common Types: "Bug", "Feature", "Task", "Story", "Epic", "Improvement"
        """
        try:
            if not issue_id or not issue_type:
                return format_json_response({
                    "error": "Both issue ID and issue type are required"
                })
            
            logger.info(f"Updating issue {issue_id} type to '{issue_type}' using proven simple string format")
            
            # Use the proven simple string format for custom field updates
            from youtrack_mcp.tools.issues.custom_fields import CustomFields
            custom_fields_handler = CustomFields(self.issues_api, self.projects_api)
            
            result = custom_fields_handler.update_custom_fields(
                issue_id=issue_id,
                custom_fields={"Type": issue_type}
            )
            
            # Parse the result to provide type-specific feedback
            result_data = json.loads(result) if isinstance(result, str) else result
            
            if result_data.get("status") == "success":
                return format_json_response({
                    "status": "success",
                    "message": f"Successfully updated issue {issue_id} type to '{issue_type}'",
                    "issue_id": issue_id,
                    "issue_type": issue_type,
                    "api_method": "Direct Field Update API",
                    "updated_fields": result_data.get("updated_fields", ["Type"]),
                    "issue_data": result_data.get("issue_data", {})
                })
            else:
                # Handle error case with type-specific guidance
                error_msg = result_data.get("error", "Unknown error")
                return format_json_response({
                    "error": f"Type update failed: {error_msg}",
                    "issue_id": issue_id,
                    "target_type": issue_type,
                    "troubleshooting": [
                        "Check if the issue type exists in your YouTrack project",
                        "Verify you have permissions to change issue types",
                        "Common types: Bug, Feature, Task, Story, Epic",
                        "Use get_available_custom_field_values() to see available types"
                    ],
                    "type_help": f"Use get_available_custom_field_values('Type') to see valid options"
                })
                
        except Exception as e:
            logger.exception(f"Error updating type for issue {issue_id}")
            return format_json_response({
                "error": str(e),
                "issue_id": issue_id,
                "target_type": issue_type,
                "suggestion": "Check issue ID format and verify type exists in YouTrack"
            })

    @sync_wrapper
    def update_issue_estimation(self, issue_id: str, estimation: str) -> str:
        """
        Update an issue's time estimation using the proven working REST API approach.
        
        🎯 PROVEN WORKING FORMAT (based on successful testing):
        - Uses simple string values: "4h", "2d", "30m", "1w"
        - NO complex objects or duration formats needed
        
        ✅ EXAMPLES THAT WORK:
        - update_issue_estimation("DEMO-123", "4h")     # 4 hours
        - update_issue_estimation("PROJECT-456", "2d")  # 2 days
        - update_issue_estimation("TASK-789", "30m")    # 30 minutes
        
        🔧 WHAT HAPPENS UNDER THE HOOD:
        - Direct Field Update API with format {"customFields": [{"name": "Estimation", "value": "4h"}]}
        - Simple time string values proven to work reliably
        - Smart error handling with estimation-specific guidance
        
        FORMAT: update_issue_estimation(issue_id="DEMO-123", estimation="4h")
        
        Args:
            issue_id: The issue identifier (e.g., "DEMO-123", "PROJECT-456")
            estimation: Time estimate (e.g., "4h", "2d", "30m", "1w", "3d 5h")
            
        Returns:
            JSON string with the updated issue information and success details
            
        Time Formats: "30m" (minutes), "4h" (hours), "2d" (days), "1w" (weeks), "3d 5h" (combined)
        """
        try:
            if not issue_id or not estimation:
                return format_json_response({
                    "error": "Both issue ID and estimation are required"
                })
            
            logger.info(f"Updating issue {issue_id} estimation to '{estimation}' using proven simple string format")
            
            # Use the proven simple string format for custom field updates
            from youtrack_mcp.tools.issues.custom_fields import CustomFields
            custom_fields_handler = CustomFields(self.issues_api, self.projects_api)
            
            result = custom_fields_handler.update_custom_fields(
                issue_id=issue_id,
                custom_fields={"Estimation": estimation}
            )
            
            # Parse the result to provide estimation-specific feedback
            result_data = json.loads(result) if isinstance(result, str) else result
            
            if result_data.get("status") == "success":
                return format_json_response({
                    "status": "success",
                    "message": f"Successfully updated issue {issue_id} estimation to '{estimation}'",
                    "issue_id": issue_id,
                    "estimation": estimation,
                    "api_method": "Direct Field Update API",
                    "updated_fields": result_data.get("updated_fields", ["Estimation"]),
                    "issue_data": result_data.get("issue_data", {})
                })
            else:
                # Handle error case with estimation-specific guidance
                error_msg = result_data.get("error", "Unknown error")
                return format_json_response({
                    "error": f"Estimation update failed: {error_msg}",
                    "issue_id": issue_id,
                    "target_estimation": estimation,
                    "troubleshooting": [
                        "Use simple time formats: '4h', '2d', '30m', '1w'",
                        "Combine units: '3d 5h' for 3 days 5 hours",
                        "Check if Estimation field exists in your project",
                        "Verify you have permissions to update time estimates"
                    ],
                    "format_examples": [
                        "30m (30 minutes)",
                        "4h (4 hours)", 
                        "2d (2 days)",
                        "1w (1 week)",
                        "3d 5h (3 days 5 hours)"
                    ]
                })
                
        except Exception as e:
            logger.exception(f"Error updating estimation for issue {issue_id}")
            return format_json_response({
                "error": str(e),
                "issue_id": issue_id,
                "target_estimation": estimation,
                "suggestion": "Check issue ID format and use simple time format like '4h' or '2d'"
            })

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for dedicated update functions."""
        return {
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
            }
        } 