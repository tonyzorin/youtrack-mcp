"""
YouTrack Knowledge Base Spaces MCP tools.
"""

import logging
from typing import Any, Dict

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.spaces import SpacesClient
from youtrack_mcp.mcp_wrappers import sync_wrapper
from youtrack_mcp.utils import format_json_response

logger = logging.getLogger(__name__)


class SpacesTools:
    """Spaces-related MCP tools."""

    def __init__(self):
        self.client = YouTrackClient()
        self.spaces_api = SpacesClient(self.client)

    def close(self) -> None:
        if hasattr(self.client, "close"):
            self.client.close()

    @sync_wrapper
    def get_space(self, space_id: str, fields: str = "id,name") -> str:
        """Get a single KB space by id."""
        try:
            if not space_id:
                return format_json_response({"error": "Space ID is required"})
            space = self.spaces_api.get_space(space_id, fields)
            return format_json_response(
                space.model_dump() if hasattr(space, "model_dump") else space
            )
        except Exception as e:
            logger.exception(f"Error getting space {space_id}")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def list_spaces(self, fields: str = "id,name", top: int = 50, skip: int = 0) -> str:
        """List KB spaces."""
        try:
            spaces = self.spaces_api.list_spaces(fields=fields, top=top, skip=skip)
            result = [s.model_dump() if hasattr(s, "model_dump") else s for s in spaces]
            return format_json_response(result)
        except Exception as e:
            logger.exception("Error listing spaces")
            return format_json_response({"error": str(e)})

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        return {
            "get_space": {
                "description": 'Get a Knowledge Base space by id. Example: get_space(space_id="0-1")',
                "parameter_descriptions": {
                    "space_id": "Space id like '0-1'",
                    "fields": "Fields to include (default: id,name)",
                },
            },
            "list_spaces": {
                "description": "List Knowledge Base spaces. Example: list_spaces(top=50)",
                "parameter_descriptions": {
                    "fields": "Fields to include (default: id,name)",
                    "top": "Max results (default: 50)",
                    "skip": "Offset for pagination (default: 0)",
                },
            },
        }
