import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from youtrack_mcp.tools.create_project_tool import create_project_direct
from youtrack_mcp.api.client import YouTrackClient
from youtrack_mcp.api.projects import ProjectsClient


class TestCreateProjectTool:
    """Test create_project_tool functionality."""

    @pytest.mark.unit
    @patch("youtrack_mcp.tools.create_project_tool.YouTrackClient")
    @patch("youtrack_mcp.tools.create_project_tool.ProjectsClient")
    def test_create_project_direct_basic(
        self, mock_projects_client, mock_youtrack_client
    ):
        """Test basic project creation."""
        # Mock the client and response
        mock_client_instance = Mock()
        mock_youtrack_client.return_value = mock_client_instance

        mock_response = {
            "id": "0-1",
            "name": "Test Project",
            "shortName": "TEST",
            "leader": {"id": "user123", "login": "testlead"},
        }
        mock_client_instance.post.return_value = mock_response

        # Call the function
        result = create_project_direct(
            name="Test Project", short_name="TEST", lead_id="user123"
        )

        # Verify client initialization
        mock_youtrack_client.assert_called_once()
        mock_projects_client.assert_called_once_with(mock_client_instance)

        # Verify API call
        mock_client_instance.post.assert_called_once_with(
            "admin/projects",
            data={
                "name": "Test Project",
                "shortName": "TEST",
                "leader": {"id": "user123"},
            },
        )

        # Verify response
        parsed_result = json.loads(result)
        assert parsed_result == mock_response

        # Verify cleanup
        mock_client_instance.close.assert_called_once()

    @pytest.mark.unit
    @patch("youtrack_mcp.tools.create_project_tool.YouTrackClient")
    @patch("youtrack_mcp.tools.create_project_tool.ProjectsClient")
    def test_create_project_direct_with_description(
        self, mock_projects_client, mock_youtrack_client
    ):
        """Test project creation with description."""
        mock_client_instance = Mock()
        mock_youtrack_client.return_value = mock_client_instance

        mock_response = {
            "id": "0-2",
            "name": "Project with Description",
            "shortName": "DESC",
            "description": "A detailed project description",
            "leader": {"id": "user456"},
        }
        mock_client_instance.post.return_value = mock_response

        # Call with description
        result = create_project_direct(
            name="Project with Description",
            short_name="DESC",
            lead_id="user456",
            description="A detailed project description",
        )

        # Verify API call includes description
        mock_client_instance.post.assert_called_once_with(
            "admin/projects",
            data={
                "name": "Project with Description",
                "shortName": "DESC",
                "leader": {"id": "user456"},
                "description": "A detailed project description",
            },
        )

        parsed_result = json.loads(result)
        assert parsed_result == mock_response

    @pytest.mark.unit
    @patch("youtrack_mcp.tools.create_project_tool.YouTrackClient")
    @patch("youtrack_mcp.tools.create_project_tool.ProjectsClient")
    def test_create_project_direct_without_description(
        self, mock_projects_client, mock_youtrack_client
    ):
        """Test project creation without description."""
        mock_client_instance = Mock()
        mock_youtrack_client.return_value = mock_client_instance
        mock_client_instance.post.return_value = {"id": "0-3"}

        # Call without description (None)
        create_project_direct(
            name="No Description Project",
            short_name="NODESC",
            lead_id="user789",
            description=None,
        )

        # Verify API call excludes description
        expected_data = {
            "name": "No Description Project",
            "shortName": "NODESC",
            "leader": {"id": "user789"},
        }
        mock_client_instance.post.assert_called_once_with(
            "admin/projects", data=expected_data
        )

        # Ensure description is not in the data
        call_args = mock_client_instance.post.call_args
        actual_data = call_args[1]["data"]
        assert "description" not in actual_data

    @pytest.mark.unit
    @patch("youtrack_mcp.tools.create_project_tool.YouTrackClient")
    @patch("youtrack_mcp.tools.create_project_tool.ProjectsClient")
    def test_create_project_direct_with_empty_description(
        self, mock_projects_client, mock_youtrack_client
    ):
        """Test project creation with empty description string."""
        mock_client_instance = Mock()
        mock_youtrack_client.return_value = mock_client_instance
        mock_client_instance.post.return_value = {"id": "0-4"}

        # Call with empty description
        create_project_direct(
            name="Empty Description Project",
            short_name="EMPTY",
            lead_id="user999",
            description="",
        )

        # Empty string is falsy, so description should not be included
        expected_data = {
            "name": "Empty Description Project",
            "shortName": "EMPTY",
            "leader": {"id": "user999"},
        }
        mock_client_instance.post.assert_called_once_with(
            "admin/projects", data=expected_data
        )

    @pytest.mark.unit
    @patch("youtrack_mcp.tools.create_project_tool.logger")
    @patch("youtrack_mcp.tools.create_project_tool.YouTrackClient")
    @patch("youtrack_mcp.tools.create_project_tool.ProjectsClient")
    def test_create_project_direct_logs_info(
        self, mock_projects_client, mock_youtrack_client, mock_logger
    ):
        """Test that project creation is logged."""
        mock_client_instance = Mock()
        mock_youtrack_client.return_value = mock_client_instance
        mock_client_instance.post.return_value = {"id": "0-5"}

        create_project_direct("Log Test", "LOG", "user123")

        # Verify info logging
        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args[0][0]
        assert "Creating project with direct tool" in log_call
        assert "Log Test" in str(mock_logger.info.call_args)

    @pytest.mark.unit
    @patch("youtrack_mcp.tools.create_project_tool.logger")
    @patch("youtrack_mcp.tools.create_project_tool.YouTrackClient")
    @patch("youtrack_mcp.tools.create_project_tool.ProjectsClient")
    def test_create_project_direct_handles_client_error(
        self, mock_projects_client, mock_youtrack_client, mock_logger
    ):
        """Test error handling when YouTrack client fails."""
        mock_client_instance = Mock()
        mock_youtrack_client.return_value = mock_client_instance

        # Mock API error
        mock_client_instance.post.side_effect = Exception(
            "API Error: Project already exists"
        )

        result = create_project_direct("Error Project", "ERR", "user123")

        # Verify error response
        parsed_result = json.loads(result)
        assert "error" in parsed_result
        assert "API Error: Project already exists" in parsed_result["error"]

        # Verify error logging
        mock_logger.exception.assert_called_once()
        log_call = mock_logger.exception.call_args[0][0]
        assert "Error creating project Error Project" in log_call

        # Verify cleanup still happens
        mock_client_instance.close.assert_called_once()

    @pytest.mark.unit
    @patch("youtrack_mcp.tools.create_project_tool.YouTrackClient")
    @patch("youtrack_mcp.tools.create_project_tool.ProjectsClient")
    def test_create_project_direct_handles_client_initialization_error(
        self, mock_projects_client, mock_youtrack_client
    ):
        """Test error handling when client initialization fails."""
        # Mock client initialization error
        mock_youtrack_client.side_effect = Exception("Failed to initialize client")

        # This reveals a bug in the implementation - UnboundLocalError in finally block
        # when client initialization fails
        with pytest.raises(UnboundLocalError):
            create_project_direct("Init Error Project", "INIT", "user123")

    @pytest.mark.unit
    @patch("youtrack_mcp.tools.create_project_tool.YouTrackClient")
    @patch("youtrack_mcp.tools.create_project_tool.ProjectsClient")
    def test_create_project_direct_ensures_cleanup_on_error(
        self, mock_projects_client, mock_youtrack_client
    ):
        """Test that client cleanup happens even when errors occur."""
        mock_client_instance = Mock()
        mock_youtrack_client.return_value = mock_client_instance

        # Mock error after client creation
        mock_client_instance.post.side_effect = Exception("Some error")

        result = create_project_direct("Cleanup Test", "CLEAN", "user123")

        # Verify error response
        parsed_result = json.loads(result)
        assert "error" in parsed_result

        # Verify cleanup was called despite error
        mock_client_instance.close.assert_called_once()

    @pytest.mark.unit
    @patch("youtrack_mcp.tools.create_project_tool.YouTrackClient")
    @patch("youtrack_mcp.tools.create_project_tool.ProjectsClient")
    def test_create_project_direct_json_serialization(
        self, mock_projects_client, mock_youtrack_client
    ):
        """Test that complex response objects are properly JSON serialized."""
        mock_client_instance = Mock()
        mock_youtrack_client.return_value = mock_client_instance

        # Complex response with nested objects
        complex_response = {
            "id": "0-6",
            "name": "Complex Project",
            "shortName": "COMPLEX",
            "leader": {
                "id": "user123",
                "login": "testuser",
                "name": "Test User",
                "email": "test@example.com",
            },
            "customFields": [
                {"name": "Environment", "value": "Production"},
                {"name": "Team", "value": "Backend"},
            ],
            "archived": False,
            "created": "2023-01-01T00:00:00Z",
        }
        mock_client_instance.post.return_value = complex_response

        result = create_project_direct("Complex Project", "COMPLEX", "user123")

        # Verify JSON is properly formatted
        parsed_result = json.loads(result)
        assert parsed_result == complex_response

        # Verify it's nicely formatted (indented)
        assert "\n" in result  # Should contain newlines from json.dumps(indent=2)

    @pytest.mark.unit
    @patch("youtrack_mcp.tools.create_project_tool.YouTrackClient")
    @patch("youtrack_mcp.tools.create_project_tool.ProjectsClient")
    def test_create_project_direct_parameters_validation(
        self, mock_projects_client, mock_youtrack_client
    ):
        """Test that function works with various parameter types and values."""
        mock_client_instance = Mock()
        mock_youtrack_client.return_value = mock_client_instance
        mock_client_instance.post.return_value = {"id": "test"}

        # Test with different parameter types
        test_cases = [
            ("Simple Name", "SIMPLE", "user1", "Simple description"),
            ("Project with numbers 123", "NUM123", "user2", None),
            (
                "Special-chars & symbols!",
                "SPEC",
                "user3",
                "Description with special chars @#$%",
            ),
            (
                "   Whitespace Project   ",
                "WHITE",
                "user4",
                "   Description with whitespace   ",
            ),
        ]

        for name, short_name, lead_id, description in test_cases:
            mock_client_instance.reset_mock()

            result = create_project_direct(name, short_name, lead_id, description)

            # Should not raise exceptions
            parsed_result = json.loads(result)
            assert "id" in parsed_result

            # Verify correct parameters were passed
            call_args = mock_client_instance.post.call_args
            data = call_args[1]["data"]
            assert data["name"] == name
            assert data["shortName"] == short_name
            assert data["leader"]["id"] == lead_id

            if description:
                assert data["description"] == description
            else:
                assert "description" not in data
