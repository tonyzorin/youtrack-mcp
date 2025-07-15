"""
Shared test configuration and fixtures for YouTrack MCP tests.
"""
import os
import pytest
from unittest.mock import Mock, patch
from typing import Generator, Dict, Any

# Test configuration
TEST_YOUTRACK_URL = "https://test.youtrack.cloud"
TEST_API_TOKEN = "test-token"


@pytest.fixture(scope="session")
def test_config() -> Dict[str, str]:
    """Provide test configuration."""
    return {
        "YOUTRACK_URL": TEST_YOUTRACK_URL,
        "YOUTRACK_API_TOKEN": TEST_API_TOKEN,
        "YOUTRACK_CLOUD": "true"
    }


@pytest.fixture(scope="function")
def mock_youtrack_client():
    """Mock YouTrack client for testing without real API calls."""
    from youtrack_mcp.api.client import YouTrackClient
    
    with patch.object(YouTrackClient, '__init__', return_value=None):
        with patch.object(YouTrackClient, 'get') as mock_get:
            with patch.object(YouTrackClient, 'post') as mock_post:
                with patch.object(YouTrackClient, 'close') as mock_close:
                    client = YouTrackClient()
                    client.base_url = TEST_YOUTRACK_URL
                    client.token = TEST_API_TOKEN
                    client.verify_ssl = True
                    
                    # Set up default mock responses
                    mock_get.return_value = {"id": "test-123", "summary": "Test Issue"}
                    mock_post.return_value = {"id": "created-123", "summary": "Created Issue"}
                    
                    yield {
                        'client': client,
                        'mock_get': mock_get,
                        'mock_post': mock_post,
                        'mock_close': mock_close
                    }


@pytest.fixture(scope="function")
def mock_environment(test_config: Dict[str, str]) -> Generator[None, None, None]:
    """Mock environment variables for testing."""
    with patch.dict(os.environ, test_config):
        yield


@pytest.fixture(scope="function")
def sample_issue_data() -> Dict[str, Any]:
    """Provide sample issue data for testing."""
    return {
        "id": "TEST-123",
        "summary": "Test Issue Summary",
        "description": "Test issue description",
        "project": {
            "id": "0-0",
            "shortName": "TEST",
            "name": "Test Project"
        },
        "reporter": {
            "id": "user-1",
            "login": "testuser",
            "fullName": "Test User"
        },
        "created": 1640995200000,  # 2022-01-01
        "updated": 1640995200000,
        "resolved": None,
        "customFields": []
    }


@pytest.fixture(scope="function")
def sample_project_data() -> Dict[str, Any]:
    """Provide sample project data for testing."""
    return {
        "id": "0-0",
        "shortName": "TEST",
        "name": "Test Project",
        "description": "A test project for unit testing",
        "archived": False,
        "customFields": []
    }


@pytest.fixture(scope="function") 
def sample_user_data() -> Dict[str, Any]:
    """Provide sample user data for testing."""
    return {
        "id": "user-1",
        "login": "testuser",
        "fullName": "Test User",
        "email": "testuser@example.com",
        "banned": False,
        "tags": []
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "docker: mark test as a docker test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    ) 