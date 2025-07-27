"""
Tests for YouTrack Issue Basic Operations Module.

Tests the core CRUD operations with focus on:
- Issue retrieval with comprehensive field data
- Issue search using YouTrack query language
- Issue creation with project validation
- Issue updates for summary and description
- Comment addition with error handling
"""

import json
import pytest
from unittest.mock import Mock, patch

from youtrack_mcp.tools.issues.basic_operations import BasicOperations


class TestBasicOperations:
    """Test suite for basic CRUD operation functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_issues_api = Mock()
        self.mock_projects_api = Mock()
        self.mock_client = Mock()
        self.mock_issues_api.client = self.mock_client
        self.basic_ops = BasicOperations(self.mock_issues_api, self.mock_projects_api)

    def test_get_issue_success(self):
        """Test successful issue retrieval."""
        # Arrange
        issue_id = "DEMO-123"
        mock_issue_data = {
            "$type": "Issue",
            "id": "3-123",
            "idReadable": "DEMO-123",
            "summary": "Test issue",
            "description": "Issue description",
            "created": 1234567890,
            "updated": 1234567891,
            "project": {
                "id": "0-1",
                "name": "Demo Project",
                "shortName": "DEMO"
            },
            "reporter": {
                "id": "1-1",
                "login": "admin",
                "name": "Administrator"
            },
            "assignee": {
                "id": "1-2",
                "login": "user",
                "name": "Test User"
            },
            "customFields": [
                {"name": "Priority", "value": {"name": "Normal"}},
                {"name": "State", "value": {"name": "Open"}}
            ]
        }
        
        self.mock_client.get.return_value = mock_issue_data
        
        # Act
        result = self.basic_ops.get_issue(issue_id)
        result_data = json.loads(result)
        
        # Assert - verify key fields (format_json_response may add ISO dates)
        assert result_data["$type"] == mock_issue_data["$type"]
        assert result_data["id"] == mock_issue_data["id"]
        assert result_data["idReadable"] == mock_issue_data["idReadable"]
        assert result_data["summary"] == mock_issue_data["summary"]
        assert result_data["description"] == mock_issue_data["description"]
        assert result_data["project"] == mock_issue_data["project"]
        
        # Verify API call with correct fields
        expected_fields = "id,idReadable,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value)"
        self.mock_client.get.assert_called_once_with(f"issues/{issue_id}?fields={expected_fields}")

    def test_get_issue_minimal_response_enhancement(self):
        """Test get_issue enhances minimal responses with default summary."""
        # Arrange
        issue_id = "DEMO-123"
        mock_minimal_issue = {
            "$type": "Issue",
            "id": "3-123",
            "idReadable": "DEMO-123"
            # Missing summary
        }
        
        self.mock_client.get.return_value = mock_minimal_issue
        
        # Act
        result = self.basic_ops.get_issue(issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["summary"] == f"Issue {issue_id}"
        assert result_data["id"] == "3-123"

    def test_get_issue_api_error(self):
        """Test get_issue when API call fails."""
        # Arrange
        issue_id = "DEMO-123"
        self.mock_client.get.side_effect = Exception("Issue not found")
        
        # Act
        result = self.basic_ops.get_issue(issue_id)
        result_data = json.loads(result)
        
        # Assert
        assert "error" in result_data
        assert "Issue not found" in result_data["error"]

    def test_search_issues_success(self):
        """Test successful issue search."""
        # Arrange
        query = "project: DEMO #Unresolved"
        limit = 5
        mock_search_results = [
            {
                "id": "3-123",
                "idReadable": "DEMO-123",
                "summary": "First issue",
                "project": {"shortName": "DEMO"}
            },
            {
                "id": "3-124",
                "idReadable": "DEMO-124", 
                "summary": "Second issue",
                "project": {"shortName": "DEMO"}
            }
        ]
        
        self.mock_client.get.return_value = mock_search_results
        
        # Act
        result = self.basic_ops.search_issues(query, limit)
        result_data = json.loads(result)
        
        # Assert
        assert result_data == mock_search_results
        
        # Verify API call with correct parameters
        expected_fields = "id,idReadable,summary,description,created,updated,project(id,name,shortName),reporter(id,login,name),assignee(id,login,name),customFields(id,name,value)"
        expected_params = {"query": query, "$top": limit, "fields": expected_fields}
        self.mock_client.get.assert_called_once_with("issues", params=expected_params)

    def test_search_issues_default_limit(self):
        """Test search_issues with default limit."""
        # Arrange
        query = "project: DEMO"
        mock_search_results = []
        
        self.mock_client.get.return_value = mock_search_results
        
        # Act
        result = self.basic_ops.search_issues(query)  # No limit specified
        result_data = json.loads(result)
        
        # Assert
        assert result_data == mock_search_results
        
        # Verify default limit of 10 is used
        call_args = self.mock_client.get.call_args[1]["params"]
        assert call_args["$top"] == 10

    def test_search_issues_api_error(self):
        """Test search_issues when API call fails."""
        # Arrange
        query = "invalid query"
        self.mock_client.get.side_effect = Exception("Invalid query syntax")
        
        # Act
        result = self.basic_ops.search_issues(query)
        result_data = json.loads(result)
        
        # Assert
        assert "error" in result_data
        assert "Invalid query syntax" in result_data["error"]

    def test_create_issue_success_with_project_name(self):
        """Test successful issue creation with project short name."""
        # Arrange
        project = "DEMO"
        summary = "Test issue"
        description = "Test description"
        
        # Mock project lookup
        mock_project = Mock()
        mock_project.id = "0-1"
        mock_project.name = "Demo Project"
        self.mock_projects_api.get_project_by_name.return_value = mock_project
        
        # Mock issue creation
        mock_created_issue = Mock()
        mock_created_issue.id = "3-123"
        mock_created_issue.model_dump.return_value = {
            "id": "3-123",
            "idReadable": "DEMO-123",
            "summary": summary,
            "description": description
        }
        
        self.mock_issues_api.create_issue.return_value = mock_created_issue
        
        # Act
        result = self.basic_ops.create_issue(project, summary, description)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["id"] == "3-123"
        assert result_data["summary"] == summary
        assert result_data["description"] == description
        
        # Verify project lookup and issue creation
        self.mock_projects_api.get_project_by_name.assert_called_once_with(project)
        self.mock_issues_api.create_issue.assert_called_once_with("0-1", summary, description)

    def test_create_issue_success_with_project_id(self):
        """Test successful issue creation with project ID."""
        # Arrange
        project = "0-1"  # Project ID format
        summary = "Test issue"
        
        mock_created_issue = {"id": "3-123", "summary": summary}
        self.mock_issues_api.create_issue.return_value = mock_created_issue
        
        # Act
        result = self.basic_ops.create_issue(project, summary)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["id"] == "3-123"
        
        # Verify no project lookup was needed
        self.mock_projects_api.get_project_by_name.assert_not_called()
        self.mock_issues_api.create_issue.assert_called_once_with(project, summary, None)

    def test_create_issue_missing_project(self):
        """Test create_issue with missing project."""
        # Act
        result = self.basic_ops.create_issue("", "Summary")
        result_data = json.loads(result)
        
        # Assert
        assert result_data["error"] == "Project is required"
        assert result_data["status"] == "error"

    def test_create_issue_missing_summary(self):
        """Test create_issue with missing summary."""
        # Act
        result = self.basic_ops.create_issue("DEMO", "")
        result_data = json.loads(result)
        
        # Assert
        assert result_data["error"] == "Summary is required"
        assert result_data["status"] == "error"

    def test_create_issue_project_not_found(self):
        """Test create_issue when project is not found."""
        # Arrange
        project = "NONEXISTENT"
        self.mock_projects_api.get_project_by_name.return_value = None
        
        # Act
        result = self.basic_ops.create_issue(project, "Summary")
        result_data = json.loads(result)
        
        # Assert
        assert f"Project not found: {project}" in result_data["error"]
        assert result_data["status"] == "error"

    def test_create_issue_project_lookup_error(self):
        """Test create_issue when project lookup fails."""
        # Arrange
        project = "DEMO"
        self.mock_projects_api.get_project_by_name.side_effect = Exception("Database error")
        
        # Act
        result = self.basic_ops.create_issue(project, "Summary")
        result_data = json.loads(result)
        
        # Assert
        assert "Error finding project" in result_data["error"]
        assert "Database error" in result_data["error"]

    def test_create_issue_api_error(self):
        """Test create_issue when API creation fails."""
        # Arrange
        project = "0-1"
        summary = "Test issue"
        
        self.mock_issues_api.create_issue.side_effect = Exception("Creation failed")
        
        # Act
        result = self.basic_ops.create_issue(project, summary)
        result_data = json.loads(result)
        
        # Assert
        assert "Creation failed" in result_data["error"]
        assert result_data["status"] == "error"

    def test_create_issue_with_detailed_retrieval(self):
        """Test create_issue retrieves detailed issue after creation."""
        # Arrange
        project = "DEMO"
        summary = "Test issue"
        
        # Mock project lookup
        mock_project = Mock()
        mock_project.id = "0-1"
        self.mock_projects_api.get_project_by_name.return_value = mock_project
        
        # Mock issue creation with ID
        mock_created_issue = Mock()
        mock_created_issue.id = "3-123"
        self.mock_issues_api.create_issue.return_value = mock_created_issue
        
        # Mock detailed issue retrieval
        mock_detailed_issue = Mock()
        mock_detailed_issue.model_dump.return_value = {
            "id": "3-123",
            "summary": summary,
            "detailed_field": "extra_data"
        }
        self.mock_issues_api.get_issue.return_value = mock_detailed_issue
        
        # Act
        result = self.basic_ops.create_issue(project, summary)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["id"] == "3-123"
        assert result_data["detailed_field"] == "extra_data"
        
        # Verify detailed retrieval was called
        self.mock_issues_api.get_issue.assert_called_once_with("3-123")

    def test_update_issue_success(self):
        """Test successful issue update."""
        # Arrange
        issue_id = "DEMO-123"
        new_summary = "Updated summary"
        new_description = "Updated description"
        additional_fields = {"priority": "High"}
        
        mock_updated_issue = Mock()
        mock_updated_issue.model_dump.return_value = {
            "id": "3-123",
            "summary": new_summary,
            "description": new_description
        }
        
        self.mock_issues_api.update_issue.return_value = mock_updated_issue
        
        # Act
        result = self.basic_ops.update_issue(
            issue_id=issue_id,
            summary=new_summary,
            description=new_description,
            additional_fields=additional_fields
        )
        result_data = json.loads(result)
        
        # Assert
        assert result_data["id"] == "3-123"
        assert result_data["summary"] == new_summary
        assert result_data["description"] == new_description
        
        # Verify API call
        self.mock_issues_api.update_issue.assert_called_once_with(
            issue_id=issue_id,
            summary=new_summary,
            description=new_description,
            additional_fields=additional_fields
        )

    def test_update_issue_with_dict_response(self):
        """Test update_issue with __dict__ response instead of model_dump."""
        # Arrange
        issue_id = "DEMO-123"
        new_summary = "Updated summary"
        
        # Create a simple object without model_dump method
        class SimpleObject:
            def __init__(self):
                self.id = "3-123"
                self.summary = new_summary
        
        mock_updated_issue = SimpleObject()
        
        self.mock_issues_api.update_issue.return_value = mock_updated_issue
        
        # Act
        result = self.basic_ops.update_issue(issue_id=issue_id, summary=new_summary)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["id"] == "3-123"
        assert result_data["summary"] == new_summary

    def test_update_issue_api_error(self):
        """Test update_issue when API call fails."""
        # Arrange
        issue_id = "DEMO-123"
        self.mock_issues_api.update_issue.side_effect = Exception("Update failed")
        
        # Act
        result = self.basic_ops.update_issue(issue_id=issue_id, summary="New summary")
        result_data = json.loads(result)
        
        # Assert
        assert "Update failed" in result_data["error"]
        assert result_data["status"] == "error"

    def test_add_comment_success(self):
        """Test successful comment addition."""
        # Arrange
        issue_id = "DEMO-123"
        comment_text = "This is a test comment"
        
        mock_comment_result = {
            "id": "comment-123",
            "text": comment_text,
            "author": {"login": "admin"},
            "created": 1234567890
        }
        
        self.mock_issues_api.add_comment.return_value = mock_comment_result
        
        # Act
        result = self.basic_ops.add_comment(issue_id, comment_text)
        result_data = json.loads(result)
        
        # Assert - verify key fields (format_json_response may add ISO dates)
        assert result_data["id"] == mock_comment_result["id"]
        assert result_data["text"] == mock_comment_result["text"] 
        assert result_data["author"] == mock_comment_result["author"]
        
        # Verify API call
        self.mock_issues_api.add_comment.assert_called_once_with(issue_id, comment_text)

    def test_add_comment_api_error(self):
        """Test add_comment when API call fails."""
        # Arrange
        issue_id = "DEMO-123"
        comment_text = "Test comment"
        
        self.mock_issues_api.add_comment.side_effect = Exception("Comment failed")
        
        # Act
        result = self.basic_ops.add_comment(issue_id, comment_text)
        result_data = json.loads(result)
        
        # Assert
        assert "Comment failed" in result_data["error"]

    def test_get_tool_definitions(self):
        """Test tool definitions for basic operation functions."""
        # Act
        definitions = self.basic_ops.get_tool_definitions()
        
        # Assert
        expected_functions = [
            "get_issue",
            "search_issues",
            "create_issue",
            "update_issue",
            "add_comment"
        ]
        
        for func_name in expected_functions:
            assert func_name in definitions
            assert "description" in definitions[func_name]
            assert "parameter_descriptions" in definitions[func_name]
        
        # Check specific parameter descriptions
        get_issue_def = definitions["get_issue"]
        assert "issue_id" in get_issue_def["parameter_descriptions"]
        
        search_def = definitions["search_issues"]
        assert "query" in search_def["parameter_descriptions"]
        assert "limit" in search_def["parameter_descriptions"]
        
        create_def = definitions["create_issue"]
        assert "project" in create_def["parameter_descriptions"]
        assert "summary" in create_def["parameter_descriptions"]
        assert "description" in create_def["parameter_descriptions"]
        
        update_def = definitions["update_issue"]
        assert "issue_id" in update_def["parameter_descriptions"]
        assert "summary" in update_def["parameter_descriptions"]
        assert "description" in update_def["parameter_descriptions"]
        assert "additional_fields" in update_def["parameter_descriptions"]
        
        comment_def = definitions["add_comment"]
        assert "issue_id" in comment_def["parameter_descriptions"]
        assert "text" in comment_def["parameter_descriptions"]

    def test_create_issue_error_response_from_api(self):
        """Test create_issue when API returns error as dict."""
        # Arrange
        project = "0-1"
        summary = "Test issue"
        
        error_response = {"error": "Insufficient permissions", "status": "error"}
        self.mock_issues_api.create_issue.return_value = error_response
        
        # Act
        result = self.basic_ops.create_issue(project, summary)
        result_data = json.loads(result)
        
        # Assert
        assert result_data["error"] == "Insufficient permissions"
        assert result_data["status"] == "error"

    def test_create_issue_with_response_error_details(self):
        """Test create_issue with detailed error response."""
        # Arrange
        project = "0-1"
        summary = "Test issue"
        
        # Mock exception with response attribute
        mock_exception = Exception("API Error")
        mock_response = Mock()
        mock_response.content = b'{"error": "Detailed error message"}'
        mock_exception.response = mock_response
        
        self.mock_issues_api.create_issue.side_effect = mock_exception
        
        # Act
        result = self.basic_ops.create_issue(project, summary)
        result_data = json.loads(result)
        
        # Assert
        assert "API Error" in result_data["error"]
        assert "Detailed error message" in result_data["error"] 