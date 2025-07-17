"""
Tests for youtrack_mcp/utils.py
"""

import json
import pytest
from datetime import datetime, timezone
from youtrack_mcp.utils import (
    convert_timestamp_to_iso8601,
    add_iso8601_timestamps,
    format_json_response
)


class TestConvertTimestampToIso8601:
    """Test convert_timestamp_to_iso8601 function."""

    def test_valid_timestamp_conversion(self):
        """Test converting valid timestamp to ISO8601."""
        # Test timestamp: 2023-01-01 00:00:00 UTC in milliseconds
        timestamp_ms = 1672531200000
        result = convert_timestamp_to_iso8601(timestamp_ms)
        
        assert result == "2023-01-01T00:00:00+00:00"

    def test_zero_timestamp(self):
        """Test converting zero timestamp."""
        result = convert_timestamp_to_iso8601(0)
        assert result == "1970-01-01T00:00:00+00:00"

    def test_negative_timestamp(self):
        """Test handling negative timestamp."""
        result = convert_timestamp_to_iso8601(-1000)
        assert result == "1969-12-31T23:59:59+00:00"

    def test_invalid_timestamp_value_error(self):
        """Test handling invalid timestamp that causes ValueError."""
        # Very large timestamp that might cause overflow
        invalid_timestamp = 9999999999999999999999
        result = convert_timestamp_to_iso8601(invalid_timestamp)
        assert result == str(invalid_timestamp)

    def test_invalid_timestamp_overflow_error(self):
        """Test handling timestamp that causes OverflowError."""
        # Test with extremely large value
        invalid_timestamp = float('inf')
        result = convert_timestamp_to_iso8601(invalid_timestamp)
        assert result == str(invalid_timestamp)

    def test_invalid_timestamp_os_error(self):
        """Test handling timestamp that might cause OSError."""
        # Test with very negative value that might cause platform-specific issues
        invalid_timestamp = -999999999999999999
        result = convert_timestamp_to_iso8601(invalid_timestamp)
        # Should either return valid ISO string or fallback to string representation
        assert isinstance(result, str)


class TestAddIso8601Timestamps:
    """Test add_iso8601_timestamps function."""

    def test_dict_with_created_timestamp(self):
        """Test adding ISO8601 timestamp to dict with created field."""
        data = {"created": 1672531200000, "name": "test"}
        result = add_iso8601_timestamps(data)
        
        assert result["created"] == 1672531200000
        assert result["created_iso8601"] == "2023-01-01T00:00:00+00:00"
        assert result["name"] == "test"

    def test_dict_with_updated_timestamp(self):
        """Test adding ISO8601 timestamp to dict with updated field."""
        data = {"updated": 1672531200000, "id": "123"}
        result = add_iso8601_timestamps(data)
        
        assert result["updated"] == 1672531200000
        assert result["updated_iso8601"] == "2023-01-01T00:00:00+00:00"
        assert result["id"] == "123"

    def test_dict_with_both_timestamps(self):
        """Test adding ISO8601 timestamps for both created and updated."""
        data = {
            "created": 1672531200000,
            "updated": 1672617600000,  # 2023-01-02 00:00:00 UTC
            "summary": "Test issue"
        }
        result = add_iso8601_timestamps(data)
        
        assert result["created_iso8601"] == "2023-01-01T00:00:00+00:00"
        assert result["updated_iso8601"] == "2023-01-02T00:00:00+00:00"
        assert result["summary"] == "Test issue"

    def test_dict_with_non_integer_timestamp(self):
        """Test dict with non-integer timestamp values."""
        data = {"created": "not-a-number", "updated": None}
        result = add_iso8601_timestamps(data)
        
        # Should not add ISO8601 fields for non-integer values
        assert "created_iso8601" not in result
        assert "updated_iso8601" not in result
        assert result["created"] == "not-a-number"
        assert result["updated"] is None

    def test_nested_dict_with_timestamps(self):
        """Test nested dictionaries with timestamps."""
        data = {
            "issue": {
                "created": 1672531200000,
                "summary": "Test"
            },
            "project": {
                "updated": 1672617600000,
                "name": "Demo"
            }
        }
        result = add_iso8601_timestamps(data)
        
        assert result["issue"]["created_iso8601"] == "2023-01-01T00:00:00+00:00"
        assert result["project"]["updated_iso8601"] == "2023-01-02T00:00:00+00:00"

    def test_list_with_timestamp_dicts(self):
        """Test list containing dictionaries with timestamps."""
        data = [
            {"created": 1672531200000, "id": "1"},
            {"updated": 1672617600000, "id": "2"}
        ]
        result = add_iso8601_timestamps(data)
        
        assert result[0]["created_iso8601"] == "2023-01-01T00:00:00+00:00"
        assert result[1]["updated_iso8601"] == "2023-01-02T00:00:00+00:00"

    def test_deeply_nested_structure(self):
        """Test deeply nested data structure with timestamps."""
        data = {
            "issues": [
                {
                    "created": 1672531200000,
                    "comments": [
                        {"created": 1672617600000, "text": "comment1"},
                        {"updated": 1672704000000, "text": "comment2"}
                    ]
                }
            ]
        }
        result = add_iso8601_timestamps(data)
        
        assert result["issues"][0]["created_iso8601"] == "2023-01-01T00:00:00+00:00"
        assert result["issues"][0]["comments"][0]["created_iso8601"] == "2023-01-02T00:00:00+00:00"
        assert result["issues"][0]["comments"][1]["updated_iso8601"] == "2023-01-03T00:00:00+00:00"

    def test_non_dict_non_list_data(self):
        """Test with data that is neither dict nor list."""
        data = "simple string"
        result = add_iso8601_timestamps(data)
        assert result == "simple string"

        data = 42
        result = add_iso8601_timestamps(data)
        assert result == 42

        data = None
        result = add_iso8601_timestamps(data)
        assert result is None

    def test_empty_dict(self):
        """Test with empty dictionary."""
        data = {}
        result = add_iso8601_timestamps(data)
        assert result == {}

    def test_empty_list(self):
        """Test with empty list."""
        data = []
        result = add_iso8601_timestamps(data)
        assert result == []

    def test_dict_copy_not_modify_original(self):
        """Test that original dict is not modified."""
        original_data = {"created": 1672531200000, "name": "test"}
        result = add_iso8601_timestamps(original_data)
        
        # Original should not have ISO8601 field
        assert "created_iso8601" not in original_data
        # Result should have ISO8601 field
        assert "created_iso8601" in result


