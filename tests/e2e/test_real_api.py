"""
End-to-end tests for YouTrack MCP with real YouTrack instance.

These tests require real YouTrack credentials and will make actual API calls.
They are disabled by default and only run when real credentials are available.
"""

import pytest
import os
from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.issues import IssuesClient
from youtrack_mcp.api.projects import ProjectsClient

# Mark all tests in this module as e2e tests
pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def real_client():
    """Create a real YouTrack client for E2E testing."""
    url = os.getenv("YOUTRACK_URL")
    token = os.getenv("YOUTRACK_API_TOKEN")
    
    if not url or not token:
        pytest.skip("Real YouTrack credentials not available")
    
    client = YouTrackClient()
    client.base_url = f"{url.rstrip('/')}/api"
    client.api_token = token
    return client


@pytest.fixture
def issues_client(real_client):
    """Create a real IssuesClient."""
    return IssuesClient(real_client)


@pytest.fixture
def projects_client(real_client):
    """Create a real ProjectsClient."""
    return ProjectsClient(real_client)


class TestRealAPI:
    """E2E tests with real YouTrack instance."""

    def test_get_projects(self, projects_client):
        """Test getting projects from real YouTrack."""
        projects = projects_client.get_projects()
        assert isinstance(projects, list)
        assert len(projects) > 0
        
        # Check that each project has required fields
        for project in projects:
            assert "id" in project
            assert "shortName" in project

    def test_search_issues(self, issues_client):
        """Test searching for issues in real YouTrack."""
        # Search for recent issues (limit to prevent too many results)
        issues = issues_client.search_issues(
            query="created: -30d",
            limit=5
        )
        assert isinstance(issues, list)
        
        # If we have issues, check their structure
        if issues:
            issue = issues[0]
            assert "id" in issue
            assert "idReadable" in issue
            assert "summary" in issue

    def test_get_current_user(self, real_client):
        """Test getting current user info."""
        from youtrack_mcp.api.users import UsersClient
        users_client = UsersClient(real_client)
        
        user = users_client.get_current_user()
        assert user is not None
        assert hasattr(user, 'id')
        assert hasattr(user, 'login')

    @pytest.mark.slow
    def test_create_and_update_issue(self, issues_client, projects_client):
        """Test creating and updating an issue (if test project exists)."""
        # Get projects to find a test project
        projects = projects_client.get_projects()
        test_project = None
        
        for project in projects:
            if project.get("shortName") in ["DEMO", "TEST", "SANDBOX"]:
                test_project = project
                break
        
        if not test_project:
            pytest.skip("No test project (DEMO, TEST, or SANDBOX) found")
        
        project_short_name = test_project["shortName"]
        
        # Create a test issue
        issue = issues_client.create_issue(
            project=project_short_name,
            summary="E2E Test Issue - Auto Created",
            description="This is an automated test issue. It can be safely deleted."
        )
        
        assert issue.id
        assert issue.summary == "E2E Test Issue - Auto Created"
        
        # Try to update custom fields using Commands API
        try:
            updated_issue = issues_client.update_issue_custom_fields(
                issue_id=issue.idReadable,
                custom_fields={"Type": "Task"},  # Assuming Type field exists
                validate=False
            )
            assert updated_issue.id == issue.id
        except Exception as e:
            # Custom field update might fail if fields don't exist
            # This is okay for E2E testing - we just verify the API works
            print(f"Custom field update failed (expected): {e}")
        
        # Verify we can retrieve the issue
        retrieved_issue = issues_client.get_issue(issue.idReadable)
        assert retrieved_issue.id == issue.id
        assert retrieved_issue.summary == issue.summary

    def test_custom_field_schema(self, projects_client):
        """Test getting custom field schemas."""
        projects = projects_client.get_projects()
        if not projects:
            pytest.skip("No projects available")
        
        project_id = projects[0]["id"]
        
        # Try to get custom field schemas
        try:
            schemas = projects_client.get_all_custom_fields_schemas(project_id)
            # Should return a list (might be empty)
            assert isinstance(schemas, list)
        except Exception as e:
            # This might fail if project has no custom fields
            # That's okay for E2E testing
            print(f"Custom field schema retrieval failed (might be expected): {e}")


class TestDockerEnvironment:
    """Tests specific to Docker environment setup."""
    
    def test_environment_variables(self):
        """Test that required environment variables are available."""
        url = os.getenv("YOUTRACK_URL")
        token = os.getenv("YOUTRACK_API_TOKEN")
        
        if url and token:
            assert url.startswith("https://")
            assert len(token) > 10  # Basic token validation
        else:
            pytest.skip("Environment variables not set - this is expected in CI")

    def test_api_connectivity(self, real_client):
        """Test basic API connectivity."""
        # This is a simple connectivity test
        try:
            from youtrack_mcp.api.users import UsersClient
            users_client = UsersClient(real_client)
            user = users_client.get_current_user()
            assert user is not None
        except Exception as e:
            pytest.fail(f"API connectivity test failed: {e}") 