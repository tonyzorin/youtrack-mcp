"""Tests for tool filtering functionality."""

import pytest
from unittest.mock import Mock, patch
from youtrack_mcp.config import Config
from youtrack_mcp.tools.loader import filter_tools


class TestToolNameNormalization:
    """Test tool name normalization."""

    @pytest.mark.unit
    def test_normalize_strips_whitespace(self):
        """Test that whitespace is stripped."""
        assert Config._normalize_tool_name("  get_issue  ") == "get_issue"

    @pytest.mark.unit
    def test_normalize_lowercase(self):
        """Test that names are lowercased."""
        assert Config._normalize_tool_name("Get_Issue") == "get_issue"
        assert Config._normalize_tool_name("GET_ISSUE") == "get_issue"

    @pytest.mark.unit
    def test_normalize_replaces_hyphens(self):
        """Test that hyphens are replaced with underscores."""
        assert Config._normalize_tool_name("get-issue") == "get_issue"
        assert Config._normalize_tool_name("search-with-filter") == "search_with_filter"

    @pytest.mark.unit
    def test_normalize_combined(self):
        """Test combined normalization."""
        assert Config._normalize_tool_name("  Get-Issue  ") == "get_issue"
        assert Config._normalize_tool_name("  SEARCH-WITH-FILTER  ") == "search_with_filter"


class TestConfigParsing:
    """Test configuration parsing for tool filtering."""

    def setup_method(self):
        """Store original values before each test."""
        self.original_disabled = Config.DISABLED_TOOLS
        self.original_enabled = Config.ENABLED_TOOLS

    def teardown_method(self):
        """Restore original values after each test."""
        Config.DISABLED_TOOLS = self.original_disabled
        Config.ENABLED_TOOLS = self.original_enabled

    @pytest.mark.unit
    def test_get_disabled_tools_empty(self):
        """Test empty DISABLED_TOOLS returns empty set."""
        Config.DISABLED_TOOLS = ""
        assert Config.get_disabled_tools() == set()

    @pytest.mark.unit
    def test_get_disabled_tools_single(self):
        """Test single tool in DISABLED_TOOLS."""
        Config.DISABLED_TOOLS = "get_issue"
        assert Config.get_disabled_tools() == {"get_issue"}

    @pytest.mark.unit
    def test_get_disabled_tools_multiple(self):
        """Test multiple tools in DISABLED_TOOLS."""
        Config.DISABLED_TOOLS = "get_issue,create_issue,search_issues"
        result = Config.get_disabled_tools()
        assert result == {"get_issue", "create_issue", "search_issues"}

    @pytest.mark.unit
    def test_get_disabled_tools_with_whitespace(self):
        """Test DISABLED_TOOLS with whitespace."""
        Config.DISABLED_TOOLS = " get_issue , create_issue "
        result = Config.get_disabled_tools()
        assert result == {"get_issue", "create_issue"}

    @pytest.mark.unit
    def test_get_disabled_tools_with_variations(self):
        """Test DISABLED_TOOLS with case and hyphen variations."""
        Config.DISABLED_TOOLS = "Get-Issue, CREATE_ISSUE"
        result = Config.get_disabled_tools()
        assert result == {"get_issue", "create_issue"}

    @pytest.mark.unit
    def test_get_disabled_tools_ignores_empty_entries(self):
        """Test DISABLED_TOOLS ignores empty entries from extra commas."""
        Config.DISABLED_TOOLS = "get_issue,,create_issue,"
        result = Config.get_disabled_tools()
        assert result == {"get_issue", "create_issue"}

    @pytest.mark.unit
    def test_get_enabled_tools_empty(self):
        """Test empty ENABLED_TOOLS returns empty set."""
        Config.ENABLED_TOOLS = ""
        assert Config.get_enabled_tools() == set()

    @pytest.mark.unit
    def test_get_enabled_tools_multiple(self):
        """Test multiple tools in ENABLED_TOOLS."""
        Config.ENABLED_TOOLS = "get_issue,search_issues"
        result = Config.get_enabled_tools()
        assert result == {"get_issue", "search_issues"}

    @pytest.mark.unit
    def test_is_allowlist_mode_false(self):
        """Test allowlist mode is false when ENABLED_TOOLS is empty."""
        Config.ENABLED_TOOLS = ""
        assert Config.is_allowlist_mode() is False

    @pytest.mark.unit
    def test_is_allowlist_mode_true(self):
        """Test allowlist mode is true when ENABLED_TOOLS is set."""
        Config.ENABLED_TOOLS = "get_issue"
        assert Config.is_allowlist_mode() is True

    @pytest.mark.unit
    def test_is_allowlist_mode_whitespace_only(self):
        """Test allowlist mode is false for whitespace-only ENABLED_TOOLS."""
        Config.ENABLED_TOOLS = "   "
        assert Config.is_allowlist_mode() is False


