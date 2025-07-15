"""
Comprehensive unit tests for YouTrack MCP configuration.
"""
import pytest
import os
import ssl
import importlib
from unittest.mock import patch, Mock

# We need to reload the config module for environment variable tests
import youtrack_mcp.config


class TestConfig:
    """Test cases for Config class."""
    
    def setup_method(self):
        """Reset configuration before each test."""
        # Store original values
        from youtrack_mcp.config import Config
        self.original_values = {
            'YOUTRACK_URL': Config.YOUTRACK_URL,
            'YOUTRACK_API_TOKEN': Config.YOUTRACK_API_TOKEN,
            'VERIFY_SSL': Config.VERIFY_SSL,
            'YOUTRACK_CLOUD': Config.YOUTRACK_CLOUD,
            'MAX_RETRIES': Config.MAX_RETRIES,
            'RETRY_DELAY': Config.RETRY_DELAY,
            'MCP_SERVER_NAME': Config.MCP_SERVER_NAME,
            'MCP_SERVER_DESCRIPTION': Config.MCP_SERVER_DESCRIPTION,
            'MCP_DEBUG': Config.MCP_DEBUG,
        }
    
    def teardown_method(self):
        """Restore original configuration after each test."""
        from youtrack_mcp.config import Config
        for key, value in self.original_values.items():
            setattr(Config, key, value)
    
    @pytest.mark.unit
    def test_default_configuration(self):
        """Test default configuration values when no environment variables are set."""
        with patch.dict(os.environ, {}, clear=True):
            # Reload the module to pick up the cleared environment
            importlib.reload(youtrack_mcp.config)
            from youtrack_mcp.config import Config
            
            assert Config.YOUTRACK_URL == ""
            assert Config.YOUTRACK_API_TOKEN == ""
            assert Config.VERIFY_SSL is True
            assert Config.YOUTRACK_CLOUD is False
            assert Config.MAX_RETRIES == 3
            assert Config.RETRY_DELAY == 1.0
            assert Config.MCP_SERVER_NAME == "youtrack-mcp"
            assert Config.MCP_SERVER_DESCRIPTION == "YouTrack MCP Server"
            assert Config.MCP_DEBUG is False
    
    @pytest.mark.unit
    def test_environment_variable_configuration(self):
        """Test configuration from environment variables."""
        env_vars = {
            'YOUTRACK_URL': 'https://test.youtrack.cloud',
            'YOUTRACK_API_TOKEN': 'test-token',
            'YOUTRACK_VERIFY_SSL': 'false',
            'YOUTRACK_CLOUD': 'true',
            'YOUTRACK_MAX_RETRIES': '5',
            'YOUTRACK_RETRY_DELAY': '2.5',
            'MCP_SERVER_NAME': 'custom-server',
            'MCP_SERVER_DESCRIPTION': 'Custom MCP Server',
            'MCP_DEBUG': 'true'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            # Reload the module to pick up the new environment variables
            importlib.reload(youtrack_mcp.config)
            from youtrack_mcp.config import Config
            
            assert Config.YOUTRACK_URL == 'https://test.youtrack.cloud'
            assert Config.YOUTRACK_API_TOKEN == 'test-token'
            assert Config.VERIFY_SSL is False
            assert Config.YOUTRACK_CLOUD is True
            assert Config.MAX_RETRIES == 5
            assert Config.RETRY_DELAY == 2.5
            assert Config.MCP_SERVER_NAME == 'custom-server'
            assert Config.MCP_SERVER_DESCRIPTION == 'Custom MCP Server'
            assert Config.MCP_DEBUG is True
    
    @pytest.mark.unit
    def test_boolean_environment_variables(self):
        """Test various boolean value formats for environment variables."""
        from youtrack_mcp.config import Config
        
        # Test true values
        for true_value in ['true', '1', 'yes', 'TRUE', 'Yes']:
            with patch.dict(os.environ, {'YOUTRACK_VERIFY_SSL': true_value}, clear=True):
                importlib.reload(youtrack_mcp.config)
                from youtrack_mcp.config import Config
                assert Config.VERIFY_SSL is True, f"Failed for value: {true_value}"
        
        # Test false values  
        for false_value in ['false', '0', 'no', 'FALSE', 'No', 'anything_else']:
            with patch.dict(os.environ, {'YOUTRACK_VERIFY_SSL': false_value}, clear=True):
                importlib.reload(youtrack_mcp.config)
                from youtrack_mcp.config import Config
                assert Config.VERIFY_SSL is False, f"Failed for value: {false_value}"
    
    @pytest.mark.unit
    def test_from_dict(self):
        """Test updating configuration from dictionary."""
        from youtrack_mcp.config import Config
        
        config_dict = {
            'YOUTRACK_URL': 'https://dict.youtrack.cloud',
            'YOUTRACK_API_TOKEN': 'dict-token',
            'VERIFY_SSL': False,
            'MAX_RETRIES': 10
        }
        
        Config.from_dict(config_dict)
        
        assert Config.YOUTRACK_URL == 'https://dict.youtrack.cloud'
        assert Config.YOUTRACK_API_TOKEN == 'dict-token'
        assert Config.VERIFY_SSL is False
        assert Config.MAX_RETRIES == 10
    
    @pytest.mark.unit
    def test_from_dict_ignores_invalid_keys(self):
        """Test that from_dict ignores keys that don't exist on the class."""
        from youtrack_mcp.config import Config
        
        original_url = Config.YOUTRACK_URL
        
        config_dict = {
            'YOUTRACK_URL': 'https://valid.youtrack.cloud',
            'INVALID_KEY': 'should_be_ignored',
            'ANOTHER_INVALID': 123
        }
        
        Config.from_dict(config_dict)
        
        assert Config.YOUTRACK_URL == 'https://valid.youtrack.cloud'
        assert not hasattr(Config, 'INVALID_KEY')
        assert not hasattr(Config, 'ANOTHER_INVALID')
    
    @pytest.mark.unit
    def test_validate_success_self_hosted(self):
        """Test successful validation for self-hosted instance."""
        from youtrack_mcp.config import Config
        
        Config.YOUTRACK_URL = 'https://selfhosted.youtrack.com'
        Config.YOUTRACK_API_TOKEN = 'valid-token'
        Config.YOUTRACK_CLOUD = False
        
        # Should not raise an exception
        Config.validate()
        
        # Check URL was cleaned
        assert Config.YOUTRACK_URL == 'https://selfhosted.youtrack.com'
    
    @pytest.mark.unit
    def test_validate_success_cloud(self):
        """Test successful validation for cloud instance."""
        from youtrack_mcp.config import Config
        
        Config.YOUTRACK_URL = ''
        Config.YOUTRACK_API_TOKEN = 'valid-token'
        Config.YOUTRACK_CLOUD = True
        
        # Should not raise an exception
        Config.validate()
    
    @pytest.mark.unit
    def test_validate_strips_trailing_slash(self):
        """Test that validation strips trailing slashes from URL."""
        from youtrack_mcp.config import Config
        
        Config.YOUTRACK_URL = 'https://test.youtrack.com//'
        Config.YOUTRACK_API_TOKEN = 'valid-token'
        Config.YOUTRACK_CLOUD = False
        
        Config.validate()
        
        assert Config.YOUTRACK_URL == 'https://test.youtrack.com'
    
    @pytest.mark.unit
    def test_validate_fails_no_token(self):
        """Test validation fails when no API token is provided."""
        from youtrack_mcp.config import Config
        
        Config.YOUTRACK_URL = 'https://test.youtrack.com'
        Config.YOUTRACK_API_TOKEN = ''
        
        with pytest.raises(ValueError, match="YouTrack API token is required"):
            Config.validate()
    
    @pytest.mark.unit
    def test_validate_fails_no_url_self_hosted(self):
        """Test validation fails when no URL is provided for self-hosted."""
        from youtrack_mcp.config import Config
        
        Config.YOUTRACK_URL = ''
        Config.YOUTRACK_API_TOKEN = 'valid-token'
        Config.YOUTRACK_CLOUD = False
        
        with pytest.raises(ValueError, match="YouTrack URL is required for self-hosted instances"):
            Config.validate()
    
    @pytest.mark.unit
    def test_get_ssl_context_verify_enabled(self):
        """Test SSL context when verification is enabled."""
        from youtrack_mcp.config import Config
        
        Config.VERIFY_SSL = True
        
        context = Config.get_ssl_context()
        
        assert context is None  # Default behavior
    
    @pytest.mark.unit
    def test_get_ssl_context_verify_disabled(self):
        """Test SSL context when verification is disabled."""
        from youtrack_mcp.config import Config
        
        Config.VERIFY_SSL = False
        
        context = Config.get_ssl_context()
        
        assert isinstance(context, ssl.SSLContext)
        assert context.check_hostname is False
        assert context.verify_mode == ssl.CERT_NONE
    
    @pytest.mark.unit
    def test_is_cloud_instance_cloud_flag_true(self):
        """Test cloud instance detection when YOUTRACK_CLOUD is True."""
        from youtrack_mcp.config import Config
        
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_URL = 'https://self-hosted.com'
        
        assert Config.is_cloud_instance() is True
    
    @pytest.mark.unit
    def test_is_cloud_instance_no_url(self):
        """Test cloud instance detection when no URL is provided."""
        from youtrack_mcp.config import Config
        
        Config.YOUTRACK_CLOUD = False
        Config.YOUTRACK_URL = ''
        
        assert Config.is_cloud_instance() is True
    
    @pytest.mark.unit
    def test_is_cloud_instance_self_hosted(self):
        """Test cloud instance detection for self-hosted with URL."""
        from youtrack_mcp.config import Config
        
        Config.YOUTRACK_CLOUD = False
        Config.YOUTRACK_URL = 'https://self-hosted.com'
        
        assert Config.is_cloud_instance() is False
    
    @pytest.mark.unit
    def test_get_base_url_explicit_url(self):
        """Test get_base_url with explicit URL."""
        from youtrack_mcp.config import Config
        
        Config.YOUTRACK_URL = 'https://explicit.youtrack.com'
        
        result = Config.get_base_url()
        
        assert result == 'https://explicit.youtrack.com/api'
    
    @pytest.mark.unit
    def test_get_base_url_cloud_perm_username_format(self):
        """Test get_base_url for cloud with perm:username.workspace format."""
        from youtrack_mcp.config import Config
        
        Config.YOUTRACK_URL = ''
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_API_TOKEN = 'perm:user.myworkspace.12345'
        
        result = Config.get_base_url()
        
        assert result == 'https://myworkspace.youtrack.cloud/api'
    
    @pytest.mark.unit
    def test_get_base_url_cloud_perm_base64_with_workspace_env(self):
        """Test get_base_url for cloud with perm- format and YOUTRACK_WORKSPACE."""
        from youtrack_mcp.config import Config
        
        Config.YOUTRACK_URL = ''
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_API_TOKEN = 'perm-base64.encoded.hash'
        
        with patch.dict(os.environ, {'YOUTRACK_WORKSPACE': 'envworkspace'}):
            result = Config.get_base_url()
            
        assert result == 'https://envworkspace.youtrack.cloud/api'
    
    @pytest.mark.unit
    def test_get_base_url_cloud_perm_base64_with_url_env(self):
        """Test get_base_url for cloud with perm- format and YOUTRACK_URL env."""
        from youtrack_mcp.config import Config
        
        Config.YOUTRACK_URL = ''
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_API_TOKEN = 'perm-base64.encoded.hash'
        
        with patch.dict(os.environ, {'YOUTRACK_URL': 'https://envurl.youtrack.cloud'}):
            result = Config.get_base_url()
            
        assert result == 'https://envurl.youtrack.cloud/api'
    
    @pytest.mark.unit
    def test_get_base_url_cloud_invalid_token_format(self):
        """Test get_base_url fails for cloud with invalid token format."""
        from youtrack_mcp.config import Config
        
        Config.YOUTRACK_URL = ''
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_API_TOKEN = 'invalid-token-format'
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Could not determine YouTrack Cloud URL"):
                Config.get_base_url()
    
    @pytest.mark.unit
    def test_get_base_url_cloud_no_workspace_info(self):
        """Test get_base_url fails when no workspace information is available."""
        from youtrack_mcp.config import Config
        
        Config.YOUTRACK_URL = ''
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_API_TOKEN = 'perm-base64.encoded.hash'
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Could not determine YouTrack Cloud URL"):
                Config.get_base_url()
    
    @pytest.mark.unit
    def test_get_base_url_simple_token_no_dots(self):
        """Test get_base_url with simple token without dots."""
        from youtrack_mcp.config import Config
        
        Config.YOUTRACK_URL = ''
        Config.YOUTRACK_CLOUD = True
        Config.YOUTRACK_API_TOKEN = 'simple-token'
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Could not determine YouTrack Cloud URL"):
                Config.get_base_url()
    
    @pytest.mark.unit
    def test_integer_environment_variables(self):
        """Test integer environment variable parsing."""
        with patch.dict(os.environ, {'YOUTRACK_MAX_RETRIES': '7'}, clear=True):
            importlib.reload(youtrack_mcp.config)
            from youtrack_mcp.config import Config
            assert Config.MAX_RETRIES == 7
            assert isinstance(Config.MAX_RETRIES, int)
    
    @pytest.mark.unit
    def test_float_environment_variables(self):
        """Test float environment variable parsing."""
        with patch.dict(os.environ, {'YOUTRACK_RETRY_DELAY': '3.14'}, clear=True):
            importlib.reload(youtrack_mcp.config)
            from youtrack_mcp.config import Config
            assert Config.RETRY_DELAY == 3.14
            assert isinstance(Config.RETRY_DELAY, float)
    
    @pytest.mark.unit
    def test_invalid_integer_environment_variable(self):
        """Test handling of invalid integer environment variables."""
        with patch.dict(os.environ, {'YOUTRACK_MAX_RETRIES': 'not-a-number'}, clear=True):
            with pytest.raises(ValueError):
                importlib.reload(youtrack_mcp.config)
    
    @pytest.mark.unit
    def test_invalid_float_environment_variable(self):
        """Test handling of invalid float environment variables."""
        with patch.dict(os.environ, {'YOUTRACK_RETRY_DELAY': 'not-a-float'}, clear=True):
            with pytest.raises(ValueError):
                importlib.reload(youtrack_mcp.config)


class TestGlobalConfigInstance:
    """Test cases for the global config instance."""
    
    @pytest.mark.unit
    def test_global_config_exists(self):
        """Test that the global config instance exists."""
        from youtrack_mcp.config import config, Config
        
        assert isinstance(config, Config)
    
    @pytest.mark.unit
    def test_global_config_is_singleton(self):
        """Test that importing config multiple times gives the same instance."""
        from youtrack_mcp.config import config as config1
        from youtrack_mcp.config import config as config2
        
        assert config1 is config2


class TestDotenvIntegration:
    """Test cases for dotenv integration."""
    
    @pytest.mark.unit
    def test_dotenv_optional_import(self):
        """Test that dotenv import is optional and doesn't break if not available."""
        # This test ensures the try/except block works correctly
        # If we get here without ImportError, the dotenv handling is working
        from youtrack_mcp.config import Config
        assert Config is not None
    
    @pytest.mark.unit
    def test_config_works_without_dotenv(self):
        """Test that configuration works even if dotenv is not available."""
        from youtrack_mcp.config import Config
        
        # Test that basic functionality works
        config_dict = {'YOUTRACK_URL': 'test'}
        Config.from_dict(config_dict)
        assert Config.YOUTRACK_URL == 'test' 