class TestFormatJsonResponse:
    """Test format_json_response function."""

    def test_simple_dict_with_timestamp(self):
        """Test formatting simple dict with timestamp."""
        data = {"created": 1672531200000, "name": "test"}
        result = format_json_response(data)
        
        parsed = json.loads(result)
        assert parsed["created"] == 1672531200000
        assert parsed["created_iso8601"] == "2023-01-01T00:00:00+00:00"
        assert parsed["name"] == "test"

    def test_complex_nested_structure(self):
        """Test formatting complex nested structure."""
        data = {
            "issues": [
                {"created": 1672531200000, "id": "1"},
                {"updated": 1672617600000, "id": "2"}
            ],
            "total": 2
        }
        result = format_json_response(data)
        
        parsed = json.loads(result)
        assert parsed["issues"][0]["created_iso8601"] == "2023-01-01T00:00:00+00:00"
        assert parsed["issues"][1]["updated_iso8601"] == "2023-01-02T00:00:00+00:00"
        assert parsed["total"] == 2

    def test_data_without_timestamps(self):
        """Test formatting data without timestamp fields."""
        data = {"name": "test", "id": 123, "active": True}
        result = format_json_response(data)
        
        parsed = json.loads(result)
        assert parsed == data

    def test_none_data(self):
        """Test formatting None data."""
        result = format_json_response(None)
        assert result == "null"

    def test_string_data(self):
        """Test formatting string data."""
        result = format_json_response("test string")
        assert result == '"test string"'

    def test_number_data(self):
        """Test formatting number data."""
        result = format_json_response(42)
        assert result == "42"

    def test_boolean_data(self):
        """Test formatting boolean data."""
        result = format_json_response(True)
        assert result == "true"

    def test_list_data(self):
        """Test formatting list data."""
        data = [1, 2, {"created": 1672531200000}]
        result = format_json_response(data)
        
        parsed = json.loads(result)
        assert parsed[0] == 1
        assert parsed[1] == 2
        assert parsed[2]["created"] == 1672531200000
        assert parsed[2]["created_iso8601"] == "2023-01-01T00:00:00+00:00"

    def test_json_formatting_indented(self):
        """Test that JSON is properly indented."""
        data = {"key": "value", "nested": {"created": 1672531200000}}
        result = format_json_response(data)
        
        # Should be indented (contains newlines and spaces)
        assert "\n" in result
        assert "  " in result  # 2-space indentation 