import json
import logging
from typing import Dict, Any, List, Optional

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
    
    @sync_wrapper
    def get_current_user(self) -> str:
        """
        Get information about the currently authenticated user.
        
        FORMAT: get_current_user()
        
        Returns:
            JSON string with current user information
        """
        try:
            user = self.users_api.get_current_user()
            return format_json_response(user.model_dump())
        except Exception as e:
            logger.exception("Error getting current user")
            return json.dumps({"error": str(e)})
    
    @sync_wrapper
    def get_user(self, user_id: str = None, user: str = None) -> str:
        """
        Get information about a specific user.
        
        FORMAT: get_user(user_id="1-1")
        
        Args:
            user_id: The user ID
            user: Alternative parameter name for user_id
            
        Returns:
            JSON string with user information
        """
        try:
            # Use either user_id or user parameter
            user_identifier = user_id or user
            if not user_identifier:
                return json.dumps({"error": "User ID is required"})
                
            user_obj = self.users_api.get_user(user_identifier)
            
            # Handle both Pydantic models and dictionaries in the response
            if user_obj is None:
                return json.dumps({"error": "User not found"})
            
            if hasattr(user_obj, 'model_dump'):
                result = user_obj.model_dump()
            else:
                result = user_obj  # Assume it's already a dict
                
            return format_json_response(result)
        except Exception as e:
            logger.exception(f"Error getting user {user_id or user}")
            return json.dumps({"error": str(e)})
    
    @sync_wrapper
    def get_user_by_login(self, login: str) -> str:
        """
        Get a user by their login name.
        
        FORMAT: get_user_by_login(login="johndoe")
        
        Args:
            login: The user's login name
            
        Returns:
            JSON string with user information
        """
        try:
            if not login:
                return json.dumps({"error": "Login is required"})
                
            user = self.users_api.get_user_by_login(login)
            
            # Handle both Pydantic models and dictionaries in the response
            if user is None:
                return json.dumps({"error": "User not found"})
            
            if hasattr(user, 'model_dump'):
                result = user.model_dump()
            else:
                result = user  # Assume it's already a dict
                
            return format_json_response(result)
        except Exception as e:
            logger.exception(f"Error getting user with login {login}")
            return json.dumps({"error": str(e)})
    
    @sync_wrapper
    def get_user_groups(self, user_id: str = None, user: str = None) -> str:
        """
        Get groups for a user.
        
        FORMAT: get_user_groups(user_id="1-1")
        
        Args:
            user_id: The user ID
            user: Alternative parameter name for user_id
            
        Returns:
            JSON string with user groups
        """
        try:
            # Use either user_id or user parameter
            user_identifier = user_id or user
            if not user_identifier:
                return json.dumps({"error": "User ID is required"})
                
            groups = self.users_api.get_user_groups(user_identifier)
            
            # Handle various response formats safely
            if groups is None:
                return json.dumps([])
            
            # If it's a dictionary (direct API response)
            if isinstance(groups, dict):
                return format_json_response(groups)
            
            # If it's a list of objects
            try:
                result = []
                # Try to iterate, but handle errors safely
                for group in groups:
                    if hasattr(group, 'model_dump'):
                        result.append(group.model_dump())
                    elif isinstance(group, dict):
                        result.append(group)
                    else:
                        # Last resort: convert to string
                        result.append(str(group))
                return format_json_response(result)
            except Exception as e:
                # If we can't iterate, return the raw string representation
                logger.warning(f"Could not process groups response: {str(e)}")
                return json.dumps({"groups": str(groups)})
        except Exception as e:
            logger.exception(f"Error getting groups for user {user_id or user}")
            return json.dumps({"error": str(e)})
    
    @sync_wrapper
    def search_users(self, query: str, limit: int = 10) -> str:
        """
        Search for users using YouTrack query.
        
        FORMAT: search_users(query="John", limit=10)
        
        Args:
            query: The search query
            limit: Maximum number of users to return (default: 10)
            
        Returns:
            JSON string with matching users
        """
        try:
            users = self.users_api.search_users(query, limit=limit)
            return format_json_response([u.model_dump() for u in users])
        except Exception as e:
            logger.exception(f"Error searching users with query {query}")
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
                "description": "Get information about the currently authenticated user. FORMAT: get_current_user()",
                "parameters": {}
            },
            "get_user": {
                "function": self.get_user,
                "description": "Get information about a specific user. FORMAT: get_user(user_id=\"1-1\")",
                "parameters": {
                    "user_id": "The user ID",
                    "user": "Alternative parameter name for user_id"
                }
            },
            "get_user_by_login": {
                "function": self.get_user_by_login,
                "description": "Get a user by their login name. FORMAT: get_user_by_login(login=\"johndoe\")",
                "parameters": {
                    "login": "The user's login name"
                }
            },
            "get_user_groups": {
                "function": self.get_user_groups,
                "description": "Get groups for a user. FORMAT: get_user_groups(user_id=\"1-1\")",
                "parameters": {
                    "user_id": "The user ID",
                    "user": "Alternative parameter name for user_id"
                }
            },
            "search_users": {
                "function": self.search_users,
                "description": "Search for users using YouTrack query. FORMAT: search_users(query=\"John\", limit=10)",
                "parameters": {
                    "query": "The search query",
                    "limit": "Maximum number of users to return (optional, default: 10)"
                }
            }
        } 