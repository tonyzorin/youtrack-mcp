#!/bin/bash

# Script to comment on PR #13
# Usage: ./comment_on_pr.sh [GITHUB_TOKEN]

if [ -z "$1" ] && [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GitHub token required"
    echo "Usage: ./comment_on_pr.sh [GITHUB_TOKEN]"
    echo "Or set GITHUB_TOKEN environment variable"
    exit 1
fi

TOKEN=${1:-$GITHUB_TOKEN}

# Read the comment content and escape it for JSON
COMMENT_BODY=$(cat PR_13_COMMENT.md | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')

# Create the comment
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $TOKEN" \
  -H "User-Agent: YouTrack-MCP-Bot" \
  https://api.github.com/repos/tonyzorin/youtrack-mcp/issues/13/comments \
  -d "{\"body\":\"$COMMENT_BODY\"}"

echo ""
echo "Comment posted to PR #13" 