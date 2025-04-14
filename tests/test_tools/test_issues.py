"""
Tests for issue-related MCP tools.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from youtrack_mcp.api.issues import Issue
from youtrack_mcp.tools.issues import IssueTools


def test_get_issue_tool_success(mock_issue_tools, mock_issue_data):
    """Test get_issue tool returns proper JSON when successful."""
    # Mock the client get method directly to return a dictionary instead of a MagicMock
    mock_issue_tools.client.get.return_value = mock_issue_data
    
    # Call the tool
    result = mock_issue_tools.get_issue("TEST-1")
    
    # Verify the result
    assert mock_issue_tools.client.get.called
    
    # Parse the JSON result and check it matches expected data
    result_data = json.loads(result)
    assert result_data["id"] == mock_issue_data["id"]
    assert result_data["summary"] == mock_issue_data["summary"]


def test_get_issue_tool_error(mock_issue_tools):
    """Test get_issue tool returns error JSON when exception occurs."""
    # Mock client to raise an exception
    mock_issue_tools.client.get.side_effect = Exception("Test error")
    
    # Call the tool
    result = mock_issue_tools.get_issue("TEST-1")
    
    # Parse the JSON result and check it contains error message
    result_data = json.loads(result)
    assert "error" in result_data
    assert "Test error" in result_data["error"]


def test_search_issues_tool_success(mock_issue_tools, mock_issues_list):
    """Test search_issues tool returns proper JSON when successful."""
    # Mock the client get method directly to return a list of dictionaries
    mock_issue_tools.client.get.return_value = mock_issues_list
    
    # Call the tool
    result = mock_issue_tools.search_issues("project: TEST")
    
    # Verify the result
    assert mock_issue_tools.client.get.called
    
    # Parse the JSON result and check it matches expected data
    result_data = json.loads(result)
    assert isinstance(result_data, list)
    assert len(result_data) == len(mock_issues_list)
    assert result_data[0]["id"] == mock_issues_list[0]["id"]
    assert result_data[1]["id"] == mock_issues_list[1]["id"]


def test_search_issues_tool_error(mock_issue_tools):
    """Test search_issues tool returns error JSON when exception occurs."""
    # Mock client to raise an exception
    mock_issue_tools.client.get.side_effect = Exception("Test error")
    
    # Call the tool
    result = mock_issue_tools.search_issues("project: TEST")
    
    # Parse the JSON result and check it contains error message
    result_data = json.loads(result)
    assert "error" in result_data
    assert "Test error" in result_data["error"]


def test_create_issue_tool_success(mock_issue_tools, mock_issue_data):
    """Test create_issue tool returns proper JSON when successful."""
    # Prepare a proper serializable response
    mock_issue = Issue.model_validate(mock_issue_data)
    # Configure the mock to return a dictionary from model_dump() instead of the mock itself
    mock_issue_tools.issues_api.create_issue.return_value = mock_issue
    
    # Call the tool
    result = mock_issue_tools.create_issue("0-1", "Test Issue", "This is a test issue")
    
    # Verify the result
    assert mock_issue_tools.issues_api.create_issue.called
    create_args = mock_issue_tools.issues_api.create_issue.call_args
    assert create_args[0][0] == "0-1"  # project_id
    assert create_args[0][1] == "Test Issue"  # summary
    assert create_args[0][2] == "This is a test issue"  # description
    
    # Parse the JSON result and check it matches expected data
    result_data = json.loads(result)
    assert result_data["id"] == mock_issue_data["id"]
    assert result_data["summary"] == mock_issue_data["summary"]


def test_create_issue_tool_error(mock_issue_tools):
    """Test create_issue tool returns error JSON when exception occurs."""
    # Mock issue API to raise an exception
    mock_issue_tools.issues_api.create_issue.side_effect = Exception("Test error")
    
    # Call the tool
    result = mock_issue_tools.create_issue("0-1", "Test Issue", "This is a test issue")
    
    # Parse the JSON result and check it contains error message
    result_data = json.loads(result)
    assert "error" in result_data
    assert "Test error" in result_data["error"]


def test_add_comment_tool_success(mock_issue_tools):
    """Test add_comment tool returns proper JSON when successful."""
    # Mock issue API to return a dummy comment result (dictionary instead of MagicMock)
    mock_comment_result = {"id": "comment-1", "text": "Test comment"}
    mock_issue_tools.issues_api.add_comment.return_value = mock_comment_result
    
    # Call the tool
    result = mock_issue_tools.add_comment("TEST-1", "Test comment")
    
    # Verify the result
    assert mock_issue_tools.issues_api.add_comment.called
    add_comment_args = mock_issue_tools.issues_api.add_comment.call_args
    assert add_comment_args[0][0] == "TEST-1"  # issue_id
    assert add_comment_args[0][1] == "Test comment"  # text
    
    # Parse the JSON result and check it matches expected data
    result_data = json.loads(result)
    assert result_data["id"] == mock_comment_result["id"]
    assert result_data["text"] == mock_comment_result["text"]


def test_add_comment_tool_error(mock_issue_tools):
    """Test add_comment tool returns error JSON when exception occurs."""
    # Mock issue API to raise an exception
    mock_issue_tools.issues_api.add_comment.side_effect = Exception("Test error")
    
    # Call the tool
    result = mock_issue_tools.add_comment("TEST-1", "Test comment")
    
    # Parse the JSON result and check it contains error message
    result_data = json.loads(result)
    assert "error" in result_data
    assert "Test error" in result_data["error"]


def test_get_tool_definitions(mock_issue_tools):
    """Test that get_tool_definitions returns the expected tools."""
    tool_defs = mock_issue_tools.get_tool_definitions()
    
    # Check that all expected tools are defined
    assert "get_issue" in tool_defs
    assert "search_issues" in tool_defs
    assert "create_issue" in tool_defs
    assert "add_comment" in tool_defs
    
    # Check that each tool has required attributes
    for tool_name, tool_def in tool_defs.items():
        assert "function" in tool_def
        assert "description" in tool_def
        assert "parameter_descriptions" in tool_def 