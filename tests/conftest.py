"""
Pytest configuration and fixtures.
"""
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.issues import IssuesClient
from youtrack_mcp.tools.issues import IssueTools


@pytest.fixture
def mock_youtrack_response():
    """Mock response for YouTrack API calls."""
    def _create_response(status_code=200, json_data=None):
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.raise_for_status = MagicMock()
        
        if status_code >= 400:
            mock_response.raise_for_status.side_effect = Exception(f"HTTP Error: {status_code}")
            
        if json_data:
            mock_response.json.return_value = json_data
            mock_response.content = json.dumps(json_data).encode()
        else:
            mock_response.json.return_value = {}
            mock_response.content = b"{}"
            
        return mock_response
    
    return _create_response


@pytest.fixture
def mock_issue_data():
    """Sample issue data for testing."""
    return {
        "id": "1-1",
        "summary": "Test Issue",
        "description": "This is a test issue",
        "created": 1626912000000,
        "updated": 1626912000000,
        "project": {
            "id": "0-1",
            "name": "Test Project",
            "shortName": "TEST"
        },
        "reporter": {
            "id": "1-1",
            "name": "Test User",
            "login": "test_user"
        },
        "custom_fields": []
    }


@pytest.fixture
def mock_issues_list():
    """Sample list of issues for testing."""
    return [
        {
            "id": "1-1",
            "summary": "Test Issue 1",
            "project": {
                "id": "0-1",
                "name": "Test Project",
                "shortName": "TEST"
            }
        },
        {
            "id": "1-2",
            "summary": "Test Issue 2",
            "project": {
                "id": "0-1",
                "name": "Test Project",
                "shortName": "TEST"
            }
        }
    ]


@pytest.fixture
def mock_youtrack_client(mock_youtrack_response, monkeypatch):
    """Mock YouTrack API client."""
    # Set test environment variables
    monkeypatch.setenv("YOUTRACK_URL", "https://example.myjetbrains.com/youtrack")
    monkeypatch.setenv("YOUTRACK_API_TOKEN", "test-token")
    
    with patch('httpx.Client'):
        client = YouTrackClient()
        yield client


@pytest.fixture
def mock_issues_client(mock_youtrack_client):
    """Mock Issues API client."""
    return IssuesClient(mock_youtrack_client)


@pytest.fixture
def mock_issue_tools():
    """Mock Issue tools."""
    with patch('youtrack_mcp.tools.issues.YouTrackClient'):
        with patch('youtrack_mcp.tools.issues.IssuesClient'):
            tools = IssueTools()
            yield tools 