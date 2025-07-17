"""
Unit tests for YouTrack Users API (api/users.py).

Tests the User model and UsersClient functionality including user retrieval,
search, and permission checking.
"""

import pytest
from unittest.mock import Mock, patch
from youtrack_mcp.api.users import User, UsersClient
from youtrack_mcp.api.client import YouTrackClient


class TestUserModel:
    """Test the User model."""

    def test_user_model_basic_creation(self):
        """Test creating a basic User model."""
        user_data = {
            "id": "user-123",
            "login": "testuser",
            "name": "Test User",
            "email": "test@example.com"
        }
        user = User.model_validate(user_data)
        
        assert user.id == "user-123"
        assert user.login == "testuser" 
        assert user.name == "Test User"
        assert user.email == "test@example.com"

    def test_user_model_with_all_fields(self):
        """Test creating a User model with all possible fields."""
        user_data = {
            "id": "user-456",
            "login": "fulluser",
            "name": "Full User",
            "email": "full@example.com",
            "jabber": "full@jabber.com",
            "ring_id": "ring-123",
            "guest": False,
            "online": True,
            "banned": False
        }
        user = User.model_validate(user_data)
        
        assert user.id == "user-456"
        assert user.login == "fulluser"
        assert user.name == "Full User"
        assert user.email == "full@example.com"
        assert user.jabber == "full@jabber.com"
        assert user.ring_id == "ring-123"
        assert user.guest is False
        assert user.online is True
        assert user.banned is False

    def test_user_model_minimal_required_fields(self):
        """Test User model with only required fields."""
        user_data = {"id": "user-minimal"}
        user = User.model_validate(user_data)
        
        assert user.id == "user-minimal"
        assert user.login is None
        assert user.name is None
        assert user.email is None

    def test_user_model_extra_fields_allowed(self):
        """Test that User model allows extra fields."""
        user_data = {
            "id": "user-extra",
            "login": "extrauser",
            "custom_field": "custom_value",
            "profile": {"avatar": "http://example.com/avatar.jpg"}
        }
        user = User.model_validate(user_data)
        
        assert user.id == "user-extra"
        assert user.login == "extrauser"
        # Extra fields should be accessible
        assert hasattr(user, "custom_field")
        assert hasattr(user, "profile")


class TestUsersClientInitialization:
    """Test UsersClient initialization."""

    def test_users_client_initialization(self):
        """Test UsersClient initialization."""
        mock_client = Mock(spec=YouTrackClient)
        users_client = UsersClient(mock_client)
        
        assert users_client.client == mock_client


class TestUsersClientGetCurrentUser:
    """Test getting current user."""

    def test_get_current_user_success(self):
        """Test successful current user retrieval."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = {
            "id": "current-user",
            "login": "currentuser",
            "name": "Current User",
            "email": "current@example.com"
        }
        
        users_client = UsersClient(mock_client)
        user = users_client.get_current_user()
        
        assert isinstance(user, User)
        assert user.id == "current-user"
        assert user.login == "currentuser"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args[0][0]
        assert "users/me" in call_args
        assert "fields=" in call_args

    def test_get_current_user_api_error(self):
        """Test current user retrieval with API error."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.side_effect = Exception("API Error")
        
        users_client = UsersClient(mock_client)
        
        with pytest.raises(Exception):
            users_client.get_current_user()


class TestUsersClientGetUser:
    """Test getting user by ID."""

    def test_get_user_success(self):
        """Test successful user retrieval by ID."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = {
            "id": "target-user",
            "login": "targetuser",
            "name": "Target User",
            "email": "target@example.com"
        }
        
        users_client = UsersClient(mock_client)
        user = users_client.get_user("target-user")
        
        assert isinstance(user, User)
        assert user.id == "target-user"
        assert user.login == "targetuser"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args[0][0]
        assert "users/target-user" in call_args
        assert "fields=" in call_args

    def test_get_user_not_found(self):
        """Test user retrieval when user not found."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.side_effect = Exception("User not found")
        
        users_client = UsersClient(mock_client)
        
        with pytest.raises(Exception):
            users_client.get_user("nonexistent-user")


