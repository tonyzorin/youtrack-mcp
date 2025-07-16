"""
Tests for youtrack_mcp/tools/users.py with proper mocking
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from youtrack_mcp.tools.users import UserTools


class TestUserTools:
    """Test UserTools class with proper mocking."""

    @patch.dict('os.environ', {'YOUTRACK_URL': 'https://test.youtrack.cloud', 'YOUTRACK_API_TOKEN': 'test-token'})
    @patch('youtrack_mcp.tools.users.YouTrackClient')
    @patch('youtrack_mcp.tools.users.UsersClient')
    def setup_method(self, method, mock_users_client, mock_youtrack_client):
        """Set up test fixtures."""
        # Mock the client initialization
        self.mock_client = Mock()
        mock_youtrack_client.return_value = self.mock_client
        
        self.mock_users_api = Mock()
        mock_users_client.return_value = self.mock_users_api
        
        self.user_tools = UserTools()

    def teardown_method(self):
        """Clean up after tests."""
        if hasattr(self.user_tools, 'close'):
            self.user_tools.close()

    @patch.dict('os.environ', {'YOUTRACK_URL': 'https://test.youtrack.cloud', 'YOUTRACK_API_TOKEN': 'test-token'})
    @patch('youtrack_mcp.tools.users.YouTrackClient')
    @patch('youtrack_mcp.tools.users.UsersClient')
    def test_init(self, mock_users_client, mock_youtrack_client):
        """Test UserTools initialization."""
        mock_client_instance = Mock()
        mock_youtrack_client.return_value = mock_client_instance
        
        user_tools = UserTools()
        
        mock_youtrack_client.assert_called_once()
        mock_users_client.assert_called_once_with(mock_client_instance)

    def test_close_with_close_method(self):
        """Test close method when client has close method."""
        mock_client = Mock()
        mock_client.close = Mock()
        self.user_tools.client = mock_client
        
        self.user_tools.close()
        
        mock_client.close.assert_called_once()

    def test_close_without_close_method(self):
        """Test close method when client doesn't have close method."""
        mock_client = Mock()
        del mock_client.close  # Remove close method
        self.user_tools.client = mock_client
        
        # Should not raise an exception
        self.user_tools.close()

    def test_get_current_user_success_pydantic_model(self):
        """Test get_current_user with Pydantic model response."""
        mock_user = Mock()
        mock_user.model_dump.return_value = {
            "id": "user-123",
            "login": "admin",
            "name": "Administrator"
        }
        self.mock_users_api.get_current_user = Mock(return_value=mock_user)
        
        result = self.user_tools.get_current_user()
        
        parsed_result = json.loads(result)
        assert parsed_result["id"] == "user-123"
        assert parsed_result["login"] == "admin"
        assert parsed_result["name"] == "Administrator"

    def test_get_current_user_success_dict_response(self):
        """Test get_current_user with dict response."""
        mock_user_dict = {
            "id": "user-456",
            "login": "testuser",
            "name": "Test User"
        }
        self.mock_users_api.get_current_user = Mock(return_value=mock_user_dict)
        
        result = self.user_tools.get_current_user()
        
        parsed_result = json.loads(result)
        assert parsed_result["id"] == "user-456"
        assert parsed_result["login"] == "testuser"
        assert parsed_result["name"] == "Test User"

    def test_get_current_user_exception(self):
        """Test get_current_user with exception."""
        self.mock_users_api.get_current_user = Mock(side_effect=Exception("API Error"))
        
        result = self.user_tools.get_current_user()
        
        parsed_result = json.loads(result)
        assert "error" in parsed_result
        assert "API Error" in parsed_result["error"]

    def test_get_user_by_id_success_pydantic_model(self):
        """Test get_user_by_id with Pydantic model response."""
        mock_user = Mock()
        mock_user.model_dump.return_value = {
            "id": "user-123",
            "login": "admin",
            "name": "Administrator"
        }
        self.mock_users_api.get_user = Mock(return_value=mock_user)
        
        result = self.user_tools.get_user_by_id("admin")
        
        parsed_result = json.loads(result)
        assert parsed_result["id"] == "user-123"
        assert parsed_result["login"] == "admin"
        self.mock_users_api.get_user.assert_called_once_with("admin")

    def test_get_user_by_id_success_dict_response(self):
        """Test get_user_by_id with dict response."""
        mock_user_dict = {
            "id": "user-456",
            "login": "testuser",
            "name": "Test User"
        }
        self.mock_users_api.get_user = Mock(return_value=mock_user_dict)
        
        result = self.user_tools.get_user_by_id("testuser")
        
        parsed_result = json.loads(result)
        assert parsed_result["id"] == "user-456"
        assert parsed_result["login"] == "testuser"

    def test_get_user_by_id_empty_user_id(self):
        """Test get_user_by_id with empty user_id."""
        result = self.user_tools.get_user_by_id("")
        
        parsed_result = json.loads(result)
        assert "error" in parsed_result
        assert "User ID is required" in parsed_result["error"]

    def test_get_user_by_id_none_user_id(self):
        """Test get_user_by_id with None user_id."""
        result = self.user_tools.get_user_by_id(None)
        
        parsed_result = json.loads(result)
        assert "error" in parsed_result
        assert "User ID is required" in parsed_result["error"]

    def test_get_user_by_id_exception(self):
        """Test get_user_by_id with exception."""
        self.mock_users_api.get_user = Mock(side_effect=Exception("User not found"))
        
        result = self.user_tools.get_user_by_id("nonexistent")
        
        parsed_result = json.loads(result)
        assert "error" in parsed_result
        assert "User not found" in parsed_result["error"]

    def test_search_users_success_pydantic_models(self):
        """Test search_users with Pydantic model responses."""
        mock_user1 = Mock()
        mock_user1.model_dump.return_value = {"id": "user-1", "login": "admin1"}
        mock_user2 = Mock()
        mock_user2.model_dump.return_value = {"id": "user-2", "login": "admin2"}
        
        self.mock_users_api.search_users = Mock(return_value=[mock_user1, mock_user2])
        
        result = self.user_tools.search_users("admin", 5)
        
        parsed_result = json.loads(result)
        assert len(parsed_result) == 2
        assert parsed_result[0]["id"] == "user-1"
        assert parsed_result[1]["id"] == "user-2"
        self.mock_users_api.search_users.assert_called_once_with("admin", 5)

    def test_search_users_success_dict_responses(self):
        """Test search_users with dict responses."""
        mock_users = [
            {"id": "user-1", "login": "admin1"},
            {"id": "user-2", "login": "admin2"}
        ]
        self.mock_users_api.search_users = Mock(return_value=mock_users)
        
        result = self.user_tools.search_users("admin")
        
        parsed_result = json.loads(result)
        assert len(parsed_result) == 2
        assert parsed_result[0]["id"] == "user-1"
        assert parsed_result[1]["id"] == "user-2"
        self.mock_users_api.search_users.assert_called_once_with("admin", 10)

    def test_search_users_default_parameters(self):
        """Test search_users with default parameters."""
        self.mock_users_api.search_users = Mock(return_value=[])
        
        result = self.user_tools.search_users()
        
        self.mock_users_api.search_users.assert_called_once_with("", 10)

    def test_search_users_exception(self):
        """Test search_users with exception."""
        self.mock_users_api.search_users = Mock(side_effect=Exception("Search failed"))
        
        result = self.user_tools.search_users("admin")
        
        parsed_result = json.loads(result)
        assert "error" in parsed_result
        assert "Search failed" in parsed_result["error"]

    def test_get_user_permissions_with_user_id_pydantic(self):
        """Test get_user_permissions with specific user_id and Pydantic model."""
        mock_user = Mock()
        mock_user.model_dump.return_value = {
            "id": "user-123",
            "login": "admin",
            "groups": ["admin-group"]
        }
        self.mock_users_api.get_user = Mock(return_value=mock_user)
        
        result = self.user_tools.get_user_permissions("admin")
        
        parsed_result = json.loads(result)
        assert parsed_result["user_id"] == "admin"
        assert "user_details" in parsed_result
        assert parsed_result["user_details"]["id"] == "user-123"
        assert "note" in parsed_result

    def test_get_user_permissions_with_user_id_dict(self):
        """Test get_user_permissions with specific user_id and dict response."""
        mock_user = Mock(spec=[])  # Create a Mock without model_dump
        mock_user.__dict__ = {
            "id": "user-123",
            "login": "admin",
            "groups": ["admin-group"]
        }
        self.mock_users_api.get_user = Mock(return_value=mock_user)
        
        result = self.user_tools.get_user_permissions("admin")
        
        parsed_result = json.loads(result)
        assert parsed_result["user_id"] == "admin"
        assert "user_details" in parsed_result
        assert parsed_result["user_details"]["id"] == "user-123"

    def test_get_user_permissions_with_user_id_string_fallback(self):
        """Test get_user_permissions with user_id and string fallback."""
        mock_user = "simple_string_user"
        self.mock_users_api.get_user = Mock(return_value=mock_user)
        
        result = self.user_tools.get_user_permissions("admin")
        
        parsed_result = json.loads(result)
        assert parsed_result["user_id"] == "admin"
        assert parsed_result["user_details"] == "simple_string_user"

    def test_get_user_permissions_no_user_id_current_user_with_id(self):
        """Test get_user_permissions without user_id, current user has id."""
        mock_current_user = Mock()
        mock_current_user.id = "current-user-123"
        self.mock_users_api.get_current_user = Mock(return_value=mock_current_user)
        
        mock_user_details = Mock()
        mock_user_details.model_dump.return_value = {"id": "current-user-123", "login": "current"}
        self.mock_users_api.get_user = Mock(return_value=mock_user_details)
        
        result = self.user_tools.get_user_permissions()
        
        parsed_result = json.loads(result)
        assert parsed_result["user_id"] == "current-user-123"
        self.mock_users_api.get_user.assert_called_once_with("current-user-123")

    def test_get_user_permissions_no_user_id_current_user_with_login(self):
        """Test get_user_permissions without user_id, current user has login."""
        mock_current_user = Mock()
        mock_current_user.login = "current-login"
        # Remove id attribute to test login fallback
        del mock_current_user.id
        self.mock_users_api.get_current_user = Mock(return_value=mock_current_user)
        
        mock_user_details = Mock()
        mock_user_details.model_dump.return_value = {"login": "current-login"}
        self.mock_users_api.get_user = Mock(return_value=mock_user_details)
        
        result = self.user_tools.get_user_permissions()
        
        parsed_result = json.loads(result)
        assert parsed_result["user_id"] == "current-login"
        self.mock_users_api.get_user.assert_called_once_with("current-login")

    def test_get_user_permissions_no_user_id_string_fallback(self):
        """Test get_user_permissions without user_id, string fallback."""
        mock_current_user = "string_user"
        self.mock_users_api.get_current_user = Mock(return_value=mock_current_user)
        
        mock_user_details = Mock()
        mock_user_details.model_dump.return_value = {"string": "representation"}
        self.mock_users_api.get_user = Mock(return_value=mock_user_details)
        
        result = self.user_tools.get_user_permissions()
        
        parsed_result = json.loads(result)
        assert parsed_result["user_id"] == "string_user"

    def test_get_user_permissions_exception(self):
        """Test get_user_permissions with exception."""
        self.mock_users_api.get_current_user = Mock(side_effect=Exception("Permission error"))
        
        result = self.user_tools.get_user_permissions()
        
        parsed_result = json.loads(result)
        assert "error" in parsed_result
        assert "Permission error" in parsed_result["error"]

    def test_get_tool_definitions(self):
        """Test get_tool_definitions method."""
        definitions = self.user_tools.get_tool_definitions()
        
        expected_tools = [
            "get_current_user",
            "get_user_by_id", 
            "search_users",
            "get_user_permissions"
        ]
        
        for tool in expected_tools:
            assert tool in definitions
            assert "description" in definitions[tool]
            assert "function" in definitions[tool]
            assert "parameter_descriptions" in definitions[tool]
        
        # Test specific tool has correct function reference
        assert definitions["get_current_user"]["function"] == self.user_tools.get_current_user
        assert definitions["get_user_by_id"]["function"] == self.user_tools.get_user_by_id
        assert definitions["search_users"]["function"] == self.user_tools.search_users
        assert definitions["get_user_permissions"]["function"] == self.user_tools.get_user_permissions

    def test_get_tool_definitions_parameter_descriptions(self):
        """Test that tool definitions have proper parameter descriptions."""
        definitions = self.user_tools.get_tool_definitions()
        
        # get_current_user should have no parameters
        assert len(definitions["get_current_user"]["parameter_descriptions"]) == 0
        
        # get_user_by_id should have user_id parameter
        assert "user_id" in definitions["get_user_by_id"]["parameter_descriptions"]
        
        # search_users should have query and limit parameters
        search_params = definitions["search_users"]["parameter_descriptions"]
        assert "query" in search_params
        assert "limit" in search_params
        
        # get_user_permissions should have user_id parameter
        assert "user_id" in definitions["get_user_permissions"]["parameter_descriptions"] 