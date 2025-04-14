#!/usr/bin/env python
"""
Example script demonstrating the use of YouTrack MCP User tools.

This script shows how to use the YouTrack MCP server to:
1. Get the current authenticated user
2. Search for users
3. Get detailed information about a specific user
4. Get a user by login name
5. Retrieve user groups

Run this script with a valid YouTrack API token:
    YOUTRACK_API_TOKEN=your_token python user_tools_example.py
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtrack_mcp.tools.users import UserTools

# Load environment variables from .env file if it exists
load_dotenv()

# Check if YouTrack token is set
if not os.getenv("YOUTRACK_API_TOKEN"):
    print("Error: YOUTRACK_API_TOKEN environment variable is not set.")
    print("Please set it with your YouTrack API token.")
    print("Example: YOUTRACK_API_TOKEN=your_token python user_tools_example.py")
    sys.exit(1)

def pretty_print(obj):
    """Pretty print JSON objects."""
    print(json.dumps(obj, indent=2))

def main():
    """Run the example script."""
    print("YouTrack MCP User Tools Example")
    print("==============================\n")
    
    # Initialize the UserTools instance
    user_tools = UserTools()
    
    try:
        # 1. Get the current authenticated user
        print("\n1. Getting current authenticated user...")
        current_user = user_tools.get_current_user("dummy")
        pretty_print(current_user)
        
        # Save the user ID for later use
        user_id = current_user.get("id")
        
        # 2. Search for users
        print("\n2. Searching for users...")
        search_query = "admin"  # Search for users with "admin" in their name or email
        users = user_tools.search_users(query=search_query, limit=5)
        pretty_print(users)
        
        # 3. Get detailed information about a specific user
        if user_id:
            print(f"\n3. Getting detailed information for user with ID {user_id}...")
            user_details = user_tools.get_user(issue_id=user_id)
            pretty_print(user_details)
        
        # 4. Get a user by login name
        if current_user.get("login"):
            login = current_user.get("login")
            print(f"\n4. Getting user by login name '{login}'...")
            user_by_login = user_tools.get_user_by_login(login=login)
            pretty_print(user_by_login)
        
        # 5. Get user groups
        if user_id:
            print(f"\n5. Getting groups for user with ID {user_id}...")
            user_groups = user_tools.get_user_groups(user_id=user_id)
            pretty_print(user_groups)
            
        print("\nAll examples completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up by closing the client
        user_tools.close()

if __name__ == "__main__":
    main() 