#!/usr/bin/env python3
"""
Test script to verify MCP functionality in Docker container.
This simulates what Claude Desktop would do.
"""
import subprocess
import json
import sys

def test_mcp_docker():
    """Test the MCP server in Docker container."""
    
    print("🐳 Testing YouTrack MCP in Docker container...")
    
    # Docker command to run the MCP server
    docker_cmd = [
        "docker", "run", "--rm", "-i",
        "--env", "YOUTRACK_URL=https://prodcamp.youtrack.cloud/",
        "--env", "YOUTRACK_API_TOKEN=perm-YWRtaW4=.NDMtMg==.JgbpvnDbEu7RSWwAJT6Ab3iXgQyPwu",
        "youtrack-mcp-local:0.3.7-wip"
    ]
    
    print(f"Running: {' '.join(docker_cmd)}")
    
    try:
        # Start the Docker container with MCP server
        process = subprocess.Popen(
            docker_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # Send MCP initialization request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {
                        "listChanged": True
                    },
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("📤 Sending initialization request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            print("📥 Received response:")
            try:
                response = json.loads(response_line.strip())
                print(json.dumps(response, indent=2))
                
                # Check if our attachment tool is available
                if 'result' in response and 'capabilities' in response['result']:
                    capabilities = response['result']['capabilities']
                    if 'tools' in capabilities:
                        print("✅ MCP server initialized successfully!")
                        print("🔧 Tools capability confirmed")
                    else:
                        print("⚠️  No tools capability found")
                else:
                    print("⚠️  Unexpected response format")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse JSON response: {e}")
                print(f"Raw response: {response_line}")
        else:
            print("❌ No response received")
            
        # Send tools list request
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        print("\n📤 Requesting tools list...")
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()
        
        # Read tools response
        tools_response_line = process.stdout.readline()
        if tools_response_line:
            print("📥 Tools response:")
            try:
                tools_response = json.loads(tools_response_line.strip())
                if 'result' in tools_response and 'tools' in tools_response['result']:
                    tools = tools_response['result']['tools']
                    print(f"✅ Found {len(tools)} tools")
                    
                    # Look for our attachment tool
                    attachment_tool = None
                    for tool in tools:
                        if tool.get('name') == 'get_attachment_content':
                            attachment_tool = tool
                            break
                    
                    if attachment_tool:
                        print("🎉 Found get_attachment_content tool!")
                        print(f"   Description: {attachment_tool.get('description', 'N/A')}")
                        if 'inputSchema' in attachment_tool:
                            props = attachment_tool['inputSchema'].get('properties', {})
                            print(f"   Parameters: {list(props.keys())}")
                    else:
                        print("❌ get_attachment_content tool not found")
                        print("Available tools:", [t.get('name') for t in tools[:5]])
                else:
                    print("❌ No tools in response")
                    print(json.dumps(tools_response, indent=2))
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse tools response: {e}")
        
        # Cleanup
        process.stdin.close()
        process.wait(timeout=5)
        
    except subprocess.TimeoutExpired:
        print("⚠️  Process timed out")
        process.kill()
    except Exception as e:
        print(f"❌ Error: {e}")
        
    print("\n🏁 Test completed!")

if __name__ == "__main__":
    test_mcp_docker() 