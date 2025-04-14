"""
Tests for user-related MCP tools.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from youtrack_mcp.api.users import User
from youtrack_mcp.tools.users import UserTools


@pytest.fixture
def mock_user_data():
    """Sample user data for testing."""
    return {
        "id": "1-1",
        "login": "test_user",
        "name": "Test User",
        "email": "test@example.com",
        "jabber": None,
        "ring_id": None,
        "guest": False,
        "online": True,
        "banned": False
    }


@pytest.fixture
def mock_users_list():
    """Sample list of users for testing."""
    return [
        {
            "id": "1-1",
            "login": "test_user1",
            "name": "Test User 1",
            "email": "test1@example.com"
        },
        {
            "id": "1-2",
            "login": "test_user2",
            "name": "Test User 2",
            "email": "test2@example.com"
        }
    ]


@pytest.fixture
def mock_user_groups():
    """Sample user groups data for testing."""
    return [
        {
            "id": "1-1",
            "name": "Developers"
        },
        {
            "id": "1-2",
            "name": "Administrators"
        }
    ]


@pytest.fixture
def mock_user_tools():
    """Mock User tools."""
    with patch('youtrack_mcp.tools.users.YouTrackClient'):
        with patch('youtrack_mcp.tools.users.UsersClient'):
            tools = UserTools()
            yield tools


def test_get_current_user_tool_success(mock_user_tools, mock_user_data):
    """Test get_current_user tool returns proper JSON when successful."""
    # Mock client to return mock data directly
    mock_user_tools.client.get.return_value = mock_user_data
    
    # Call the tool
    result = mock_user_tools.get_current_user()
    
    # Verify the result
    assert mock_user_tools.client.get.called
    assert "users/me" in mock_user_tools.client.get.call_args[0][0]
    
    # Parse the JSON result and check it matches expected data
    result_data = json.loads(result)
    assert result_data["id"] == mock_user_data["id"]
    assert result_data["login"] == mock_user_data["login"]
    assert result_data["name"] == mock_user_data["name"]


def test_get_current_user_tool_error(mock_user_tools):
    """Test get_current_user tool returns error JSON when exception occurs."""
    # Mock client to raise an exception
    mock_user_tools.client.get.side_effect = Exception("Test error")
    
    # Call the tool
    result = mock_user_tools.get_current_user()
    
    # Parse the JSON result and check it contains error message
    result_data = json.loads(result)
    assert "error" in result_data
    assert "Test error" in result_data["error"]


def test_get_user_tool_success(mock_user_tools, mock_user_data):
    """Test get_user tool returns proper JSON when successful."""
    # Mock client to return mock data directly
    mock_user_tools.client.get.return_value = mock_user_data
    
    # Call the tool
    result = mock_user_tools.get_user("1-1")
    
    # Verify the result
    assert mock_user_tools.client.get.called
    assert "users/1-1" in mock_user_tools.client.get.call_args[0][0]
    
    # Parse the JSON result and check it matches expected data
    result_data = json.loads(result)
    assert result_data["id"] == mock_user_data["id"]
    assert result_data["login"] == mock_user_data["login"]
    assert result_data["name"] == mock_user_data["name"]


def test_get_user_tool_error(mock_user_tools):
    """Test get_user tool returns error JSON when exception occurs."""
    # Mock client to raise an exception
    mock_user_tools.client.get.side_effect = Exception("Test error")
    
    # Call the tool
    result = mock_user_tools.get_user("1-1")
    
    # Parse the JSON result and check it contains error message
    result_data = json.loads(result)
    assert "error" in result_data
    assert "Test error" in result_data["error"]


def test_search_users_tool_success(mock_user_tools, mock_users_list):
    """Test search_users tool returns proper JSON when successful."""
    # Mock client to return mock data directly
    mock_user_tools.client.get.return_value = mock_users_list
    
    # Call the tool
    result = mock_user_tools.search_users("test")
    
    # Verify the result
    assert mock_user_tools.client.get.called
    assert mock_user_tools.client.get.call_args[0][0] == "users"
    assert mock_user_tools.client.get.call_args[1]["params"]["query"] == "test"
    
    # Parse the JSON result and check it matches expected data
    result_data = json.loads(result)
    assert isinstance(result_data, list)
    assert len(result_data) == len(mock_users_list)
    assert result_data[0]["id"] == mock_users_list[0]["id"]
    assert result_data[1]["id"] == mock_users_list[1]["id"]


def test_search_users_tool_error(mock_user_tools):
    """Test search_users tool returns error JSON when exception occurs."""
    # Mock client to raise an exception
    mock_user_tools.client.get.side_effect = Exception("Test error")
    
    # Call the tool
    result = mock_user_tools.search_users("test")
    
    # Parse the JSON result and check it contains error message
    result_data = json.loads(result)
    assert "error" in result_data
    assert "Test error" in result_data["error"]


def test_get_user_by_login_tool_success(mock_user_tools, mock_user_data):
    """Test get_user_by_login tool returns proper JSON when successful."""
    # Mock user API to return a mock user
    mock_user = User.model_validate(mock_user_data)
    mock_user_tools.users_api.get_user_by_login.return_value = mock_user
    
    # Call the tool
    result = mock_user_tools.get_user_by_login("test_user")
    
    # Verify the result
    assert mock_user_tools.users_api.get_user_by_login.called
    assert mock_user_tools.users_api.get_user_by_login.call_args[0][0] == "test_user"
    
    # Parse the JSON result and check it matches expected data
    result_data = json.loads(result)
    assert result_data["id"] == mock_user_data["id"]
    assert result_data["login"] == mock_user_data["login"]


def test_get_user_by_login_tool_not_found(mock_user_tools):
    """Test get_user_by_login tool returns error JSON when user not found."""
    # Mock user API to return None (user not found)
    mock_user_tools.users_api.get_user_by_login.return_value = None
    
    # Call the tool
    result = mock_user_tools.get_user_by_login("nonexistent_user")
    
    # Parse the JSON result and check it contains error message
    result_data = json.loads(result)
    assert "error" in result_data
    assert "not found" in result_data["error"]


def test_get_user_by_login_tool_error(mock_user_tools):
    """Test get_user_by_login tool returns error JSON when exception occurs."""
    # Mock user API to raise an exception
    mock_user_tools.users_api.get_user_by_login.side_effect = Exception("Test error")
    
    # Call the tool
    result = mock_user_tools.get_user_by_login("test_user")
    
    # Parse the JSON result and check it contains error message
    result_data = json.loads(result)
    assert "error" in result_data
    assert "Test error" in result_data["error"]


def test_get_user_groups_tool_success(mock_user_tools, mock_user_groups):
    """Test get_user_groups tool returns proper JSON when successful."""
    # Mock user API to return mock groups
    mock_user_tools.users_api.get_user_groups.return_value = mock_user_groups
    
    # Call the tool
    result = mock_user_tools.get_user_groups("1-1")
    
    # Verify the result
    assert mock_user_tools.users_api.get_user_groups.called
    assert mock_user_tools.users_api.get_user_groups.call_args[0][0] == "1-1"
    
    # Parse the JSON result and check it matches expected data
    result_data = json.loads(result)
    assert isinstance(result_data, list)
    assert len(result_data) == len(mock_user_groups)
    assert result_data[0]["id"] == mock_user_groups[0]["id"]
    assert result_data[1]["name"] == mock_user_groups[1]["name"]


def test_get_user_groups_tool_error(mock_user_tools):
    """Test get_user_groups tool returns error JSON when exception occurs."""
    # Mock user API to raise an exception
    mock_user_tools.users_api.get_user_groups.side_effect = Exception("Test error")
    
    # Call the tool
    result = mock_user_tools.get_user_groups("1-1")
    
    # Parse the JSON result and check it contains error message
    result_data = json.loads(result)
    assert "error" in result_data
    assert "Test error" in result_data["error"]


def test_get_tool_definitions(mock_user_tools):
    """Test that get_tool_definitions returns the expected tools."""
    tool_defs = mock_user_tools.get_tool_definitions()
    
    # Check that all expected tools are defined
    assert "get_current_user" in tool_defs
    assert "get_user" in tool_defs
    assert "search_users" in tool_defs
    assert "get_user_by_login" in tool_defs
    assert "get_user_groups" in tool_defs
    
    # Check that each tool has required attributes
    for tool_name, tool_def in tool_defs.items():
        assert "function" in tool_def
        assert "description" in tool_def
        assert "parameter_descriptions" in tool_def 