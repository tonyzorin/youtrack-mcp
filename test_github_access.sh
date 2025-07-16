#!/bin/bash

# Test GitHub token permissions
# Usage: ./test_github_access.sh YOUR_GITHUB_TOKEN

if [ -z "$1" ]; then
    echo "Usage: ./test_github_access.sh YOUR_GITHUB_TOKEN"
    exit 1
fi

TOKEN=$1

echo "Testing GitHub token permissions..."
echo "======================================"

# Test user access
echo "1. Testing user access:"
curl -s -H "Authorization: token $TOKEN" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/user | jq '.login // .message'

# Test repo access
echo "2. Testing repository access:"
curl -s -H "Authorization: token $TOKEN" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/repos/tonyzorin/youtrack-mcp | jq '.name // .message'

# Test comment permissions (dry run)
echo "3. Testing comment permissions:"
curl -s -X POST \
     -H "Authorization: token $TOKEN" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/repos/tonyzorin/youtrack-mcp/issues/13/comments \
     -d '{"body":"[TEST] Checking permissions - please ignore"}' | jq '.id // .message'

echo "======================================"
echo "If you see numbers above (not error messages), the token works!"
echo "If you see 'Resource not accessible', the token needs more permissions." 