#!/bin/bash
# Build and run the YouTrack MCP container to test tool prioritization

echo "Building the Docker image..."
docker build -t youtrack-mcp-test .

echo -e "\nCreating a test script to check tool prioritization..."
cat > test_priority.py << 'EOF'
"""
Test script to verify tool prioritization.
This script bypasses client initialization to allow testing without credentials.
"""
import sys
import logging
import importlib

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Mock the necessary components to avoid client initialization
def patch_module():
    """
    Patch module imports to prevent client initialization.
    This allows the loader to work without actual YouTrack credentials.
    """
    # First, we need to override the client initialization
    import youtrack_mcp.api.client
    
    # Create a mock client class that doesn't need to connect
    class MockYouTrackClient:
        def __init__(self, base_url=None, token=None, verify_ssl=True):
            self.base_url = "https://example.youtrack.cloud"
            self.token = "mock-token"
            self.verify_ssl = verify_ssl
            
        def get(self, endpoint, params=None):
            return {}
            
        def post(self, endpoint, data=None, json_data=None):
            return {}
            
        def close(self):
            pass
            
    # Replace the real client with our mock
    youtrack_mcp.api.client.YouTrackClient = MockYouTrackClient

# Apply the patches
patch_module()

# Now import the loader and load tools
from youtrack_mcp.tools.loader import load_all_tools

print("\nTesting YouTrack MCP tool prioritization...\n")

# Load all tools
all_tools = load_all_tools()

# List of tools we are particularly interested in
focus_tools = [
    'get_issue', 
    'get_project', 
    'get_project_issues', 
    'get_user',
    'get_all_issues',
    'get_all_projects',
    'get_all_users',
    'get_issue_comments',
    'search_issues'
]

# Print results 
print(f'Total tools loaded: {len(all_tools)}')
print('\nTools of interest:')
print('-' * 80)
print(f"{'Tool Name':<25} {'Module':<55}")
print('-' * 80)

for tool_name in focus_tools:
    if tool_name in all_tools:
        tool = all_tools[tool_name]
        # Get the module name to verify which implementation was chosen
        func_module = getattr(tool, '__module__', 'Unknown')
        print(f"{tool_name:<25} {func_module:<55}")
    else:
        print(f"{tool_name:<25} {'NOT FOUND':<55}")

print('-' * 80)
EOF

echo -e "\nRunning tests in Docker container..."
docker run --rm -e YOUTRACK_URL="https://example.youtrack.cloud" -e YOUTRACK_API_TOKEN="dummy-token" youtrack-mcp-test python3 test_priority.py 