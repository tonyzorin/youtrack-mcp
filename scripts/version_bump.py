#!/usr/bin/env python3
"""
Version management script for YouTrack MCP.
Helps with version bumping and proper tagging.
"""
import os
import sys
import subprocess
import re
from pathlib import Path

def get_current_version():
    """Get the current version from version.py"""
    version_file = Path(__file__).parent.parent / "youtrack_mcp" / "version.py"
    with open(version_file, 'r') as f:
        content = f.read()
        match = re.search(r'__version__ = "([^"]+)"', content)
        if match:
            return match.group(1)
    raise ValueError("Could not find version in version.py")

def update_version(new_version):
    """Update the version in version.py"""
    version_file = Path(__file__).parent.parent / "youtrack_mcp" / "version.py"
    with open(version_file, 'r') as f:
        content = f.read()
    
    new_content = re.sub(
        r'__version__ = "[^"]+"',
        f'__version__ = "{new_version}"',
        content
    )
    
    with open(version_file, 'w') as f:
        f.write(new_content)
    
    print(f"Updated version to {new_version}")

def bump_version(version, bump_type):
    """Bump version based on type (major, minor, patch)"""
    parts = list(map(int, version.split('.')))
    
    if bump_type == 'major':
        parts[0] += 1
        parts[1] = 0
        parts[2] = 0
    elif bump_type == 'minor':
        parts[1] += 1
        parts[2] = 0
    elif bump_type == 'patch':
        parts[2] += 1
    else:
        raise ValueError("bump_type must be 'major', 'minor', or 'patch'")
    
    return '.'.join(map(str, parts))

def run_command(cmd, check=True):
    """Run a shell command"""
    print(f"Running: {cmd}")
    if check:
        subprocess.run(cmd, shell=True, check=True)
    else:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: python version_bump.py <bump_type|version> [--dry-run]")
        print("  bump_type: major, minor, patch")
        print("  version: specific version like 1.0.0")
        print("  --dry-run: Only calculate the new version, don't make changes")
        print("Examples:")
        print("  python version_bump.py patch    # 1.0.0 -> 1.0.1")
        print("  python version_bump.py minor    # 1.0.0 -> 1.1.0")
        print("  python version_bump.py major    # 1.0.0 -> 2.0.0")
        print("  python version_bump.py 1.1.0    # Set to specific version")
        print("  python version_bump.py patch --dry-run  # Just show what would happen")
        sys.exit(1)
    
    arg = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    
    current_version = get_current_version()
    
    # Determine new version
    if arg in ['major', 'minor', 'patch']:
        new_version = bump_version(current_version, arg)
    else:
        # Assume it's a specific version
        new_version = arg
    
    if dry_run:
        # For dry run, just print the new version and exit
        print(new_version)
        return
    
    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")
    
    # Check if working directory is clean
    result = run_command("git status --porcelain", check=False)
    if result.stdout.strip():
        print("Warning: Working directory has uncommitted changes.")
        print("Commit your changes first, then run this script.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Update version
    update_version(new_version)
    
    # Commit version change
    run_command(f'git add youtrack_mcp/version.py')
    run_command(f'git commit -m "Bump version to {new_version}"')
    
    # Create tag
    run_command(f'git tag -a v{new_version} -m "Release version {new_version}"')
    
    print(f"\nVersion bumped to {new_version}")
    print("Next steps:")
    print("1. Push changes: git push origin main")
    print("2. Push tags: git push origin --tags")
    print("3. Create GitHub release to trigger Docker build with 'latest' tag")
    print(f"4. Or just push to main for WIP build: {new_version}_wip")

if __name__ == "__main__":
    main() 