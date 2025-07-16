"""
YouTrack User MCP tools.
"""

import logging
from typing import Any, Dict, Optional

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.users import UsersClient
from youtrack_mcp.mcp_wrappers import sync_wrapper
from youtrack_mcp.utils import format_json_response

logger = logging.getLogger(__name__)


class UserTools:
    """User-related MCP tools."""

    def __init__(self):
        """Initialize the user tools."""
        self.client = YouTrackClient()
        self.users_api = UsersClient(self.client)

    def close(self) -> None:
        """Close the user tools."""
        if hasattr(self.client, "close"):
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
            if hasattr(user, "model_dump"):
                result = user.model_dump()
            else:
                result = user  # Assume it's already a dict
            return format_json_response(result)
        except Exception as e:
            logger.exception("Error getting current user")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def get_user_by_id(self, user_id: str) -> str:
        """
        Get information about a specific user by ID or login.

        FORMAT: get_user_by_id(user_id="admin")

        Args:
            user_id: The user identifier (ID like 'user-123' or login like 'admin')

        Returns:
            JSON string with user information
        """
        try:
            if not user_id:
                return format_json_response({"error": "User ID is required"})

            user_obj = self.users_api.get_user(user_id)
            if hasattr(user_obj, "model_dump"):
                result = user_obj.model_dump()
            else:
                result = user_obj  # Assume it's already a dict
            return format_json_response(result)
        except Exception as e:
            logger.exception(f"Error getting user {user_id}")
            return format_json_response({"error": str(e)})

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
                if hasattr(user, "model_dump"):
                    result.append(user.model_dump())
                else:
                    result.append(user)  # Assume it's already a dict

            return format_json_response(result)
        except Exception as e:
            logger.exception(f"Error searching users with query: {query}")
            return format_json_response({"error": str(e)})

    @sync_wrapper
    def get_user_permissions(self, user_id: str = None) -> str:
        """
        Get permissions for a specific user.

        FORMAT: get_user_permissions(user_id="admin") or get_user_permissions() for current user

        Args:
            user_id: The user identifier (ID like 'user-123' or login like 'admin'). 
                    If not provided, gets permissions for current user.

        Returns:
            JSON string with user permissions
        """
        try:
            # If no user_id provided, get current user
            if not user_id:
                current_user = self.users_api.get_current_user()
                if hasattr(current_user, 'id'):
                    user_id = current_user.id
                elif hasattr(current_user, 'login'):
                    user_id = current_user.login
                else:
                    user_id = str(current_user)

            # Get user details which may include permission info
            user_details = self.users_api.get_user(user_id)
            
            # Convert User object to dictionary for JSON serialization
            if hasattr(user_details, 'model_dump'):
                user_details_dict = user_details.model_dump()
            elif hasattr(user_details, '__dict__'):
                user_details_dict = user_details.__dict__
            else:
                user_details_dict = str(user_details)
            
            # Try to get available permission info from user details
            permissions = {
                "user_id": user_id,
                "user_details": user_details_dict,
                "note": "User permissions shown through user details. Full group permissions API not available in YouTrack Cloud."
            }
            return format_json_response(permissions)
        except Exception as e:
            logger.exception(f"Error getting permissions for user {user_id}")
            return format_json_response({"error": str(e)})

    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get tool definitions with descriptions."""
        return {
            "get_current_user": {
                "description": "Get information about the currently authenticated user. Example: get_current_user()",
                "function": self.get_current_user,
                "parameter_descriptions": {},
            },
            "get_user_by_id": {
                "description": 'Get information about a specific user by their ID or login name. Example: get_user_by_id(user_id="admin")',
                "function": self.get_user_by_id,
                "parameter_descriptions": {
                    "user_id": "User identifier (ID like 'user-123' or login like 'admin')"
                },
            },
            "search_users": {
                "description": 'Search for users by name or login with a search term. Example: search_users(query="admin", limit=5)',
                "function": self.search_users,
                "parameter_descriptions": {
                    "query": "Search term to match user names or logins",
                    "limit": "Maximum number of users to return (default: 10)",
                },
            },
            "get_user_permissions": {
                "description": 'Get permissions for a specific user in the system. Example: get_user_permissions(user_id="admin")',
                "function": self.get_user_permissions,
                "parameter_descriptions": {
                    "user_id": "User identifier (ID like 'user-123' or login like 'admin')"
                },
            },
        }
