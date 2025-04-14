"""
Tests for the YouTrack MCP server.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from youtrack_mcp.server import YouTrackMCPServer


@patch('youtrack_mcp.server.FastMCP')
def test_server_initialization(MockFastMCP):
    """Test that server initializes correctly."""
    # Create a mock instance to return
    mock_instance = MagicMock()
    MockFastMCP.return_value = mock_instance
    
    # Create a server instance
    server = YouTrackMCPServer()
    
    # Verify that the FastMCP was created
    MockFastMCP.assert_called_once()
    
    # Check that tools registry is initialized
    assert server._tools == {}


@patch('youtrack_mcp.server.FastMCP')
def test_register_tool(MockFastMCP):
    """Test that tools can be registered correctly."""
    # Create a mock instance to return
    mock_instance = MagicMock()
    MockFastMCP.return_value = mock_instance
    
    # Create a server instance
    server = YouTrackMCPServer()
    
    # Define a dummy tool function
    def dummy_tool(param1, param2):
        return f"{param1} {param2}"
    
    # Register the tool
    server.register_tool(
        name="dummy_tool",
        func=dummy_tool,
        description="A dummy tool for testing",
        parameter_descriptions={
            "param1": "First parameter",
            "param2": "Second parameter"
        }
    )
    
    # Verify tool is registered in the server's registry
    assert "dummy_tool" in server._tools
    assert server._tools["dummy_tool"] == dummy_tool
    
    # Verify tool is registered with the MCP server
    mock_instance.add_tool.assert_called_once_with(
        fn=dummy_tool,
        name="dummy_tool", 
        description="A dummy tool for testing"
    )


@patch('youtrack_mcp.server.FastMCP')
def test_register_tools(MockFastMCP):
    """Test that multiple tools can be registered at once."""
    # Create a mock instance to return
    mock_instance = MagicMock()
    MockFastMCP.return_value = mock_instance
    
    # Create a server instance
    server = YouTrackMCPServer()
    
    # Define dummy tool functions
    def tool1(): pass
    def tool2(): pass
    
    # Define tools configuration
    tools = {
        "tool1": {
            "function": tool1,
            "description": "Tool 1",
            "parameter_descriptions": {}
        },
        "tool2": {
            "function": tool2,
            "description": "Tool 2",
            "parameter_descriptions": {}
        }
    }
    
    # Register multiple tools
    server.register_tools(tools)
    
    # Verify tools are registered in the server's registry
    assert "tool1" in server._tools
    assert "tool2" in server._tools
    
    # Verify tools are registered with the MCP server
    assert mock_instance.add_tool.call_count == 2


@patch('youtrack_mcp.server.FastMCP')
def test_server_run_stop(MockFastMCP):
    """Test server run and stop methods."""
    # Create a mock instance to return with no real run method
    mock_instance = MagicMock()
    MockFastMCP.return_value = mock_instance
    
    # Create a server instance
    server = YouTrackMCPServer()
    
    # Run the server (but patch the actual run method to do nothing)
    with patch.object(server.server, 'run'):
        server.run()
        server.server.run.assert_called_once()
    
    # Stop the server - note: stop() doesn't actually call anything on the server instance
    server.stop() 