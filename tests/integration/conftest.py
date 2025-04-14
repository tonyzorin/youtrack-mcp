"""
Pytest fixtures for integration tests.
"""
import os
import pytest
from dotenv import load_dotenv

from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.issues import IssuesClient
from youtrack_mcp.api.users import UsersClient
from youtrack_mcp.api.projects import ProjectsClient
from youtrack_mcp.tools.users import UserTools
from youtrack_mcp.tools.issues import IssueTools
from youtrack_mcp.tools.projects import ProjectTools
from youtrack_mcp.tools.search import SearchTools

# Load .env.test if it exists
load_dotenv(".env.test")


def pytest_configure(config):
    """
    Validate that we have the necessary environment variables for integration tests.
    Skip all integration tests if not configured properly.
    """
    required_vars = ["YOUTRACK_URL", "YOUTRACK_API_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        message = (
            f"Missing environment variables for integration tests: {', '.join(missing_vars)}. "
            "Please create a .env.test file with test instance credentials."
        )
        print(message)
        pytest.skip(message, allow_module_level=True)


@pytest.fixture
def youtrack_client():
    """Create a YouTrack API client for integration tests."""
    client = YouTrackClient()
    yield client
    client.close()


@pytest.fixture
def users_client(youtrack_client):
    """Create a Users API client for integration tests."""
    return UsersClient(youtrack_client)


@pytest.fixture
def issues_client(youtrack_client):
    """Create an Issues API client for integration tests."""
    return IssuesClient(youtrack_client)


@pytest.fixture
def projects_client(youtrack_client):
    """Create a Projects API client for integration tests."""
    return ProjectsClient(youtrack_client)


@pytest.fixture
def user_tools():
    """Create User tools for integration tests."""
    tools = UserTools()
    yield tools
    tools.close()


@pytest.fixture
def issue_tools():
    """Create Issue tools for integration tests."""
    tools = IssueTools()
    yield tools
    tools.close()


@pytest.fixture
def project_tools():
    """Create Project tools for integration tests."""
    tools = ProjectTools()
    yield tools
    tools.close()


@pytest.fixture
def search_tools():
    """Create Search tools for integration tests."""
    tools = SearchTools()
    yield tools
    tools.close() 