class TestUsersClientSearchUsers:
    """Test user search functionality."""

    def test_search_users_success(self):
        """Test successful user search."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = [
            {
                "id": "search-user-1",
                "login": "searchuser1",
                "name": "Search User 1",
                "email": "search1@example.com"
            },
            {
                "id": "search-user-2", 
                "login": "searchuser2",
                "name": "Search User 2",
                "email": "search2@example.com"
            }
        ]
        
        users_client = UsersClient(mock_client)
        users = users_client.search_users("search", limit=10)
        
        assert len(users) == 2
        assert all(isinstance(user, User) for user in users)
        assert users[0].id == "search-user-1"
        assert users[1].id == "search-user-2"
        
        mock_client.get.assert_called_once_with(
            "users", 
            params={"query": "search", "$top": 10, "fields": "id,login,name,email,jabber,ringId,guest,online,banned"}
        )

    def test_search_users_empty_results(self):
        """Test user search with empty results."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = []
        
        users_client = UsersClient(mock_client)
        users = users_client.search_users("nonexistent")
        
        assert len(users) == 0
        assert users == []

    def test_search_users_with_invalid_data(self):
        """Test user search with some invalid user data."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = [
            {
                "id": "valid-user",
                "login": "validuser",
                "name": "Valid User"
            },
            {
                # Invalid data - missing required id field
                "login": "invaliduser"
            },
            {
                "id": "another-valid-user",
                "login": "anotheruser"
            }
        ]
        
        users_client = UsersClient(mock_client)
        
        # Should log warning for invalid user but continue processing
        with patch('youtrack_mcp.api.users.logging.getLogger') as mock_logger:
            users = users_client.search_users("test")
            
            # Should only return valid users
            assert len(users) == 2
            assert users[0].id == "valid-user"
            assert users[1].id == "another-valid-user"
            
            # Should have logged a warning
            mock_logger.return_value.warning.assert_called_once()

    def test_search_users_default_limit(self):
        """Test user search with default limit."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = []
        
        users_client = UsersClient(mock_client)
        users_client.search_users("test")
        
        # Check that default limit of 10 was used
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["$top"] == 10


class TestUsersClientGetUserByLogin:
    """Test getting user by login."""

    def test_get_user_by_login_found(self):
        """Test getting user by login when user exists."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = [
            {
                "id": "login-user",
                "login": "loginuser",
                "name": "Login User",
                "email": "login@example.com"
            }
        ]
        
        users_client = UsersClient(mock_client)
        user = users_client.get_user_by_login("loginuser")
        
        assert user is not None
        assert isinstance(user, User)
        assert user.id == "login-user"
        assert user.login == "loginuser"
        
        # Should have called search with login query
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["query"] == "login: loginuser"
        assert call_args[1]["params"]["$top"] == 1

    def test_get_user_by_login_not_found(self):
        """Test getting user by login when user doesn't exist."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = []
        
        users_client = UsersClient(mock_client)
        user = users_client.get_user_by_login("nonexistentuser")
        
        assert user is None


class TestUsersClientGetUserGroups:
    """Test getting user groups."""

    def test_get_user_groups_success(self):
        """Test successful user groups retrieval."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = [
            {"id": "group-1", "name": "Developers"},
            {"id": "group-2", "name": "Administrators"}
        ]
        
        users_client = UsersClient(mock_client)
        groups = users_client.get_user_groups("user-123")
        
        assert len(groups) == 2
        assert groups[0]["name"] == "Developers"
        assert groups[1]["name"] == "Administrators"
        
        mock_client.get.assert_called_once_with("users/user-123/groups")

    def test_get_user_groups_empty(self):
        """Test user groups retrieval with no groups."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = []
        
        users_client = UsersClient(mock_client)
        groups = users_client.get_user_groups("user-123")
        
        assert groups == []

    def test_get_user_groups_api_error(self):
        """Test user groups retrieval with API error."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.side_effect = Exception("API Error")
        
        users_client = UsersClient(mock_client)
        
        with pytest.raises(Exception):
            users_client.get_user_groups("user-123")


class TestUsersClientCheckUserPermissions:
    """Test checking user permissions."""

    def test_check_user_permissions_has_permission(self):
        """Test permission check when user has permission."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = [
            {"id": "group-1", "name": "Developers"},
            {"id": "group-2", "name": "Administrators"}
        ]
        
        users_client = UsersClient(mock_client)
        
        # Check for "admin" permission (should match "Administrators")
        has_permission = users_client.check_user_permissions("user-123", "admin")
        
        assert has_permission is True

    def test_check_user_permissions_no_permission(self):
        """Test permission check when user doesn't have permission."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = [
            {"id": "group-1", "name": "Developers"},
            {"id": "group-2", "name": "Users"}
        ]
        
        users_client = UsersClient(mock_client)
        
        # Check for "admin" permission (should not match any group)
        has_permission = users_client.check_user_permissions("user-123", "admin")
        
        assert has_permission is False

    def test_check_user_permissions_api_error(self):
        """Test permission check with API error."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.side_effect = Exception("API Error")
        
        users_client = UsersClient(mock_client)
        
        # Should return False on error (assume no permission)
        has_permission = users_client.check_user_permissions("user-123", "admin")
        
        assert has_permission is False

    def test_check_user_permissions_case_insensitive(self):
        """Test permission check is case insensitive."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = [
            {"id": "group-1", "name": "ADMINISTRATORS"}
        ]
        
        users_client = UsersClient(mock_client)
        
        # Check for "admin" permission (should match "ADMINISTRATORS")
        has_permission = users_client.check_user_permissions("user-123", "admin")
        
        assert has_permission is True

    def test_check_user_permissions_group_without_name(self):
        """Test permission check with group that has no name."""
        mock_client = Mock(spec=YouTrackClient)
        mock_client.get.return_value = [
            {"id": "group-1"},  # No name field
            {"id": "group-2", "name": "Users"}
        ]
        
        users_client = UsersClient(mock_client)
        
        # Should handle missing name gracefully
        has_permission = users_client.check_user_permissions("user-123", "admin")
        
        assert has_permission is False 