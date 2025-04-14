#!/usr/bin/env python
"""
Setup Environment Script

This script helps users set up their .env file for the YouTrack MCP server.
It guides users through the process and ensures no sensitive tokens are committed to version control.
"""

import os
import sys
import shutil
from pathlib import Path

def create_env_file():
    """Create a new .env file based on the .env.example template."""
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # Check if .env.example exists
    example_path = project_root / ".env.example"
    if not example_path.exists():
        print("Error: .env.example file not found.")
        sys.exit(1)
    
    # Check if .env already exists
    env_path = project_root / ".env"
    if env_path.exists():
        overwrite = input(".env file already exists. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("Setup cancelled.")
            return
    
    # Create a backup of existing .env if it exists
    if env_path.exists():
        backup_path = project_root / ".env.backup"
        shutil.copy(env_path, backup_path)
        print(f"Created backup of existing .env file as {backup_path}")
    
    # Copy the example file to create a new .env file
    shutil.copy(example_path, env_path)
    
    # Read the template
    with open(env_path, 'r') as f:
        template = f.read()
    
    # Gather information from the user
    print("\n=== YouTrack MCP Server Environment Setup ===\n")
    print("Please provide your YouTrack information:")
    
    # YouTrack Cloud or self-hosted
    is_cloud = input("Are you using YouTrack Cloud? (y/n): ").lower() == 'y'
    
    if is_cloud:
        url = input("YouTrack Cloud URL (e.g., https://yourorg.youtrack.cloud): ")
    else:
        url = input("YouTrack URL (e.g., https://example.myjetbrains.com/youtrack): ")
    
    # Get API token
    print("\nIMPORTANT: API tokens are sensitive credentials.")
    print("This token will be stored in your .env file, which should NEVER be committed to version control.")
    print("Make sure .env is included in your .gitignore file.")
    api_token = input("\nYouTrack API token (starting with 'perm:'): ")
    
    # Verify SSL
    verify_ssl = input("\nVerify SSL certificates? (y/n, default: y): ")
    verify_ssl = verify_ssl.lower() != 'n'
    
    # Update the template with user-provided values
    template = template.replace("YOUTRACK_URL=https://your-workspace.youtrack.cloud", f"YOUTRACK_URL={url}")
    
    # Add YOUTRACK_CLOUD line if it doesn't exist
    if "YOUTRACK_CLOUD" not in template:
        cloud_line = f"YOUTRACK_CLOUD={'true' if is_cloud else 'false'}"
        # Insert after URL line
        template = template.replace("YOUTRACK_URL=", f"YOUTRACK_URL=\n{cloud_line}\n# ")
    else:
        template = template.replace("# YOUTRACK_CLOUD=true", f"YOUTRACK_CLOUD={'true' if is_cloud else 'false'}")
    
    template = template.replace("YOUTRACK_API_TOKEN=perm:your-permanent-token-here", f"YOUTRACK_API_TOKEN={api_token}")
    
    # Add VERIFY_SSL line if it doesn't exist
    if "YOUTRACK_VERIFY_SSL" not in template:
        ssl_line = f"YOUTRACK_VERIFY_SSL={'true' if verify_ssl else 'false'}"
        # Insert after API token line
        template = template.replace("YOUTRACK_API_TOKEN=", f"YOUTRACK_API_TOKEN=\n{ssl_line}\n\n# ")
    else:
        template = template.replace("YOUTRACK_VERIFY_SSL=true", f"YOUTRACK_VERIFY_SSL={'true' if verify_ssl else 'false'}")
    
    # Write the updated content back to the .env file
    with open(env_path, 'w') as f:
        f.write(template)
    
    print("\n=== Environment Setup Complete ===")
    print(f".env file created at {env_path}")
    print("\nSECURITY REMINDER:")
    print("1. NEVER commit your .env file to version control")
    print("2. Make sure .env is listed in your .gitignore file")
    print("3. Keep your API token secure and rotate it periodically")
    print("\nYou can now run the YouTrack MCP server.")

if __name__ == "__main__":
    create_env_file() 