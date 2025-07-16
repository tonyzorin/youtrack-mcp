import pytest
import re
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from youtrack_mcp import version


class TestVersion:
    """Test version module."""

    @pytest.mark.unit
    def test_version_exists(self):
        """Test that __version__ exists and is a string."""
        assert hasattr(version, "__version__")
        assert isinstance(version.__version__, str)

    @pytest.mark.unit
    def test_version_format(self):
        """Test that version follows semantic versioning format."""
        version_str = version.__version__

        # Should match semantic versioning pattern (major.minor.patch)
        # Allow for optional pre-release and build metadata
        semver_pattern = r"^\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?(?:\+[a-zA-Z0-9.-]+)?$"
        assert re.match(
            semver_pattern, version_str
        ), f"Version {version_str} doesn't follow semantic versioning"

    @pytest.mark.unit
    def test_version_not_empty(self):
        """Test that version is not empty."""
        assert version.__version__.strip() != ""

    @pytest.mark.unit
    def test_version_components(self):
        """Test that version has at least major.minor.patch components."""
        version_parts = version.__version__.split(".")

        # Should have at least 3 parts (major, minor, patch)
        assert len(version_parts) >= 3

        # First three parts should be numeric
        for i in range(3):
            assert version_parts[
                i
            ].isdigit(), f"Version component {i} should be numeric"

    @pytest.mark.unit
    def test_version_consistency(self):
        """Test that version is consistent with expected format."""
        # The version should be a reasonable version number
        version_str = version.__version__

        # Should not contain spaces
        assert " " not in version_str

        # Should start with a digit
        assert version_str[0].isdigit()

        # Should contain at least one dot
        assert "." in version_str

    @pytest.mark.unit
    def test_module_docstring(self):
        """Test that the module has a docstring."""
        assert version.__doc__ is not None
        assert isinstance(version.__doc__, str)
        assert len(version.__doc__.strip()) > 0

    @pytest.mark.unit
    def test_can_import_version(self):
        """Test that version can be imported directly."""
        # Test importing the version directly
        from youtrack_mcp.version import __version__

        assert isinstance(__version__, str)
        assert __version__ == version.__version__
