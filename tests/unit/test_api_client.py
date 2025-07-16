"""
Comprehensive unit tests for YouTrack API client.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import ConnectionError, Timeout

from youtrack_mcp.api.client import (
    YouTrackClient,
    YouTrackModel,
    YouTrackAPIError,
    RateLimitError,
    ResourceNotFoundError,
    AuthenticationError,
    PermissionDeniedError,
    ValidationError,
    ServerError,
)


class TestYouTrackModel:
    """Test cases for YouTrackModel base class."""

    @pytest.mark.unit
    def test_model_creation(self):
        """Test that YouTrackModel can be created with required fields."""
        model = YouTrackModel(id="test-id")
        assert model.id == "test-id"

    @pytest.mark.unit
    def test_model_extra_fields(self):
        """Test that extra fields are allowed in YouTrackModel."""
        model = YouTrackModel(id="test-id", extra_field="extra_value")
        assert model.id == "test-id"
        assert model.extra_field == "extra_value"


class TestYouTrackClient:
    """Test cases for YouTrackClient class."""

    @pytest.fixture
    def mock_session(self):
        """Mock requests session."""
        with patch("youtrack_mcp.api.client.requests.Session") as mock_session_class:
            session = Mock()
            mock_session_class.return_value = session
            yield session

    @pytest.fixture
    def client(self, mock_session):
        """Create a test client with mocked session."""
        with patch("youtrack_mcp.api.client.config") as mock_config:
            mock_config.get_base_url.return_value = "https://test.youtrack.cloud"
            mock_config.YOUTRACK_API_TOKEN = "test-token"
            mock_config.VERIFY_SSL = True
            mock_config.is_cloud_instance.return_value = True
            return YouTrackClient()

    @pytest.mark.unit
    def test_client_initialization_default(self, mock_session):
        """Test client initialization with default configuration."""
        with patch("youtrack_mcp.api.client.config") as mock_config:
            mock_config.get_base_url.return_value = "https://test.youtrack.cloud"
            mock_config.get_api_token.return_value = "test-token"
            mock_config.VERIFY_SSL = True
            mock_config.is_cloud_instance.return_value = True

            client = YouTrackClient()

            assert client.base_url == "https://test.youtrack.cloud"
            assert client.api_token == "test-token"
            assert client.verify_ssl is True
            assert client.max_retries == 3
            assert client.retry_delay == 1.0

    @pytest.mark.unit
    def test_client_initialization_custom(self, mock_session):
        """Test client initialization with custom parameters."""
        client = YouTrackClient(
            base_url="https://custom.youtrack.cloud",
            api_token="custom-token",
            verify_ssl=False,
            max_retries=5,
            retry_delay=2.0,
        )

        assert client.base_url == "https://custom.youtrack.cloud"
        assert client.api_token == "custom-token"
        assert client.verify_ssl is False
        assert client.max_retries == 5
        assert client.retry_delay == 2.0

    @pytest.mark.unit
    def test_client_initialization_no_token(self, mock_session):
        """Test that client raises error when no API token is provided."""
        with patch("youtrack_mcp.api.client.config") as mock_config:
            mock_config.get_base_url.return_value = "https://test.youtrack.cloud"
            mock_config.get_api_token.side_effect = ValueError("API token is required")

            with pytest.raises(ValueError, match="API token is required"):
                YouTrackClient()

    @pytest.mark.unit
    def test_get_api_url_with_api_suffix(self, client):
        """Test API URL construction when base URL ends with /api."""
        client.base_url = "https://test.youtrack.cloud/api"
        url = client._get_api_url("issues")
        assert url == "https://test.youtrack.cloud/api/issues"

    @pytest.mark.unit
    def test_get_api_url_without_api_suffix(self, client):
        """Test API URL construction when base URL doesn't end with /api."""
        client.base_url = "https://test.youtrack.cloud"
        url = client._get_api_url("issues")
        assert url == "https://test.youtrack.cloud/api/issues"

    @pytest.mark.unit
    def test_handle_response_success_json(self, client):
        """Test successful JSON response handling."""
        response = Mock()
        response.status_code = 200
        response.content = b'{"test": "data"}'
        response.json.return_value = {"test": "data"}

        result = client._handle_response(response)
        assert result == {"test": "data"}

    @pytest.mark.unit
    def test_handle_response_success_empty(self, client):
        """Test successful empty response handling."""
        response = Mock()
        response.status_code = 200
        response.content = b""

        result = client._handle_response(response)
        assert result == {}

    @pytest.mark.unit
    def test_handle_response_success_non_json(self, client):
        """Test successful non-JSON response handling."""
        response = Mock()
        response.status_code = 200
        response.content = b"plain text response"
        response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        result = client._handle_response(response)
        assert result == {"raw_content": "plain text response"}

    @pytest.mark.unit
    def test_handle_response_400_validation_error(self, client):
        """Test 400 Bad Request response handling."""
        response = Mock()
        response.status_code = 400
        response.json.return_value = {"error": "Invalid request"}

        with pytest.raises(
            ValidationError, match="API request failed with status 400: Invalid request"
        ):
            client._handle_response(response)

    @pytest.mark.unit
    def test_handle_response_401_auth_error(self, client):
        """Test 401 Unauthorized response handling."""
        response = Mock()
        response.status_code = 401
        response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        response.content = b"Unauthorized"

        with pytest.raises(
            AuthenticationError,
            match="API request failed with status 401: Unauthorized",
        ):
            client._handle_response(response)

    @pytest.mark.unit
    def test_handle_response_403_permission_error(self, client):
        """Test 403 Forbidden response handling."""
        response = Mock()
        response.status_code = 403
        response.json.return_value = {"error": "Permission denied"}

        with pytest.raises(
            PermissionDeniedError,
            match="API request failed with status 403: Permission denied",
        ):
            client._handle_response(response)

    @pytest.mark.unit
    def test_handle_response_404_not_found(self, client):
        """Test 404 Not Found response handling."""
        response = Mock()
        response.status_code = 404
        response.json.return_value = {"error": "Resource not found"}

        with pytest.raises(
            ResourceNotFoundError,
            match="API request failed with status 404: Resource not found",
        ):
            client._handle_response(response)

    @pytest.mark.unit
    def test_handle_response_429_rate_limit(self, client):
        """Test 429 Rate Limit response handling."""
        response = Mock()
        response.status_code = 429
        response.json.return_value = {"error": "Rate limit exceeded"}

        with pytest.raises(
            RateLimitError,
            match="API request failed with status 429: Rate limit exceeded",
        ):
            client._handle_response(response)

    @pytest.mark.unit
    def test_handle_response_500_server_error(self, client):
        """Test 500 Server Error response handling."""
        response = Mock()
        response.status_code = 500
        response.json.return_value = {"error": "Internal server error"}

        with pytest.raises(
            ServerError,
            match="API request failed with status 500: Internal server error",
        ):
            client._handle_response(response)

    @pytest.mark.unit
    def test_handle_response_unknown_error(self, client):
        """Test unknown error code response handling."""
        response = Mock()
        response.status_code = 418  # I'm a teapot
        response.json.return_value = {"error": "Unknown error"}

        with pytest.raises(
            YouTrackAPIError, match="API request failed with status 418: Unknown error"
        ):
            client._handle_response(response)

    @pytest.mark.unit
    def test_make_request_success(self, client, mock_session):
        """Test successful request making."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"test": "data"}
        mock_session.request.return_value = response

        result = client._make_request("GET", "issues")

        mock_session.request.assert_called_once_with(
            "GET", "https://test.youtrack.cloud/api/issues"
        )
        assert result == {"test": "data"}

    @pytest.mark.unit
    def test_make_request_retry_on_server_error(self, client, mock_session):
        """Test retry logic for server errors."""
        # First call fails with 500, second succeeds
        error_response = Mock()
        error_response.status_code = 500
        error_response.json.return_value = {"error": "Server error"}

        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {"test": "data"}

        mock_session.request.side_effect = [error_response, success_response]

        with patch("time.sleep"):  # Mock sleep to speed up test
            result = client._make_request("GET", "issues")

        assert mock_session.request.call_count == 2
        assert result == {"test": "data"}

    @pytest.mark.unit
    def test_make_request_max_retries_exceeded(self, client, mock_session):
        """Test max retries exceeded."""
        client.max_retries = 1  # Only allow 1 retry

        error_response = Mock()
        error_response.status_code = 500
        error_response.json.return_value = {"error": "Server error"}
        mock_session.request.return_value = error_response

        with patch("time.sleep"):  # Mock sleep to speed up test
            with pytest.raises(ServerError):
                client._make_request("GET", "issues")

        assert mock_session.request.call_count == 2  # Original + 1 retry

    @pytest.mark.unit
    def test_make_request_non_retryable_error(self, client, mock_session):
        """Test that non-retryable errors are not retried."""
        error_response = Mock()
        error_response.status_code = 404
        error_response.json.return_value = {"error": "Not found"}
        mock_session.request.return_value = error_response

        with pytest.raises(ResourceNotFoundError):
            client._make_request("GET", "issues")

        assert mock_session.request.call_count == 1  # No retries

    @pytest.mark.unit
    def test_get_method(self, client, mock_session):
        """Test GET method."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"test": "data"}
        mock_session.request.return_value = response

        result = client.get("issues", params={"project": "TEST"})

        mock_session.request.assert_called_once_with(
            "GET", "https://test.youtrack.cloud/api/issues", params={"project": "TEST"}
        )
        assert result == {"test": "data"}

    @pytest.mark.unit
    def test_post_method_with_data(self, client, mock_session):
        """Test POST method with data."""
        response = Mock()
        response.status_code = 201
        response.json.return_value = {"id": "new-issue"}
        mock_session.request.return_value = response

        data = {"summary": "New issue"}
        result = client.post("issues", data=data)

        mock_session.request.assert_called_once_with(
            "POST", "https://test.youtrack.cloud/api/issues", json=data
        )
        assert result == {"id": "new-issue"}

    @pytest.mark.unit
    def test_post_method_with_json_data(self, client, mock_session):
        """Test POST method with explicit JSON data."""
        response = Mock()
        response.status_code = 201
        response.json.return_value = {"id": "new-issue"}
        mock_session.request.return_value = response

        json_data = {"summary": "New issue"}
        result = client.post("issues", json_data=json_data)

        mock_session.request.assert_called_once_with(
            "POST", "https://test.youtrack.cloud/api/issues", data=None, json=json_data
        )
        assert result == {"id": "new-issue"}

    @pytest.mark.unit
    def test_put_method(self, client, mock_session):
        """Test PUT method."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"updated": True}
        mock_session.request.return_value = response

        data = {"summary": "Updated issue"}
        result = client.put("issues/ISSUE-1", data=data)

        mock_session.request.assert_called_once_with(
            "PUT",
            "https://test.youtrack.cloud/api/issues/ISSUE-1",
            data=data,
            json=None,
        )
        assert result == {"updated": True}

    @pytest.mark.unit
    def test_delete_method(self, client, mock_session):
        """Test DELETE method."""
        response = Mock()
        response.status_code = 204
        response.content = b""
        mock_session.request.return_value = response

        result = client.delete("issues/ISSUE-1")

        mock_session.request.assert_called_once_with(
            "DELETE", "https://test.youtrack.cloud/api/issues/ISSUE-1"
        )
        assert result == {}

    @pytest.mark.unit
    def test_context_manager(self, client, mock_session):
        """Test client as context manager."""
        with client as c:
            assert c is client

        mock_session.close.assert_called_once()

    @pytest.mark.unit
    def test_close_method(self, client, mock_session):
        """Test explicit close method."""
        client.close()
        mock_session.close.assert_called_once()

    @pytest.mark.unit
    def test_ssl_verification_disabled(self, mock_session):
        """Test SSL verification disabled."""
        with patch("youtrack_mcp.api.client.config") as mock_config:
            mock_config.get_base_url.return_value = "https://test.youtrack.cloud"
            mock_config.YOUTRACK_API_TOKEN = "test-token"
            mock_config.VERIFY_SSL = False

            with patch(
                "youtrack_mcp.api.client.requests.packages.urllib3.disable_warnings"
            ) as mock_disable:
                client = YouTrackClient()

                assert client.verify_ssl is False
                assert mock_session.verify is False
                mock_disable.assert_called_once()


class TestExceptionClasses:
    """Test cases for custom exception classes."""

    @pytest.mark.unit
    def test_youtrack_api_error_basic(self):
        """Test basic YouTrackAPIError creation."""
        error = YouTrackAPIError("Test error")
        assert str(error) == "Test error"
        assert error.status_code is None
        assert error.response is None

    @pytest.mark.unit
    def test_youtrack_api_error_with_details(self):
        """Test YouTrackAPIError with status code and response."""
        response = Mock()
        error = YouTrackAPIError("Test error", status_code=500, response=response)
        assert str(error) == "Test error"
        assert error.status_code == 500
        assert error.response is response

    @pytest.mark.unit
    def test_rate_limit_error(self):
        """Test RateLimitError inherits from YouTrackAPIError."""
        error = RateLimitError("Rate limited", status_code=429)
        assert isinstance(error, YouTrackAPIError)
        assert str(error) == "Rate limited"
        assert error.status_code == 429

    @pytest.mark.unit
    def test_resource_not_found_error(self):
        """Test ResourceNotFoundError inherits from YouTrackAPIError."""
        error = ResourceNotFoundError("Not found", status_code=404)
        assert isinstance(error, YouTrackAPIError)
        assert str(error) == "Not found"
        assert error.status_code == 404

    @pytest.mark.unit
    def test_authentication_error(self):
        """Test AuthenticationError inherits from YouTrackAPIError."""
        error = AuthenticationError("Unauthorized", status_code=401)
        assert isinstance(error, YouTrackAPIError)
        assert str(error) == "Unauthorized"
        assert error.status_code == 401

    @pytest.mark.unit
    def test_permission_denied_error(self):
        """Test PermissionDeniedError inherits from YouTrackAPIError."""
        error = PermissionDeniedError("Forbidden", status_code=403)
        assert isinstance(error, YouTrackAPIError)
        assert str(error) == "Forbidden"
        assert error.status_code == 403

    @pytest.mark.unit
    def test_validation_error(self):
        """Test ValidationError inherits from YouTrackAPIError."""
        error = ValidationError("Bad request", status_code=400)
        assert isinstance(error, YouTrackAPIError)
        assert str(error) == "Bad request"
        assert error.status_code == 400

    @pytest.mark.unit
    def test_server_error(self):
        """Test ServerError inherits from YouTrackAPIError."""
        error = ServerError("Internal server error", status_code=500)
        assert isinstance(error, YouTrackAPIError)
        assert str(error) == "Internal server error"
        assert error.status_code == 500
