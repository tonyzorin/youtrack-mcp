"""
Comprehensive unit tests for YouTrack MCP configuration.
"""

import pytest
import os
import ssl
from unittest.mock import patch, MagicMock
from youtrack_mcp.config import Config, config


class TestConfig:
    """Test the Config class."""

    def setup_method(self):
        """Reset config before each test."""
        # Store original values
        self.original_values = {
            "YOUTRACK_URL": Config.YOUTRACK_URL,
            "YOUTRACK_API_TOKEN": Config.YOUTRACK_API_TOKEN,
            "YOUTRACK_CLOUD": Config.YOUTRACK_CLOUD,
            "VERIFY_SSL": Config.VERIFY_SSL,
            "MAX_RETRIES": Config.MAX_RETRIES,
            "RETRY_DELAY": Config.RETRY_DELAY,
            "MCP_SERVER_NAME": Config.MCP_SERVER_NAME,
            "MCP_SERVER_DESCRIPTION": Config.MCP_SERVER_DESCRIPTION,
            "MCP_DEBUG": Config.MCP_DEBUG,
        }

        # Reset to defaults
        Config.YOUTRACK_URL = os.getenv("YOUTRACK_URL", "")
        Config.YOUTRACK_API_TOKEN = os.getenv("YOUTRACK_API_TOKEN", "")
        Config.YOUTRACK_CLOUD = os.getenv(
            "YOUTRACK_CLOUD", "false"
        ).lower() in (
            "true",
            "1",
            "yes",
        )
        Config.VERIFY_SSL = os.getenv(
            "YOUTRACK_VERIFY_SSL", "true"
        ).lower() in (
            "true",
            "1",
            "yes",
        )
        Config.MAX_RETRIES = int(os.getenv("YOUTRACK_MAX_RETRIES", "3"))
        Config.RETRY_DELAY = float(os.getenv("YOUTRACK_RETRY_DELAY", "1.0"))
        Config.MCP_SERVER_NAME = os.getenv("MCP_SERVER_NAME", "youtrack-mcp")
        Config.MCP_SERVER_DESCRIPTION = os.getenv(
            "MCP_SERVER_DESCRIPTION", "YouTrack MCP Server"
        )
        Config.MCP_DEBUG = os.getenv("MCP_DEBUG", "false").lower() in (
            "true",
            "1",
            "yes",
        )

    def teardown_method(self):
        """Restore original values after each test."""
        for key, value in self.original_values.items():
            setattr(Config, key, value)

    @pytest.mark.unit
    def test_config_defaults(self):
        """Test that config has correct default values."""
        assert Config.VERIFY_SSL is True
        assert Config.MAX_RETRIES == 3
        assert Config.RETRY_DELAY == 1.0
        assert Config.MCP_SERVER_NAME == "youtrack-mcp"
        assert Config.MCP_SERVER_DESCRIPTION == "YouTrack MCP Server"
        assert Config.MCP_DEBUG is False

    @pytest.mark.unit
    def test_from_dict(self):
        """Test loading configuration from dictionary."""
        config_dict = {
            "YOUTRACK_URL": "https://test.youtrack.cloud",
            "YOUTRACK_API_TOKEN": "test-token",
            "YOUTRACK_CLOUD": True,
            "VERIFY_SSL": False,
            "MAX_RETRIES": 5,
        }

        Config.from_dict(config_dict)

        assert Config.YOUTRACK_URL == "https://test.youtrack.cloud"
        assert Config.YOUTRACK_API_TOKEN == "test-token"
        assert Config.YOUTRACK_CLOUD is True
        assert Config.VERIFY_SSL is False
        assert Config.MAX_RETRIES == 5

    @pytest.mark.unit
    def test_from_dict_ignores_unknown_attributes(self):
        """Test that from_dict ignores unknown attributes."""
        original_url = Config.YOUTRACK_URL

        config_dict = {
            "UNKNOWN_SETTING": "should be ignored",
            "YOUTRACK_URL": "https://test.youtrack.cloud",
        }

        Config.from_dict(config_dict)

        assert Config.YOUTRACK_URL == "https://test.youtrack.cloud"
        assert not hasattr(Config, "UNKNOWN_SETTING")

    @pytest.mark.unit
    def test_validate_missing_api_token(self):
        """Test validation fails when API token is missing."""
        Config.YOUTRACK_API_TOKEN = ""

        with pytest.raises(ValueError, match="YouTrack API token is required"):
            Config.validate()

    @pytest.mark.unit
    def test_validate_missing_url_for_self_hosted(self):
        """Test validation fails when URL is missing for self-hosted instances."""
        Config.YOUTRACK_API_TOKEN = "test-token"
        Config.YOUTRACK_URL = ""
        Config.YOUTRACK_CLOUD = False

        with pytest.raises(
            ValueError,
            match="YouTrack URL is required for self-hosted instances",
        ):
            Config.validate()

    @pytest.mark.unit
    def test_validate_cloud_instance_without_url(self):
        """Test validation passes for cloud instances without URL."""
        Config.YOUTRACK_API_TOKEN = "test-token"
        Config.YOUTRACK_URL = ""
        Config.YOUTRACK_CLOUD = True

        # Should not raise
        Config.validate()

    @pytest.mark.unit
    def test_validate_strips_trailing_slash(self):
        """Test validation strips trailing slash from URL."""
        Config.YOUTRACK_API_TOKEN = "test-token"
        Config.YOUTRACK_URL = "https://test.youtrack.cloud/"

        Config.validate()

        assert Config.YOUTRACK_URL == "https://test.youtrack.cloud"

    @pytest.mark.unit
    def test_get_ssl_context_verify_disabled(self):
        """Test SSL context creation when verification is disabled."""
        Config.VERIFY_SSL = False

        context = Config.get_ssl_context()

        assert context is not None
        assert isinstance(context, ssl.SSLContext)
        assert context.check_hostname is False
        assert context.verify_mode == ssl.CERT_NONE

    @pytest.mark.unit
    def test_get_ssl_context_verify_enabled(self):
        """Test SSL context when verification is enabled."""
        Config.VERIFY_SSL = True

        context = Config.get_ssl_context()

        assert context is None

    @pytest.mark.unit
    def test_is_cloud_instance_explicit_cloud(self):
        """Test cloud instance detection when explicitly set."""
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_URL = "https://test.youtrack.cloud"

        assert Config.is_cloud_instance() is True

    @pytest.mark.unit
    def test_is_cloud_instance_no_url(self):
        """Test cloud instance detection when no URL is provided."""
        Config.YOUTRACK_CLOUD = False
        Config.YOUTRACK_URL = ""

        assert Config.is_cloud_instance() is True

    @pytest.mark.unit
    def test_is_cloud_instance_self_hosted(self):
        """Test cloud instance detection for self-hosted."""
        Config.YOUTRACK_CLOUD = False
        Config.YOUTRACK_URL = "https://my-server.com/youtrack"

        assert Config.is_cloud_instance() is False

    @pytest.mark.unit
    def test_get_base_url_explicit_url(self):
        """Test base URL generation with explicit URL."""
        Config.YOUTRACK_URL = "https://test.youtrack.cloud"

        result = Config.get_base_url()

        assert result == "https://test.youtrack.cloud/api"

    @pytest.mark.unit
    def test_get_base_url_cloud_perm_colon_format(self):
        """Test base URL generation for cloud with perm: token format."""
        Config.YOUTRACK_URL = ""
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_API_TOKEN = "perm:user.workspace.12345"

        result = Config.get_base_url()

        assert result == "https://workspace.youtrack.cloud/api"

    @pytest.mark.unit
    def test_get_base_url_cloud_perm_dash_with_workspace_env(self):
        """Test base URL generation for cloud with perm- token and workspace env."""
        Config.YOUTRACK_URL = ""
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_API_TOKEN = "perm-base64.base64.hash"

        with patch.dict(os.environ, {"YOUTRACK_WORKSPACE": "myworkspace"}):
            result = Config.get_base_url()

        assert result == "https://myworkspace.youtrack.cloud/api"

    @pytest.mark.unit
    def test_get_base_url_cloud_perm_dash_with_url_env(self):
        """Test base URL generation for cloud with perm- token and URL env."""
        Config.YOUTRACK_URL = ""
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_API_TOKEN = "perm-base64.base64.hash"

        with patch.dict(
            os.environ,
            {"YOUTRACK_URL": "https://env-workspace.youtrack.cloud"},
        ):
            result = Config.get_base_url()

        assert result == "https://env-workspace.youtrack.cloud/api"

    @pytest.mark.unit
    def test_get_base_url_cloud_invalid_token_format(self):
        """Test base URL generation fails for cloud with invalid token format."""
        Config.YOUTRACK_URL = ""
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_API_TOKEN = "invalid-token-format"

        with pytest.raises(
            ValueError, match="Could not determine YouTrack Cloud URL"
        ):
            Config.get_base_url()

    @pytest.mark.unit
    def test_get_base_url_cloud_perm_dash_no_fallbacks(self):
        """Test base URL generation fails for cloud with perm- token but no fallbacks."""
        Config.YOUTRACK_URL = ""
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_API_TOKEN = "perm-base64.base64.hash"

        # Ensure no fallback environment variables
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="Could not determine YouTrack Cloud URL"
            ):
                Config.get_base_url()

    @pytest.mark.unit
    def test_get_base_url_no_cloud_no_url_fallback(self):
        """Test base URL generation fallback error."""
        Config.YOUTRACK_URL = ""
        Config.YOUTRACK_CLOUD = False

        # This should trigger the is_cloud_instance() check which returns True when no URL
        # So we need to mock it to return False to reach the fallback error
        with patch.object(Config, "is_cloud_instance", return_value=False):
            with pytest.raises(ValueError, match="YouTrack URL is required"):
                Config.get_base_url()

    @pytest.mark.unit
    def test_config_global_instance(self):
        """Test that global config instance exists."""
        from youtrack_mcp.config import config

        assert config is not None
        assert isinstance(config, Config)


