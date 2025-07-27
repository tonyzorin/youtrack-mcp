"""
YouTrack Issue Attachments Module.

This module contains functions for handling issue attachments and raw data access:
- Raw issue data retrieval bypassing Pydantic models
- Attachment content access with base64 encoding
- Comprehensive attachment metadata retrieval
- File size analysis and format conversion

These functions enable file handling and detailed data access within YouTrack workflows.
"""

import json
import base64
import logging
from typing import Any, Dict

from youtrack_mcp.mcp_wrappers import sync_wrapper
from youtrack_mcp.utils import format_json_response

logger = logging.getLogger(__name__)


class Attachments:
    """Issue attachment and raw data access functions."""

    def __init__(self, issues_api, projects_api):
        """Initialize with API clients."""
        self.issues_api = issues_api
        self.projects_api = projects_api
        self.client = issues_api.client  # Direct access for raw API calls

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
                    ) if len(content) > 0 else 0.0,
                    "status": "success",
                }
            )
        except Exception as e:
            logger.exception(
                f"Error getting attachment content for issue {issue_id}, attachment {attachment_id}"
            )
            return format_json_response({"error": str(e), "status": "error"})

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions for attachment functions."""
        return {
            "get_issue_raw": {
                "description": "Get comprehensive raw issue data bypassing Pydantic models, including all fields, custom fields, attachments, and comments. Useful for detailed data analysis or when structured models are insufficient. Example: get_issue_raw(issue_id='DEMO-123')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier like 'DEMO-123' or 'PROJECT-456'"
                }
            },
            "get_attachment_content": {
                "description": "Download and retrieve attachment content as base64-encoded data with comprehensive metadata including file size analysis and format information. Supports files up to 10MB. Example: get_attachment_content(issue_id='DEMO-123', attachment_id='1-456')",
                "parameter_descriptions": {
                    "issue_id": "Issue identifier containing the attachment like 'DEMO-123'",
                    "attachment_id": "Attachment identifier from issue attachments list like '1-456' or '2-789'"
                }
            }
        } 