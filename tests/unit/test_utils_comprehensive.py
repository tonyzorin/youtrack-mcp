"""
Comprehensive tests for youtrack_mcp.utils module.
These tests cover all available functions with edge cases and error scenarios.
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, List, Any
from unittest.mock import patch
from unittest import mock
import os

from youtrack_mcp.utils import convert_timestamp_to_iso8601, add_iso8601_timestamps


class TestConvertTimestampToIso8601:
    """Comprehensive tests for convert_timestamp_to_iso8601 function."""

    @pytest.mark.unit
    def test_convert_valid_timestamps(self):
        """Test convert_timestamp_to_iso8601 with valid timestamps."""
        test_cases = [
            (0, "1970-01-01T00:00:00+00:00"),  # Unix epoch
            (1672531200000, "2023-01-01T00:00:00+00:00"),  # New Year 2023
            (1609459200000, "2021-01-01T00:00:00+00:00"),  # New Year 2021
            (946684800000, "2000-01-01T00:00:00+00:00"),   # Y2K
        ]
        
        for timestamp_ms, expected_start in test_cases:
            result = convert_timestamp_to_iso8601(timestamp_ms)
            assert isinstance(result, str)
            assert expected_start in result or result.endswith("Z")

    @pytest.mark.unit
    def test_convert_edge_timestamps(self):
        """Test convert_timestamp_to_iso8601 with edge case timestamps."""
        # Very small positive timestamp
        result = convert_timestamp_to_iso8601(1)
        assert isinstance(result, str)
        assert "1970" in result
        
        # Large but valid timestamp (year 2100)
        large_timestamp = 4102444800000
        result = convert_timestamp_to_iso8601(large_timestamp)
        assert isinstance(result, str)
        
        # Very large timestamp that might cause overflow
        huge_timestamp = 999999999999999999
        result = convert_timestamp_to_iso8601(huge_timestamp)
        assert isinstance(result, str)
        # Should return string representation on overflow
        assert "999999999999999999" in result

    @pytest.mark.unit
    def test_convert_negative_timestamps(self):
        """Test convert_timestamp_to_iso8601 with negative timestamps."""
        # Negative timestamp (before Unix epoch)
        result = convert_timestamp_to_iso8601(-86400000)  # One day before epoch
        assert isinstance(result, str)
        
        # Very negative timestamp
        result = convert_timestamp_to_iso8601(-999999999999)
        assert isinstance(result, str)

    @pytest.mark.unit
    def test_convert_error_handling(self):
        """Test error handling in convert_timestamp_to_iso8601."""
        # Test with timestamp that causes ValueError
        with patch('youtrack_mcp.utils.datetime') as mock_datetime:
            mock_datetime.fromtimestamp.side_effect = ValueError("Invalid timestamp")
            mock_datetime.timezone = timezone
            
            result = convert_timestamp_to_iso8601(1234567890)
            
            # Should return string representation of original timestamp
            assert result == "1234567890"

    @pytest.mark.unit
    def test_convert_overflow_error(self):
        """Test overflow error handling in convert_timestamp_to_iso8601."""
        # Test with timestamp that causes OverflowError
        with patch('youtrack_mcp.utils.datetime') as mock_datetime:
            mock_datetime.fromtimestamp.side_effect = OverflowError("Timestamp overflow")
            mock_datetime.timezone = timezone
            
            result = convert_timestamp_to_iso8601(999999999999999999)
            
            # Should return string representation of original timestamp
            assert result == "999999999999999999"

    @pytest.mark.unit
    def test_convert_os_error(self):
        """Test OS error handling in convert_timestamp_to_iso8601."""
        # Test with timestamp that causes OSError
        with patch('youtrack_mcp.utils.datetime') as mock_datetime:
            mock_datetime.fromtimestamp.side_effect = OSError("System error")
            mock_datetime.timezone = timezone
            
            result = convert_timestamp_to_iso8601(1672531200000)
            
            # Should return string representation of original timestamp
            assert result == "1672531200000"


class TestAddIso8601Timestamps:
    """Comprehensive tests for add_iso8601_timestamps function."""

    @pytest.mark.unit
    def test_add_timestamps_to_dict(self):
        """Test adding ISO8601 timestamps to dictionary."""
        data = {
            "id": "TEST-123",
            "created": 1672531200000,  # 2023-01-01 00:00:00 UTC
            "updated": 1672617600000,  # 2023-01-02 00:00:00 UTC
            "summary": "Test issue"
        }
        
        result = add_iso8601_timestamps(data)
        
        assert isinstance(result, dict)
        assert result["id"] == "TEST-123"
        assert result["summary"] == "Test issue"
        assert result["created"] == 1672531200000
        assert result["updated"] == 1672617600000
        assert "created_iso8601" in result
        assert "updated_iso8601" in result
        assert "2023-01-01" in result["created_iso8601"]
        assert "2023-01-02" in result["updated_iso8601"]

    @pytest.mark.unit
    def test_add_timestamps_to_nested_dict(self):
        """Test adding ISO8601 timestamps to nested dictionary."""
        data = {
            "issue": {
                "id": "TEST-123",
                "created": 1672531200000,
                "metadata": {
                    "updated": 1672617600000,
                    "author": "user123"
                }
            },
            "project": {
                "created": 1609459200000,
                "name": "Test Project"
            }
        }
        
        result = add_iso8601_timestamps(data)
        
        assert isinstance(result, dict)
        assert "created_iso8601" in result["issue"]
        assert "updated_iso8601" in result["issue"]["metadata"]
        assert "created_iso8601" in result["project"]
        assert "2023-01-01" in result["issue"]["created_iso8601"]
        assert "2023-01-02" in result["issue"]["metadata"]["updated_iso8601"]
        assert "2021-01-01" in result["project"]["created_iso8601"]

    @pytest.mark.unit
    def test_add_timestamps_to_list(self):
        """Test adding ISO8601 timestamps to list of dictionaries."""
        data = [
            {"id": "TEST-1", "created": 1672531200000},
            {"id": "TEST-2", "updated": 1672617600000},
            {"id": "TEST-3", "created": 1609459200000, "updated": 1672531200000}
        ]
        
        result = add_iso8601_timestamps(data)
        
        assert isinstance(result, list)
        assert len(result) == 3
        assert "created_iso8601" in result[0]
        assert "updated_iso8601" in result[1]
        assert "created_iso8601" in result[2]
        assert "updated_iso8601" in result[2]

    @pytest.mark.unit
    def test_add_timestamps_to_mixed_data(self):
        """Test adding ISO8601 timestamps to mixed data types."""
        data = {
            "issues": [
                {"id": "TEST-1", "created": 1672531200000},
                {"id": "TEST-2", "updated": 1672617600000}
            ],
            "metadata": {
                "created": 1609459200000,
                "stats": {
                    "updated": 1672531200000,
                    "count": 10
                }
            },
            "simple_value": "string",
            "number": 42
        }
        
        result = add_iso8601_timestamps(data)
        
        assert isinstance(result, dict)
        assert "created_iso8601" in result["issues"][0]
        assert "updated_iso8601" in result["issues"][1]
        assert "created_iso8601" in result["metadata"]
        assert "updated_iso8601" in result["metadata"]["stats"]
        assert result["simple_value"] == "string"
        assert result["number"] == 42

    @pytest.mark.unit
    def test_add_timestamps_with_none_values(self):
        """Test adding ISO8601 timestamps when timestamp values are None."""
        data = {
            "id": "TEST-123",
            "created": None,
            "updated": 1672531200000,
            "deleted": None
        }
        
        result = add_iso8601_timestamps(data)
        
        assert isinstance(result, dict)
        assert result["created"] is None
        assert "created_iso8601" not in result  # Should not add ISO8601 for None values
        assert "updated_iso8601" in result
        assert result["deleted"] is None

    @pytest.mark.unit
    def test_add_timestamps_with_invalid_timestamps(self):
        """Test adding ISO8601 timestamps with invalid timestamp values."""
        data = {
            "id": "TEST-123",
            "created": "not_a_number",
            "updated": 1672531200000,
            "invalid": -999999999999999999999
        }
        
        result = add_iso8601_timestamps(data)
        
        assert isinstance(result, dict)
        assert result["created"] == "not_a_number"
        # Should not add ISO8601 for invalid timestamps
        assert "created_iso8601" not in result
        assert "updated_iso8601" in result
        # Should handle very large negative numbers
        assert result["invalid"] == -999999999999999999999

    @pytest.mark.unit
    def test_add_timestamps_preserves_original(self):
        """Test that adding ISO8601 timestamps preserves original data."""
        original_data = {
            "id": "TEST-123",
            "created": 1672531200000,
            "summary": "Original summary"
        }
        
        result = add_iso8601_timestamps(original_data)
        
        # Should not modify original data
        assert "created_iso8601" not in original_data
        assert result["id"] == original_data["id"]
        assert result["created"] == original_data["created"]
        assert result["summary"] == original_data["summary"]
        assert "created_iso8601" in result

    @pytest.mark.unit
    def test_add_timestamps_with_non_dict_list(self):
        """Test adding ISO8601 timestamps with non-dict/list input."""
        # Test with string
        result = add_iso8601_timestamps("simple string")
        assert result == "simple string"
        
        # Test with number
        result = add_iso8601_timestamps(42)
        assert result == 42
        
        # Test with None
        result = add_iso8601_timestamps(None)
        assert result is None
        
        # Test with boolean
        result = add_iso8601_timestamps(True)
        assert result is True

    @pytest.mark.unit
    def test_add_timestamps_empty_structures(self):
        """Test adding ISO8601 timestamps to empty structures."""
        # Empty dictionary
        result = add_iso8601_timestamps({})
        assert result == {}
        
        # Empty list
        result = add_iso8601_timestamps([])
        assert result == []

    @pytest.mark.unit
    def test_add_timestamps_complex_nesting(self):
        """Test adding ISO8601 timestamps to deeply nested structures."""
        data = {
            "level1": {
                "level2": {
                    "level3": [
                        {
                            "level4": {
                                "created": 1672531200000,
                                "updated": 1672617600000
                            }
                        }
                    ]
                }
            }
        }
        
        result = add_iso8601_timestamps(data)
        
        assert isinstance(result, dict)
        level4 = result["level1"]["level2"]["level3"][0]["level4"]
        assert "created_iso8601" in level4
        assert "updated_iso8601" in level4
        assert "2023-01-01" in level4["created_iso8601"]
        assert "2023-01-02" in level4["updated_iso8601"]

    @pytest.mark.unit
    def test_add_timestamps_with_zero_timestamp(self):
        """Test adding ISO8601 timestamps with zero timestamp (Unix epoch)."""
        data = {
            "id": "TEST-123",
            "created": 0,
            "updated": 0
        }
        
        result = add_iso8601_timestamps(data)
        
        assert isinstance(result, dict)
        assert "created_iso8601" in result
        assert "updated_iso8601" in result
        assert "1970-01-01" in result["created_iso8601"]
        assert "1970-01-01" in result["updated_iso8601"] 