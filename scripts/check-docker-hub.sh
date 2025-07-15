#!/bin/bash

echo "🔍 Docker Hub Repository Checker"
echo "================================"

REPO_NAME="tonyzorin/youtrack-mcp"

echo "Checking Docker Hub repository: $REPO_NAME"
echo ""

# Check if repository exists by trying to pull a tag
echo "1. Testing repository accessibility..."
if curl -s -f https://hub.docker.com/v2/repositories/$REPO_NAME/ > /dev/null; then
    echo "✅ Repository $REPO_NAME exists on Docker Hub"
    
    # Get repository info
    echo ""
    echo "2. Repository information:"
    curl -s https://hub.docker.com/v2/repositories/$REPO_NAME/ | jq -r '. | "Name: \(.name)\nStatus: \(.status)\nIs Private: \(.is_private)\nPull Count: \(.pull_count)"' 2>/dev/null || echo "Repository found (jq not available for details)"
    
    echo ""
    echo "3. Existing tags:"
    curl -s https://hub.docker.com/v2/repositories/$REPO_NAME/tags/ | jq -r '.results[].name' 2>/dev/null | head -10 || echo "Tags available (jq not available for details)"
    
else
    echo "❌ Repository $REPO_NAME does not exist or is not accessible"
    echo ""
    echo "🔧 To fix this:"
    echo "1. Go to https://hub.docker.com"
    echo "2. Sign in with your Docker Hub account"
    echo "3. Click 'Create Repository'"
    echo "4. Repository name: youtrack-mcp"
    echo "5. Namespace: tonyzorin"
    echo "6. Make sure it's set to Public (or Private if you have a paid plan)"
fi

echo ""
echo "4. Testing Docker Hub connectivity..."
if docker pull hello-world:latest > /dev/null 2>&1; then
    echo "✅ Docker Hub connectivity is working"
else
    echo "❌ Docker Hub connectivity issues detected"
fi

echo ""
echo "5. Checking if you're logged into Docker Hub locally..."
if docker info | grep -q "Username:"; then
    USERNAME=$(docker info | grep "Username:" | awk '{print $2}')
    echo "✅ Logged in as: $USERNAME"
    
    # Test push permissions
    echo ""
    echo "6. Testing push permissions..."
    echo "Creating a test image..."
    echo "FROM alpine:latest" | docker build -t test-push-permissions - > /dev/null 2>&1
    docker tag test-push-permissions $REPO_NAME:test-permissions
    
    if docker push $REPO_NAME:test-permissions > /dev/null 2>&1; then
        echo "✅ Push permissions verified"
        echo "Cleaning up test image..."
        docker rmi $REPO_NAME:test-permissions test-push-permissions > /dev/null 2>&1
    else
        echo "❌ Push permissions failed"
        echo "Make sure you have push access to $REPO_NAME"
        docker rmi test-push-permissions > /dev/null 2>&1
    fi
else
    echo "ℹ️  Not logged into Docker Hub locally"
    echo "To test push permissions, run: docker login"
fi

echo ""
echo "🔧 GitHub Actions Setup Checklist:"
echo "=================================="
echo ""
echo "Repository Settings → Secrets and variables → Actions:"
echo ""
echo "DOCKER_USERNAME (required):"
echo "  └── Should be: tonyzorin"
echo ""
echo "DOCKER_PASSWORD (required):"
echo "  └── Should be: Your Docker Hub access token"
echo "  └── Create at: https://hub.docker.com/settings/security"
echo "  └── Permissions: Read, Write, Delete"
echo ""
echo "Repository: $REPO_NAME"
echo "  └── Must exist and be accessible"
echo "  └── You must have push permissions"

echo ""
echo "🚀 Next Steps:"
echo "=============="
echo "1. Ensure Docker Hub repository exists"
echo "2. Set up GitHub Actions secrets"
echo "3. Push another commit to trigger the workflow"
echo "4. Check the workflow logs for the improved diagnostics" 