class TestFilterTools:
    """Test the filter_tools function."""

    def setup_method(self):
        """Store original values before each test."""
        self.original_disabled = Config.DISABLED_TOOLS
        self.original_enabled = Config.ENABLED_TOOLS

    def teardown_method(self):
        """Restore original values after each test."""
        Config.DISABLED_TOOLS = self.original_disabled
        Config.ENABLED_TOOLS = self.original_enabled

    @pytest.fixture
    def sample_tools(self):
        """Create sample tools dict for testing."""
        return {
            "get_issue": Mock(),
            "create_issue": Mock(),
            "search_issues": Mock(),
            "get_projects": Mock(),
            "get_user": Mock(),
        }

    @pytest.mark.unit
    def test_no_filtering(self, sample_tools):
        """Test no filtering when neither env var is set."""
        Config.DISABLED_TOOLS = ""
        Config.ENABLED_TOOLS = ""
        result = filter_tools(sample_tools)
        assert result == sample_tools

    @pytest.mark.unit
    def test_denylist_single_tool(self, sample_tools):
        """Test disabling a single tool."""
        Config.DISABLED_TOOLS = "get_issue"
        Config.ENABLED_TOOLS = ""
        result = filter_tools(sample_tools)
        assert "get_issue" not in result
        assert len(result) == 4

    @pytest.mark.unit
    def test_denylist_multiple_tools(self, sample_tools):
        """Test disabling multiple tools."""
        Config.DISABLED_TOOLS = "get_issue,create_issue"
        Config.ENABLED_TOOLS = ""
        result = filter_tools(sample_tools)
        assert "get_issue" not in result
        assert "create_issue" not in result
        assert len(result) == 3

    @pytest.mark.unit
    def test_denylist_case_insensitive(self, sample_tools):
        """Test that denylist is case insensitive."""
        Config.DISABLED_TOOLS = "GET_ISSUE,Create_Issue"
        Config.ENABLED_TOOLS = ""
        result = filter_tools(sample_tools)
        assert "get_issue" not in result
        assert "create_issue" not in result

    @pytest.mark.unit
    def test_denylist_hyphen_underscore_equivalent(self, sample_tools):
        """Test that hyphens and underscores are equivalent in denylist."""
        Config.DISABLED_TOOLS = "get-issue,create-issue"
        Config.ENABLED_TOOLS = ""
        result = filter_tools(sample_tools)
        assert "get_issue" not in result
        assert "create_issue" not in result

    @pytest.mark.unit
    def test_allowlist_single_tool(self, sample_tools):
        """Test enabling only a single tool."""
        Config.ENABLED_TOOLS = "get_issue"
        Config.DISABLED_TOOLS = ""
        result = filter_tools(sample_tools)
        assert list(result.keys()) == ["get_issue"]

    @pytest.mark.unit
    def test_allowlist_multiple_tools(self, sample_tools):
        """Test enabling multiple tools."""
        Config.ENABLED_TOOLS = "get_issue,search_issues"
        Config.DISABLED_TOOLS = ""
        result = filter_tools(sample_tools)
        assert set(result.keys()) == {"get_issue", "search_issues"}

    @pytest.mark.unit
    def test_allowlist_precedence(self, sample_tools):
        """Test that allowlist takes precedence over denylist."""
        Config.ENABLED_TOOLS = "get_issue,search_issues"
        Config.DISABLED_TOOLS = "get_issue"
        # Even though get_issue is in DISABLED_TOOLS, allowlist takes precedence
        result = filter_tools(sample_tools)
        assert "get_issue" in result
        assert len(result) == 2

    @pytest.mark.unit
    def test_invalid_tool_name_denylist(self, sample_tools, caplog):
        """Test warning for invalid tool name in denylist."""
        Config.DISABLED_TOOLS = "nonexistent_tool"
        Config.ENABLED_TOOLS = ""
        result = filter_tools(sample_tools)
        assert len(result) == 5  # No tools filtered
        assert "nonexistent_tool" in caplog.text
        assert "unknown tool" in caplog.text.lower()

    @pytest.mark.unit
    def test_invalid_tool_name_allowlist(self, sample_tools, caplog):
        """Test warning for invalid tool name in allowlist."""
        Config.ENABLED_TOOLS = "nonexistent_tool,get_issue"
        Config.DISABLED_TOOLS = ""
        result = filter_tools(sample_tools)
        assert list(result.keys()) == ["get_issue"]
        assert "nonexistent_tool" in caplog.text

    @pytest.mark.unit
    def test_denylist_all_tools(self, sample_tools):
        """Test disabling all tools."""
        Config.DISABLED_TOOLS = "get_issue,create_issue,search_issues,get_projects,get_user"
        Config.ENABLED_TOOLS = ""
        result = filter_tools(sample_tools)
        assert len(result) == 0

    @pytest.mark.unit
    def test_allowlist_preserves_tool_references(self, sample_tools):
        """Test that allowlist preserves the original tool references."""
        Config.ENABLED_TOOLS = "get_issue"
        Config.DISABLED_TOOLS = ""
        result = filter_tools(sample_tools)
        assert result["get_issue"] is sample_tools["get_issue"]

    @pytest.mark.unit
    def test_denylist_preserves_tool_references(self, sample_tools):
        """Test that denylist preserves the original tool references."""
        Config.DISABLED_TOOLS = "get_issue"
        Config.ENABLED_TOOLS = ""
        result = filter_tools(sample_tools)
        assert result["create_issue"] is sample_tools["create_issue"]

    @pytest.mark.unit
    def test_empty_tools_dict(self):
        """Test filtering an empty tools dict."""
        Config.DISABLED_TOOLS = "get_issue"
        Config.ENABLED_TOOLS = ""
        result = filter_tools({})
        assert result == {}

    @pytest.mark.unit
    def test_allowlist_empty_tools_dict(self):
        """Test allowlist filtering an empty tools dict."""
        Config.ENABLED_TOOLS = "get_issue"
        Config.DISABLED_TOOLS = ""
        result = filter_tools({})
        assert result == {}


