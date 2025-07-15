import json
import logging
from typing import Any, Dict

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.users import UsersClient
from youtrack_mcp.mcp_wrappers import sync_wrapper

logger = logging.getLogger(__name__)


class UserTools:
    """User-related MCP tools."""

    def __init__(self):
        """Initialize the user tools."""
        self.client = YouTrackClient()
        self.users_api = UsersClient(self.client)

    def close(self) -> None:
        """Close the user tools."""
        if hasattr(self.client, 'close'):
            self.client.close()

    @sync_wrapper
    def get_current_user(self) -> str:
        """
        Get information about the current user.

        FORMAT: get_current_user()

        Returns:
            JSON string with current user information
        """
        try:
            # Using 'me' endpoint to get current user info
            user = self.users_api.get_current_user()
            if hasattr(user, 'model_dump'):
                result = user.model_dump()
            else:
                result = user  # Assume it's already a dict
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception("Error getting current user")
            return json.dumps({"error": str(e)})

    @sync_wrapper
    def get_user_by_id(self, user_id: str = None, user: str = None) -> str:
        """
        Get information about a specific user by ID or login.

        FORMAT: get_user_by_id(user_id="user-123") or get_user_by_id(user="username")

        Args:
            user_id: The user ID (optional)
            user: The user login/username (optional)

        Returns:
            JSON string with user information
        """
        try:
            # Determine which parameter to use
            identifier = user_id or user
            if not identifier:
                return json.dumps({"error": "Either user_id or user parameter is required"})

            user_obj = self.users_api.get_user(identifier)
            if hasattr(user_obj, 'model_dump'):
                result = user_obj.model_dump()
            else:
                result = user_obj  # Assume it's already a dict
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception(f"Error getting user {identifier}")
            return json.dumps({"error": str(e)})

    @sync_wrapper
    def search_users(self, query: str = "", limit: int = 10) -> str:
        """
        Search for users by name or login.

        FORMAT: search_users(query="john", limit=10)

        Args:
            query: Search query for user name or login
            limit: Maximum number of results to return

        Returns:
            JSON string with list of matching users
        """
        try:
            users = self.users_api.search_users(query, limit)

            # Handle both Pydantic models and dictionaries in the response
            result = []
            for user in users:
                if hasattr(user, 'model_dump'):
                    result.append(user.model_dump())
                else:
                    result.append(user)  # Assume it's already a dict

            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception(f"Error searching users with query: {query}")
            return json.dumps({"error": str(e)})

    @sync_wrapper
    def get_user_permissions(self, user_id: str = None, user: str = None) -> str:
        """
        Get permissions for a specific user.

        FORMAT: get_user_permissions(user_id="user-123") or get_user_permissions(user="username")

        Args:
            user_id: The user ID (optional)
            user: The user login/username (optional)

        Returns:
            JSON string with user permissions
        """
        try:
            # Determine which parameter to use
            identifier = user_id or user
            if not identifier:
                return json.dumps({"error": "Either user_id or user parameter is required"})

            permissions = self.users_api.get_user_permissions(identifier)
            return json.dumps(permissions, indent=2)
        except Exception as e:
            logger.exception(f"Error getting permissions for user {identifier}")
            return json.dumps({"error": str(e)})

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions with descriptions."""
        return {
            "get_current_user": {
                "description": "Get information about the current user",
                "function": self.get_current_user,
                "parameter_descriptions": {}
            },

            "get_user_by_id": {
                "description": "Get information about a specific user by ID or login",
                "function": self.get_user_by_id,
                "parameter_descriptions": {
                    "user_id": "The user ID (e.g., 'user-123')",
                    "user": "The user login/username (alternative to user_id)"
                }
            },

            "search_users": {
                "description": "Search for users by name or login",
                "function": self.search_users,
                "parameter_descriptions": {
                    "query": "Search query for user name or login",
                    "limit": "Maximum number of results (default: 10)"
                }
            },

            "get_user_permissions": {
                "description": "Get permissions for a specific user",
                "function": self.get_user_permissions,
                "parameter_descriptions": {
                    "user_id": "The user ID (e.g., 'user-123')",
                    "user": "The user login/username (alternative to user_id)"
                }
            }
        } 