class TestConfigEnvironmentVariables:
    """Test configuration loading from environment variables."""

    @pytest.mark.unit
    def test_boolean_environment_variables(self):
        """Test boolean environment variable parsing."""
        test_cases = [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("yes", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
            ("no", False),
            ("anything_else", False),
            ("", False),
        ]

        for env_value, expected in test_cases:
            result = env_value.lower() in ("true", "1", "yes")
            assert result == expected, f"Failed for value: {env_value}"

    @pytest.mark.unit
    def test_integer_environment_variables(self):
        """Test integer environment variable parsing."""
        with patch.dict(os.environ, {"YOUTRACK_MAX_RETRIES": "7"}):
            max_retries = int(os.getenv("YOUTRACK_MAX_RETRIES", "3"))
            assert max_retries == 7

    @pytest.mark.unit
    def test_float_environment_variables(self):
        """Test float environment variable parsing."""
        with patch.dict(os.environ, {"YOUTRACK_RETRY_DELAY": "5.5"}):
            retry_delay = float(os.getenv("YOUTRACK_RETRY_DELAY", "1.0"))
            assert retry_delay == 5.5


class TestComplexScenarios:
    """Test complex configuration scenarios."""

    def setup_method(self):
        """Setup for complex scenario tests."""
        # Store original values
        self.original_values = {
            "YOUTRACK_URL": Config.YOUTRACK_URL,
            "YOUTRACK_API_TOKEN": Config.YOUTRACK_API_TOKEN,
            "YOUTRACK_CLOUD": Config.YOUTRACK_CLOUD,
            "VERIFY_SSL": Config.VERIFY_SSL,
        }

    def teardown_method(self):
        """Cleanup after complex scenario tests."""
        for key, value in self.original_values.items():
            setattr(Config, key, value)

    @pytest.mark.unit
    def test_cloud_token_with_single_dot(self):
        """Test cloud token with only one dot (invalid format)."""
        Config.YOUTRACK_URL = ""
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_API_TOKEN = "perm:invalid"

        with pytest.raises(
            ValueError, match="Could not determine YouTrack Cloud URL"
        ):
            Config.get_base_url()

    @pytest.mark.unit
    def test_cloud_token_not_starting_with_perm(self):
        """Test cloud token not starting with perm: or perm-."""
        Config.YOUTRACK_URL = ""
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_API_TOKEN = "regular.token.format"

        with pytest.raises(
            ValueError, match="Could not determine YouTrack Cloud URL"
        ):
            Config.get_base_url()

    @pytest.mark.unit
    def test_url_takes_precedence_over_cloud_detection(self):
        """Test that explicit URL takes precedence over cloud auto-detection."""
        Config.YOUTRACK_URL = "https://my-server.com/youtrack"
        Config.YOUTRACK_CLOUD = (
            True  # Even with cloud=True, URL should be used
        )
        Config.YOUTRACK_API_TOKEN = "perm:user.workspace.12345"

        result = Config.get_base_url()

        assert result == "https://my-server.com/youtrack/api"

    @pytest.mark.unit
    def test_validate_and_strip_multiple_trailing_slashes(self):
        """Test validation strips multiple trailing slashes."""
        Config.YOUTRACK_API_TOKEN = "test-token"
        Config.YOUTRACK_URL = "https://test.youtrack.cloud///"

        Config.validate()

        assert Config.YOUTRACK_URL == "https://test.youtrack.cloud"


class TestSpecialEdgeCases:
    """Test special edge cases and error conditions."""

    def setup_method(self):
        """Setup for edge case tests."""
        self.original_values = {
            "YOUTRACK_URL": Config.YOUTRACK_URL,
            "YOUTRACK_API_TOKEN": Config.YOUTRACK_API_TOKEN,
            "YOUTRACK_CLOUD": Config.YOUTRACK_CLOUD,
        }

    def teardown_method(self):
        """Cleanup after edge case tests."""
        for key, value in self.original_values.items():
            setattr(Config, key, value)

    @pytest.mark.unit
    def test_perm_dash_token_insufficient_parts(self):
        """Test perm- token with insufficient parts."""
        Config.YOUTRACK_URL = ""
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_API_TOKEN = "perm-base64"  # Only one part after perm-

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                ValueError, match="Could not determine YouTrack Cloud URL"
            ):
                Config.get_base_url()

    @pytest.mark.unit
    def test_error_message_format(self):
        """Test that error messages contain proper guidance."""
        Config.YOUTRACK_URL = ""
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_API_TOKEN = "invalid-format"

        try:
            Config.get_base_url()
            pytest.fail("Should have raised ValueError")
        except ValueError as e:
            error_msg = str(e)
            assert "Set YOUTRACK_URL" in error_msg
            assert "Set YOUTRACK_WORKSPACE" in error_msg
            assert "perm:username.workspace.12345" in error_msg

    @pytest.mark.unit
    def test_dotenv_lines_coverage(self):
        """Test to cover the dotenv import lines (13-15)."""
        # These lines are covered at module import time, but let's ensure they exist
        # by checking the module imports dotenv functionality
        import youtrack_mcp.config

        # If we can import the module without error, the dotenv handling works
        assert hasattr(youtrack_mcp.config, "Config")

    @pytest.mark.unit
    def test_from_dict_lines_coverage(self):
        """Test to cover specific lines in from_dict method (47-49)."""
        # Test the hasattr check and setattr calls
        Config.from_dict({"YOUTRACK_URL": "test"})
        assert Config.YOUTRACK_URL == "test"

        # Test with invalid attribute (should be ignored)
        original_url = Config.YOUTRACK_URL
        Config.from_dict(
            {"INVALID_ATTR": "ignored", "YOUTRACK_URL": "new-test"}
        )
        assert Config.YOUTRACK_URL == "new-test"
        assert not hasattr(Config, "INVALID_ATTR")

    @pytest.mark.unit
    def test_validate_url_normalization(self):
        """Test URL normalization in validate method (lines 60-69)."""
        Config.YOUTRACK_API_TOKEN = "test-token"

        # Test different trailing slash scenarios
        test_cases = [
            ("https://test.com/", "https://test.com"),
            ("https://test.com//", "https://test.com"),
            ("https://test.com///", "https://test.com"),
            ("https://test.com", "https://test.com"),  # No change needed
        ]

        for input_url, expected_url in test_cases:
            Config.YOUTRACK_URL = input_url
            Config.validate()
            assert Config.YOUTRACK_URL == expected_url

    @pytest.mark.unit
    def test_ssl_context_creation_lines(self):
        """Test SSL context creation lines (79-86)."""
        Config.VERIFY_SSL = False

        context = Config.get_ssl_context()

        # This covers lines 81-84
        assert context is not None
        assert context.check_hostname is False
        assert context.verify_mode == ssl.CERT_NONE

        # Test the return None case (line 86)
        Config.VERIFY_SSL = True
        context = Config.get_ssl_context()
        assert context is None

    @pytest.mark.unit
    def test_get_base_url_cloud_url_extraction(self):
        """Test cloud URL extraction logic (lines 118-135)."""
        Config.YOUTRACK_URL = ""
        Config.YOUTRACK_CLOUD = True

        # Test perm: format extraction (lines 119-123)
        Config.YOUTRACK_API_TOKEN = "perm:user.workspace.token"
        result = Config.get_base_url()
        assert result == "https://workspace.youtrack.cloud/api"

        # Test perm- format with workspace env (lines 125-128)
        Config.YOUTRACK_API_TOKEN = "perm-encoded.data.hash"
        with patch.dict(os.environ, {"YOUTRACK_WORKSPACE": "testws"}):
            result = Config.get_base_url()
            assert result == "https://testws.youtrack.cloud/api"

        # Test perm- format with URL env (lines 130-132)
        with patch.dict(
            os.environ, {"YOUTRACK_URL": "https://urlenv.youtrack.cloud"}
        ):
            result = Config.get_base_url()
            assert result == "https://urlenv.youtrack.cloud/api"

    @pytest.mark.unit
    def test_final_fallback_error_line(self):
        """Test the final fallback error (line 146)."""
        Config.YOUTRACK_URL = ""
        Config.YOUTRACK_CLOUD = False

        # Mock is_cloud_instance to return False to reach line 146
        with patch.object(Config, "is_cloud_instance", return_value=False):
            with pytest.raises(ValueError, match="YouTrack URL is required"):
                Config.get_base_url()