class TestFilterToolsLogging:
    """Test logging behavior of filter_tools."""

    def setup_method(self):
        """Store original values before each test."""
        self.original_disabled = Config.DISABLED_TOOLS
        self.original_enabled = Config.ENABLED_TOOLS

    def teardown_method(self):
        """Restore original values after each test."""
        Config.DISABLED_TOOLS = self.original_disabled
        Config.ENABLED_TOOLS = self.original_enabled

    @pytest.fixture
    def sample_tools(self):
        """Create sample tools dict for testing."""
        return {
            "get_issue": Mock(),
            "create_issue": Mock(),
            "search_issues": Mock(),
        }

    @pytest.mark.unit
    def test_denylist_logs_disabled_tools(self, sample_tools, caplog):
        """Test that denylist mode logs which tools were disabled."""
        Config.DISABLED_TOOLS = "get_issue,create_issue"
        Config.ENABLED_TOOLS = ""

        import logging
        with caplog.at_level(logging.INFO):
            filter_tools(sample_tools)

        assert "Denylist mode" in caplog.text
        assert "2 tools disabled" in caplog.text

    @pytest.mark.unit
    def test_allowlist_logs_enabled_count(self, sample_tools, caplog):
        """Test that allowlist mode logs enabled/disabled counts."""
        Config.ENABLED_TOOLS = "get_issue"
        Config.DISABLED_TOOLS = ""

        import logging
        with caplog.at_level(logging.INFO):
            filter_tools(sample_tools)

        assert "Allowlist mode" in caplog.text
        assert "1 tool enabled" in caplog.text
        assert "2 tools disabled" in caplog.text
