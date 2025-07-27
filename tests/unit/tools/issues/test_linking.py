"""
Tests for YouTrack Issue Linking Module.

Tests the issue relationship and dependency management functions with focus on:
- Generic issue linking with various link types
- Issue dependency management (depends on/blocks relationships)
- Specialized relationship creation (relates, duplicates)
- Link retrieval and available link types discovery
- Dependency removal with command-based operations
"""

import json
import pytest
from unittest.mock import Mock, patch

from youtrack_mcp.tools.issues.linking import Linking


class TestLinking:
    """Test suite for linking functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_issues_api = Mock()
        self.mock_projects_api = Mock()
        self.mock_client = Mock()
        self.mock_issues_api.client = self.mock_client
        self.linking = Linking(self.mock_issues_api, self.mock_projects_api)

    def test_link_issues_success(self):
        """Test successful issue linking."""
        # Arrange
        source_issue_id = "DEMO-123"
        target_issue_id = "DEMO-456"
        link_type = "Relates"
        
        mock_link_result = {
            "id": "link-789",
            "source": {"id": "3-123", "idReadable": source_issue_id},
            "target": {"id": "3-456", "idReadable": target_issue_id},
            "linkType": {"name": link_type}
        }
        
        self.mock_issues_api.link_issues.return_value = mock_link_result
        
        # Act
        result = self.linking.link_issues(source_issue_id, target_issue_id, link_type)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["id"] == "link-789"
        assert result_data["source"]["idReadable"] == source_issue_id
        assert result_data["target"]["idReadable"] == target_issue_id
        assert result_data["linkType"]["name"] == link_type
        
        # Verify API call
        self.mock_issues_api.link_issues.assert_called_once_with(
            source_issue_id, target_issue_id, link_type
        )

    def test_link_issues_api_error(self):
        """Test link_issues when API call fails."""
        # Arrange
        source_issue_id = "DEMO-123"
        target_issue_id = "DEMO-456"
        link_type = "Relates"
        
        self.mock_issues_api.link_issues.side_effect = Exception("Link creation failed")
        
        # Act
        result = self.linking.link_issues(source_issue_id, target_issue_id, link_type)
        result_data = json.loads(result)
        
        # Assert
        assert "error" in result_data
        assert "Link creation failed" in result_data["error"]
        assert result_data["status"] == "error"

    def test_get_issue_links_success(self):
        """Test successful retrieval of issue links."""
        # Arrange
        issue_id = "DEMO-123"
        mock_links_result = {
            "inward": [
                {
                    "id": "link-1",
                    "source": {"idReadable": "DEMO-456"},
                    "linkType": {"name": "Depends on"}
                }
            ],
            "outward": [
                {
                    "id": "link-2", 
                    "target": {"idReadable": "DEMO-789"},
                    "linkType": {"name": "Relates"}
                }
            ]
        }
        
        self.mock_issues_api.get_issue_links.return_value = mock_links_result
        
        # Act
        result = self.linking.get_issue_links(issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert "inward" in result_data
        assert "outward" in result_data
        assert len(result_data["inward"]) == 1
        assert len(result_data["outward"]) == 1
        assert result_data["inward"][0]["source"]["idReadable"] == "DEMO-456"
        assert result_data["outward"][0]["target"]["idReadable"] == "DEMO-789"
        
        # Verify API call
        self.mock_issues_api.get_issue_links.assert_called_once_with(issue_id)

    def test_get_issue_links_api_error(self):
        """Test get_issue_links when API call fails."""
        # Arrange
        issue_id = "DEMO-123"
        self.mock_issues_api.get_issue_links.side_effect = Exception("Links not found")
        
        # Act
        result = self.linking.get_issue_links(issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert "error" in result_data
        assert "Links not found" in result_data["error"]
        assert result_data["status"] == "error"

    def test_get_available_link_types_success(self):
        """Test successful retrieval of available link types."""
        # Arrange
        mock_link_types = [
            {
                "id": "type-1",
                "name": "Relates",
                "sourceToTarget": "relates to",
                "targetToSource": "relates to"
            },
            {
                "id": "type-2",
                "name": "Depends on",
                "sourceToTarget": "depends on",
                "targetToSource": "is required for"
            },
            {
                "id": "type-3",
                "name": "Duplicates",
                "sourceToTarget": "duplicates",
                "targetToSource": "is duplicated by"
            }
        ]
        
        self.mock_issues_api.get_available_link_types.return_value = mock_link_types
        
        # Act
        result = self.linking.get_available_link_types()
        result_data = json.loads(result)
        
        # Assert
        assert len(result_data) == 3
        assert result_data[0]["name"] == "Relates"
        assert result_data[1]["name"] == "Depends on" 
        assert result_data[2]["name"] == "Duplicates"
        
        # Verify API call
        self.mock_issues_api.get_available_link_types.assert_called_once()

    def test_get_available_link_types_api_error(self):
        """Test get_available_link_types when API call fails."""
        # Arrange
        self.mock_issues_api.get_available_link_types.side_effect = Exception("Link types not available")
        
        # Act
        result = self.linking.get_available_link_types()
        result_data = json.loads(result)
        
        # Assert
        assert "error" in result_data
        assert "Link types not available" in result_data["error"]
        assert result_data["status"] == "error"

    def test_add_dependency_success(self):
        """Test successful dependency addition."""
        # Arrange
        dependent_issue_id = "DEMO-123"
        dependency_issue_id = "DEMO-456"
        
        # Mock the result from link_issues (which add_dependency calls)
        mock_dependency_result = {
            "id": "link-dep",
            "source": {"idReadable": dependent_issue_id},
            "target": {"idReadable": dependency_issue_id},
            "linkType": {"name": "Depends on"}
        }
        
        self.mock_issues_api.link_issues.return_value = mock_dependency_result
        
        # Act
        result = self.linking.add_dependency(dependent_issue_id, dependency_issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["linkType"]["name"] == "Depends on"
        assert result_data["source"]["idReadable"] == dependent_issue_id
        assert result_data["target"]["idReadable"] == dependency_issue_id
        
        # Verify it calls link_issues with correct parameters
        self.mock_issues_api.link_issues.assert_called_once_with(
            dependent_issue_id, dependency_issue_id, "Depends on"
        )

    def test_add_dependency_api_error(self):
        """Test add_dependency when underlying link_issues fails."""
        # Arrange
        dependent_issue_id = "DEMO-123"
        dependency_issue_id = "DEMO-456"
        
        self.mock_issues_api.link_issues.side_effect = Exception("Dependency creation failed")
        
        # Act
        result = self.linking.add_dependency(dependent_issue_id, dependency_issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert "error" in result_data
        assert "Dependency creation failed" in result_data["error"]
        assert result_data["status"] == "error"

    def test_remove_dependency_success(self):
        """Test successful dependency removal."""
        # Arrange
        dependent_issue_id = "DEMO-123"
        dependency_issue_id = "DEMO-456"
        
        # Mock internal ID retrieval
        self.mock_issues_api._get_internal_id.return_value = "3-123"
        self.mock_issues_api._get_readable_id.return_value = "DEMO-456"
        
        # Mock command API response
        mock_command_response = {"status": "success"}
        self.mock_client.post.return_value = mock_command_response
        
        # Act
        result = self.linking.remove_dependency(dependent_issue_id, dependency_issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["status"] == "success"
        assert "Successfully removed dependency" in result_data["message"]
        assert result_data["command"] == "remove depends on DEMO-456"
        
        # Verify API calls
        self.mock_issues_api._get_internal_id.assert_called_once_with(dependent_issue_id)
        self.mock_issues_api._get_readable_id.assert_called_once_with(dependency_issue_id)
        
        expected_command_data = {
            "query": "remove depends on DEMO-456",
            "issues": [{"id": "3-123"}]
        }
        self.mock_client.post.assert_called_once_with("commands", data=expected_command_data)

    def test_remove_dependency_api_error(self):
        """Test remove_dependency when API call fails."""
        # Arrange
        dependent_issue_id = "DEMO-123"
        dependency_issue_id = "DEMO-456"
        
        self.mock_issues_api._get_internal_id.side_effect = Exception("ID lookup failed")
        
        # Act
        result = self.linking.remove_dependency(dependent_issue_id, dependency_issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert "error" in result_data
        assert "ID lookup failed" in result_data["error"]
        assert result_data["status"] == "error"

    def test_add_relates_link_success(self):
        """Test successful relates link addition."""
        # Arrange
        source_issue_id = "DEMO-123"
        target_issue_id = "DEMO-456"
        
        mock_relates_result = {
            "id": "link-relates",
            "source": {"idReadable": source_issue_id},
            "target": {"idReadable": target_issue_id},
            "linkType": {"name": "Relates"}
        }
        
        self.mock_issues_api.link_issues.return_value = mock_relates_result
        
        # Act
        result = self.linking.add_relates_link(source_issue_id, target_issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["linkType"]["name"] == "Relates"
        assert result_data["source"]["idReadable"] == source_issue_id
        assert result_data["target"]["idReadable"] == target_issue_id
        
        # Verify it calls link_issues with "Relates"
        self.mock_issues_api.link_issues.assert_called_once_with(
            source_issue_id, target_issue_id, "Relates"
        )

    def test_add_relates_link_api_error(self):
        """Test add_relates_link when API call fails."""
        # Arrange
        source_issue_id = "DEMO-123"
        target_issue_id = "DEMO-456"
        
        self.mock_issues_api.link_issues.side_effect = Exception("Relates link failed")
        
        # Act
        result = self.linking.add_relates_link(source_issue_id, target_issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert "error" in result_data
        assert "Relates link failed" in result_data["error"]
        assert result_data["status"] == "error"

    def test_add_duplicate_link_success(self):
        """Test successful duplicate link addition."""
        # Arrange
        duplicate_issue_id = "DEMO-123"
        original_issue_id = "DEMO-456"
        
        mock_duplicate_result = {
            "id": "link-duplicate",
            "source": {"idReadable": duplicate_issue_id},
            "target": {"idReadable": original_issue_id},
            "linkType": {"name": "Duplicates"}
        }
        
        self.mock_issues_api.link_issues.return_value = mock_duplicate_result
        
        # Act
        result = self.linking.add_duplicate_link(duplicate_issue_id, original_issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["linkType"]["name"] == "Duplicates"
        assert result_data["source"]["idReadable"] == duplicate_issue_id
        assert result_data["target"]["idReadable"] == original_issue_id
        
        # Verify it calls link_issues with "Duplicates"
        self.mock_issues_api.link_issues.assert_called_once_with(
            duplicate_issue_id, original_issue_id, "Duplicates"
        )

    def test_add_duplicate_link_api_error(self):
        """Test add_duplicate_link when API call fails."""
        # Arrange
        duplicate_issue_id = "DEMO-123"
        original_issue_id = "DEMO-456"
        
        self.mock_issues_api.link_issues.side_effect = Exception("Duplicate link failed")
        
        # Act
        result = self.linking.add_duplicate_link(duplicate_issue_id, original_issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert "error" in result_data
        assert "Duplicate link failed" in result_data["error"]
        assert result_data["status"] == "error"

    def test_get_tool_definitions(self):
        """Test tool definitions for linking functions."""
        # Act
        definitions = self.linking.get_tool_definitions()
        
        # Assert
        expected_functions = [
            "link_issues",
            "get_issue_links",
            "get_available_link_types",
            "add_dependency",
            "remove_dependency",
            "add_relates_link",
            "add_duplicate_link"
        ]
        
        for func_name in expected_functions:
            assert func_name in definitions
            assert "description" in definitions[func_name]
            assert "parameter_descriptions" in definitions[func_name]
        
        # Check specific parameter descriptions
        link_def = definitions["link_issues"]
        assert "source_issue_id" in link_def["parameter_descriptions"]
        assert "target_issue_id" in link_def["parameter_descriptions"]
        assert "link_type" in link_def["parameter_descriptions"]
        
        get_links_def = definitions["get_issue_links"]
        assert "issue_id" in get_links_def["parameter_descriptions"]
        
        # get_available_link_types has no parameters
        link_types_def = definitions["get_available_link_types"]
        assert len(link_types_def["parameter_descriptions"]) == 0
        
        dependency_def = definitions["add_dependency"]
        assert "dependent_issue_id" in dependency_def["parameter_descriptions"]
        assert "dependency_issue_id" in dependency_def["parameter_descriptions"]
        
        remove_dep_def = definitions["remove_dependency"]
        assert "dependent_issue_id" in remove_dep_def["parameter_descriptions"]
        assert "dependency_issue_id" in remove_dep_def["parameter_descriptions"]
        
        relates_def = definitions["add_relates_link"]
        assert "source_issue_id" in relates_def["parameter_descriptions"]
        assert "target_issue_id" in relates_def["parameter_descriptions"]
        
        duplicate_def = definitions["add_duplicate_link"]
        assert "duplicate_issue_id" in duplicate_def["parameter_descriptions"]
        assert "original_issue_id" in duplicate_def["parameter_descriptions"]

    def test_remove_dependency_non_dict_response(self):
        """Test remove_dependency when command API returns non-dict response."""
        # Arrange
        dependent_issue_id = "DEMO-123"
        dependency_issue_id = "DEMO-456"
        
        self.mock_issues_api._get_internal_id.return_value = "3-123"
        self.mock_issues_api._get_readable_id.return_value = "DEMO-456"
        
        # Mock non-dict response (like a string or list)
        mock_response = "Command executed successfully"
        self.mock_client.post.return_value = mock_response
        
        # Act
        result = self.linking.remove_dependency(dependent_issue_id, dependency_issue_id)
        result_data = json.loads(result)
        
        # Assert - should get the raw response formatted
        assert result_data == mock_response

    @pytest.mark.parametrize("link_type,description", [
        ("Relates", "General relationship"),
        ("Depends on", "Dependency relationship"),
        ("Duplicates", "Duplicate marking"),
        ("Blocks", "Blocking relationship"),
        ("Parent for", "Parent-child relationship")
    ])
    def test_link_issues_with_different_link_types(self, link_type, description):
        """Test link_issues with various link type values."""
        # Arrange
        source_issue_id = "DEMO-123"
        target_issue_id = "DEMO-456"
        
        mock_result = {
            "linkType": {"name": link_type},
            "description": description
        }
        
        self.mock_issues_api.link_issues.return_value = mock_result
        
        # Act
        result = self.linking.link_issues(source_issue_id, target_issue_id, link_type)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["linkType"]["name"] == link_type 