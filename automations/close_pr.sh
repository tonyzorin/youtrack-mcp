#!/bin/bash

# Script to close PR #13
# Usage: ./close_pr.sh [GITHUB_TOKEN]

if [ -z "$1" ] && [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GitHub token required"
    echo "Usage: ./close_pr.sh [GITHUB_TOKEN]"
    echo "Or set GITHUB_TOKEN environment variable"
    exit 1
fi

TOKEN=${1:-$GITHUB_TOKEN}

# Close the PR
curl -X PATCH \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $TOKEN" \
  -H "User-Agent: YouTrack-MCP-Bot" \
  https://api.github.com/repos/tonyzorin/youtrack-mcp/pulls/13 \
  -d '{"state":"closed"}'

echo ""
echo "PR #13 has been closed" 