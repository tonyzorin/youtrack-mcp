"""
Tests for YouTrack Issue Attachments Module.

Tests the issue attachment and raw data access functions with focus on:
- Raw issue data retrieval bypassing Pydantic models
- Attachment content access with base64 encoding
- Comprehensive attachment metadata retrieval
- File size analysis and format conversion
- Error handling for missing attachments or invalid IDs
"""

import json
import base64
import pytest
from unittest.mock import Mock, patch

from youtrack_mcp.tools.issues.attachments import Attachments


class TestAttachments:
    """Test suite for attachment functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_issues_api = Mock()
        self.mock_projects_api = Mock()
        self.mock_client = Mock()
        self.mock_issues_api.client = self.mock_client
        self.attachments = Attachments(self.mock_issues_api, self.mock_projects_api)

    def test_get_issue_raw_success(self):
        """Test successful raw issue data retrieval."""
        # Arrange
        issue_id = "DEMO-123"
        
        mock_raw_issue = {
            "id": "3-123",
            "idReadable": issue_id,
            "summary": "Test Issue",
            "description": "Test description",
            "created": "2024-01-01T10:00:00Z",
            "updated": "2024-01-02T15:30:00Z",
            "project": {
                "id": "1-1",
                "name": "Demo Project",
                "shortName": "DEMO"
            },
            "reporter": {
                "id": "2-1",
                "login": "admin",
                "name": "Administrator"
            },
            "assignee": {
                "id": "2-2", 
                "login": "developer",
                "name": "Developer User"
            },
            "customFields": [
                {
                    "id": "field-1",
                    "name": "Priority",
                    "value": {"id": "151-1", "name": "Normal"}
                },
                {
                    "id": "field-2",
                    "name": "State",
                    "value": {"id": "154-1", "name": "Open"}
                }
            ],
            "attachments": [
                {
                    "id": "1-456",
                    "name": "screenshot.png",
                    "size": 1024,
                    "url": "/api/files/1-456"
                }
            ],
            "comments": [
                {
                    "id": "comment-1",
                    "text": "Test comment",
                    "author": {"login": "admin", "name": "Administrator"},
                    "created": "2024-01-01T11:00:00Z"
                }
            ]
        }
        
        expected_fields = "id,idReadable,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value(id,name)),attachments(id,name,size,url),comments(id,text,author(login,name),created)"
        self.mock_client.get.return_value = mock_raw_issue
        
        # Act
        result = self.attachments.get_issue_raw(issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["idReadable"] == issue_id
        assert result_data["summary"] == "Test Issue"
        assert result_data["project"]["shortName"] == "DEMO"
        assert len(result_data["customFields"]) == 2
        assert len(result_data["attachments"]) == 1
        assert len(result_data["comments"]) == 1
        
        # Verify API call with comprehensive fields
        self.mock_client.get.assert_called_once_with(f"issues/{issue_id}?fields={expected_fields}")

    def test_get_issue_raw_api_error(self):
        """Test get_issue_raw when API call fails."""
        # Arrange
        issue_id = "DEMO-123"
        self.mock_client.get.side_effect = Exception("Issue not found")
        
        # Act
        result = self.attachments.get_issue_raw(issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert "error" in result_data
        assert "Issue not found" in result_data["error"]

    def test_get_issue_raw_missing_issue_id(self):
        """Test get_issue_raw with empty issue ID."""
        # Arrange
        issue_id = ""
        self.mock_client.get.side_effect = Exception("Invalid issue ID")
        
        # Act
        result = self.attachments.get_issue_raw(issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert "error" in result_data
        assert "Invalid issue ID" in result_data["error"]

    def test_get_attachment_content_success(self):
        """Test successful attachment content retrieval."""
        # Arrange
        issue_id = "DEMO-123"
        attachment_id = "1-456"
        
        # Mock binary content (simulating a small image file)
        original_content = b"PNG\x89\x00\x00\x00\rIHDR\x00\x00test_image_data"
        expected_base64 = base64.b64encode(original_content).decode("utf-8")
        
        # Mock attachment metadata
        mock_issue_response = {
            "attachments": [
                {
                    "id": attachment_id,
                    "name": "screenshot.png",
                    "mimeType": "image/png",
                    "size": len(original_content)
                }
            ]
        }
        
        self.mock_issues_api.get_attachment_content.return_value = original_content
        self.mock_client.get.return_value = mock_issue_response
        
        # Act
        result = self.attachments.get_attachment_content(issue_id, attachment_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["content"] == expected_base64
        assert result_data["size_bytes_original"] == len(original_content)
        assert result_data["size_bytes_base64"] == len(expected_base64)
        assert result_data["filename"] == "screenshot.png"
        assert result_data["mime_type"] == "image/png"
        assert result_data["status"] == "success"
        assert isinstance(result_data["size_increase_percent"], float)
        
        # Verify API calls
        self.mock_issues_api.get_attachment_content.assert_called_once_with(issue_id, attachment_id)
        self.mock_client.get.assert_called_once_with(f"issues/{issue_id}?fields=attachments(id,name,mimeType,size)")

    def test_get_attachment_content_no_metadata(self):
        """Test attachment content retrieval when metadata is missing."""
        # Arrange
        issue_id = "DEMO-123"
        attachment_id = "1-456"
        original_content = b"test file content"
        expected_base64 = base64.b64encode(original_content).decode("utf-8")
        
        # Mock response with no attachments
        mock_issue_response = {"attachments": []}
        
        self.mock_issues_api.get_attachment_content.return_value = original_content
        self.mock_client.get.return_value = mock_issue_response
        
        # Act
        result = self.attachments.get_attachment_content(issue_id, attachment_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["content"] == expected_base64
        assert result_data["filename"] is None
        assert result_data["mime_type"] is None
        assert result_data["status"] == "success"

    def test_get_attachment_content_metadata_no_attachments_key(self):
        """Test attachment content when issue response has no attachments key."""
        # Arrange
        issue_id = "DEMO-123"
        attachment_id = "1-456"
        original_content = b"test content"
        expected_base64 = base64.b64encode(original_content).decode("utf-8")
        
        # Mock response without attachments key
        mock_issue_response = {"id": "3-123", "summary": "Test Issue"}
        
        self.mock_issues_api.get_attachment_content.return_value = original_content
        self.mock_client.get.return_value = mock_issue_response
        
        # Act
        result = self.attachments.get_attachment_content(issue_id, attachment_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["content"] == expected_base64
        assert result_data["filename"] is None
        assert result_data["mime_type"] is None
        assert result_data["status"] == "success"

    def test_get_attachment_content_metadata_wrong_attachment_id(self):
        """Test attachment content when metadata exists but for different attachment."""
        # Arrange
        issue_id = "DEMO-123"
        attachment_id = "1-456"
        original_content = b"test content"
        expected_base64 = base64.b64encode(original_content).decode("utf-8")
        
        # Mock response with different attachment ID
        mock_issue_response = {
            "attachments": [
                {
                    "id": "1-789",  # Different ID
                    "name": "other_file.txt",
                    "mimeType": "text/plain",
                    "size": 100
                }
            ]
        }
        
        self.mock_issues_api.get_attachment_content.return_value = original_content
        self.mock_client.get.return_value = mock_issue_response
        
        # Act
        result = self.attachments.get_attachment_content(issue_id, attachment_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["content"] == expected_base64
        assert result_data["filename"] is None  # No metadata found for our attachment ID
        assert result_data["mime_type"] is None
        assert result_data["status"] == "success"

    def test_get_attachment_content_api_error(self):
        """Test get_attachment_content when API call fails."""
        # Arrange
        issue_id = "DEMO-123"
        attachment_id = "1-456"
        
        self.mock_issues_api.get_attachment_content.side_effect = Exception("Attachment not found")
        
        # Act
        result = self.attachments.get_attachment_content(issue_id, attachment_id)
        result_data = json.loads(result)
        
        # Assert
        assert "error" in result_data
        assert "Attachment not found" in result_data["error"]
        assert result_data["status"] == "error"

    def test_get_attachment_content_metadata_api_error(self):
        """Test get_attachment_content when content succeeds but metadata fails."""
        # Arrange
        issue_id = "DEMO-123"
        attachment_id = "1-456"
        original_content = b"test content"
        
        self.mock_issues_api.get_attachment_content.return_value = original_content
        self.mock_client.get.side_effect = Exception("Metadata fetch failed")
        
        # Act
        result = self.attachments.get_attachment_content(issue_id, attachment_id)
        result_data = json.loads(result)
        
        # Assert - should still fail because metadata fetch is part of the function
        assert "error" in result_data
        assert "Metadata fetch failed" in result_data["error"]
        assert result_data["status"] == "error"

    def test_get_attachment_content_large_file_analysis(self):
        """Test attachment content with large file for size analysis."""
        # Arrange
        issue_id = "DEMO-123"
        attachment_id = "1-456"
        
        # Create a larger file to test size calculation
        original_content = b"A" * 1000  # 1KB of 'A' characters
        expected_base64 = base64.b64encode(original_content).decode("utf-8")
        
        mock_issue_response = {
            "attachments": [
                {
                    "id": attachment_id,
                    "name": "large_file.txt",
                    "mimeType": "text/plain",
                    "size": len(original_content)
                }
            ]
        }
        
        self.mock_issues_api.get_attachment_content.return_value = original_content
        self.mock_client.get.return_value = mock_issue_response
        
        # Act
        result = self.attachments.get_attachment_content(issue_id, attachment_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["size_bytes_original"] == 1000
        assert result_data["size_bytes_base64"] == len(expected_base64)
        # Base64 encoding typically increases size by ~33%
        size_increase = result_data["size_increase_percent"]
        assert 30 <= size_increase <= 40  # Should be around 33%
        assert result_data["filename"] == "large_file.txt"
        assert result_data["mime_type"] == "text/plain"

    def test_get_attachment_content_empty_file(self):
        """Test attachment content with empty file."""
        # Arrange
        issue_id = "DEMO-123" 
        attachment_id = "1-456"
        original_content = b""  # Empty file
        expected_base64 = base64.b64encode(original_content).decode("utf-8")
        
        mock_issue_response = {
            "attachments": [
                {
                    "id": attachment_id,
                    "name": "empty.txt",
                    "mimeType": "text/plain",
                    "size": 0
                }
            ]
        }
        
        self.mock_issues_api.get_attachment_content.return_value = original_content
        self.mock_client.get.return_value = mock_issue_response
        
        # Act
        result = self.attachments.get_attachment_content(issue_id, attachment_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["content"] == expected_base64
        assert result_data["size_bytes_original"] == 0
        assert result_data["size_bytes_base64"] == len(expected_base64)
        assert result_data["filename"] == "empty.txt"
        assert result_data["status"] == "success"

    def test_get_tool_definitions(self):
        """Test tool definitions for attachment functions."""
        # Act
        definitions = self.attachments.get_tool_definitions()
        
        # Assert
        expected_functions = ["get_issue_raw", "get_attachment_content"]
        
        for func_name in expected_functions:
            assert func_name in definitions
            assert "description" in definitions[func_name]
            assert "parameter_descriptions" in definitions[func_name]
        
        # Check specific parameter descriptions
        raw_def = definitions["get_issue_raw"]
        assert "issue_id" in raw_def["parameter_descriptions"]
        assert "raw issue data" in raw_def["description"].lower()
        assert "pydantic" in raw_def["description"].lower()
        
        attachment_def = definitions["get_attachment_content"]
        assert "issue_id" in attachment_def["parameter_descriptions"]
        assert "attachment_id" in attachment_def["parameter_descriptions"]
        assert "base64" in attachment_def["description"].lower()
        assert "10mb" in attachment_def["description"].lower()

    def test_get_attachment_content_with_special_characters_filename(self):
        """Test attachment content with special characters in filename."""
        # Arrange
        issue_id = "DEMO-123"
        attachment_id = "1-456"
        original_content = b"test content"
        expected_base64 = base64.b64encode(original_content).decode("utf-8")
        
        mock_issue_response = {
            "attachments": [
                {
                    "id": attachment_id,
                    "name": "test file with spaces & symbols!@#.txt",
                    "mimeType": "text/plain",
                    "size": len(original_content)
                }
            ]
        }
        
        self.mock_issues_api.get_attachment_content.return_value = original_content
        self.mock_client.get.return_value = mock_issue_response
        
        # Act
        result = self.attachments.get_attachment_content(issue_id, attachment_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["filename"] == "test file with spaces & symbols!@#.txt"
        assert result_data["status"] == "success"

    def test_get_attachment_content_json_parsing(self):
        """Test that get_attachment_content returns valid JSON."""
        # Arrange
        issue_id = "DEMO-123"
        attachment_id = "1-456"
        original_content = b"simple content"
        
        mock_issue_response = {"attachments": []}
        
        self.mock_issues_api.get_attachment_content.return_value = original_content
        self.mock_client.get.return_value = mock_issue_response
        
        # Act
        result = self.attachments.get_attachment_content(issue_id, attachment_id)
        
        # Assert - should be valid JSON
        result_data = json.loads(result)  # This will raise if invalid JSON
        assert isinstance(result_data, dict)
        assert "content" in result_data
        assert "status" in result_data 