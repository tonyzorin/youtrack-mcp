"""
Integration tests for YouTrack User tools.
"""
import json
import pytest


@pytest.mark.integration
def test_get_current_user(user_tools):
    """Test that get_current_user returns valid user information."""
    # Call the tool
    result = user_tools.get_current_user()
    
    # Parse the result and check it has the expected structure
    result_data = json.loads(result)
    
    # Verify basic user data structure
    assert "id" in result_data
    assert "login" in result_data
    assert "name" in result_data
    
    # The email may be present depending on permissions
    if "email" in result_data:
        assert isinstance(result_data["email"], str) or result_data["email"] is None


@pytest.mark.integration
def test_search_users(user_tools):
    """Test that search_users returns results."""
    # Call the tool with a query that should return at least the current user
    result = user_tools.search_users("", limit=10)  # Empty query should return all users up to limit
    
    # Parse the result
    result_data = json.loads(result)
    
    # Verify we got user results
    assert isinstance(result_data, list)
    assert len(result_data) > 0
    
    # Check the structure of the first user
    first_user = result_data[0]
    assert "id" in first_user
    assert "login" in first_user
    
    # Test with a specific limit
    limited_result = user_tools.search_users("", limit=1)
    limited_data = json.loads(limited_result)
    assert isinstance(limited_data, list)
    assert len(limited_data) <= 1


@pytest.mark.integration
def test_get_user_by_login(user_tools):
    """Test that get_user_by_login can find a user."""
    # First get the current user to know a valid login
    current_user_result = user_tools.get_current_user()
    current_user = json.loads(current_user_result)
    login = current_user.get("login")
    
    # Skip if no login available
    if not login:
        pytest.skip("Current user has no login")
    
    # Call the tool with the known login
    result = user_tools.get_user_by_login(login)
    
    # Parse the result
    result_data = json.loads(result)
    
    # Verify we got the right user
    assert "id" in result_data
    assert result_data.get("login") == login


@pytest.mark.integration
def test_get_user(user_tools):
    """Test that get_user can retrieve a user by ID."""
    # First get the current user to know a valid ID
    current_user_result = user_tools.get_current_user()
    current_user = json.loads(current_user_result)
    user_id = current_user.get("id")
    
    # Call the tool with the known ID
    result = user_tools.get_user(user_id)
    
    # Parse the result
    result_data = json.loads(result)
    
    # Verify we got the right user
    assert result_data.get("id") == user_id


@pytest.mark.integration
def test_get_user_groups(user_tools):
    """Test that get_user_groups returns groups for a user."""
    # First get the current user to know a valid ID
    current_user_result = user_tools.get_current_user()
    current_user = json.loads(current_user_result)
    user_id = current_user.get("id")
    
    # Call the tool with the known ID
    result = user_tools.get_user_groups(user_id)
    
    # Parse the result
    result_data = json.loads(result)
    
    # Verify we got a list of groups
    assert isinstance(result_data, list)
    
    # If there are groups, check their structure
    if result_data:
        group = result_data[0]
        assert "id" in group
        assert "name" in group 