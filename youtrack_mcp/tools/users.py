"""
YouTrack User MCP tools.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.users import UsersClient

logger = logging.getLogger(__name__)


class UserTools:
    """User-related MCP tools."""
    
    def __init__(self):
        """Initialize the user tools."""
        self.client = YouTrackClient()
        self.users_api = UsersClient(self.client)
    
    def get_current_user(self) -> str:
        """
        Get information about the currently authenticated user.
        
        Returns:
            JSON string with user information
        """
        try:
            # Get user data with all fields
            fields = "id,login,name,email,jabber,ringId,guest,online,banned"
            response = self.client.get(f"users/me?fields={fields}")
            return json.dumps(response, indent=2)
        except Exception as e:
            logger.exception("Error getting current user")
            return json.dumps({"error": str(e)})
    
    def get_user(self, user_id: str) -> str:
        """
        Get information about a specific user.
        
        Args:
            user_id: The user ID
            
        Returns:
            JSON string with user information
        """
        try:
            # Get user data with all fields
            fields = "id,login,name,email,jabber,ringId,guest,online,banned"
            response = self.client.get(f"users/{user_id}?fields={fields}")
            return json.dumps(response, indent=2)
        except Exception as e:
            logger.exception(f"Error getting user {user_id}")
            return json.dumps({"error": str(e)})
    
    def search_users(self, query: str, limit: int = 10) -> str:
        """
        Search for users using YouTrack query.
        
        Args:
            query: The search query (name, login, or email)
            limit: Maximum number of users to return
            
        Returns:
            JSON string with matching users
        """
        try:
            # Request with explicit fields to get complete data
            fields = "id,login,name,email,jabber,ringId,guest,online,banned"
            params = {"query": query, "$top": limit, "fields": fields}
            raw_users = self.client.get("users", params=params)
            
            # Return the raw users data directly
            return json.dumps(raw_users, indent=2)
        except Exception as e:
            logger.exception(f"Error searching users with query: {query}")
            return json.dumps({"error": str(e)})
    
    def get_user_by_login(self, login: str) -> str:
        """
        Get a user by their login name.
        
        Args:
            login: The user login name
            
        Returns:
            JSON string with user information
        """
        try:
            user = self.users_api.get_user_by_login(login)
            if user:
                return json.dumps(user.model_dump(), indent=2)
            else:
                return json.dumps({"error": f"User with login '{login}' not found"})
        except Exception as e:
            logger.exception(f"Error getting user by login: {login}")
            return json.dumps({"error": str(e)})
    
    def get_user_groups(self, user_id: str) -> str:
        """
        Get groups for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            JSON string with user groups
        """
        try:
            groups = self.users_api.get_user_groups(user_id)
            return json.dumps(groups, indent=2)
        except Exception as e:
            logger.exception(f"Error getting groups for user {user_id}")
            return json.dumps({"error": str(e)})
    
    def close(self) -> None:
        """Close the API client."""
        self.client.close()
    
    def get_tool_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the definitions of all user tools.
        
        Returns:
            Dictionary mapping tool names to their configuration
        """
        return {
            "get_current_user": {
                "function": self.get_current_user,
                "description": "Get information about the currently authenticated YouTrack user",
                "parameter_descriptions": {}
            },
            "get_user": {
                "function": self.get_user,
                "description": "Get information about a specific YouTrack user by ID",
                "parameter_descriptions": {
                    "user_id": "The user ID"
                }
            },
            "search_users": {
                "function": self.search_users,
                "description": "Search for YouTrack users",
                "parameter_descriptions": {
                    "query": "The search query (name, login, or email)",
                    "limit": "Maximum number of users to return (default: 10)"
                }
            },
            "get_user_by_login": {
                "function": self.get_user_by_login,
                "description": "Get a YouTrack user by login name",
                "parameter_descriptions": {
                    "login": "The user login name"
                }
            },
            "get_user_groups": {
                "function": self.get_user_groups,
                "description": "Get groups for a YouTrack user",
                "parameter_descriptions": {
                    "user_id": "The user ID"
                }
            }
        } 