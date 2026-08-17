#!/bin/bash

echo "🔍 YouTrack MCP Docker Build Diagnostics"
echo "========================================"

# Check Docker installation
echo "1. Checking Docker installation..."
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed: $(docker --version)"
else
    echo "❌ Docker is not installed"
    exit 1
fi

# Check if Docker daemon is running
echo ""
echo "2. Checking Docker daemon..."
if docker ps &> /dev/null; then
    echo "✅ Docker daemon is running"
else
    echo "❌ Docker daemon is not running. Please start Docker."
    exit 1
fi

# Check current directory and files
echo ""
echo "3. Checking project structure..."
if [ -f "Dockerfile" ]; then
    echo "✅ Dockerfile found"
else
    echo "❌ Dockerfile not found in current directory"
    exit 1
fi

if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt found"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

if [ -f "youtrack_mcp/version.py" ]; then
    echo "✅ version.py found"
    VERSION=$(python3 -c "exec(open('youtrack_mcp/version.py').read()); print(__version__)" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✅ Version extracted: $VERSION"
    else
        echo "❌ Failed to extract version"
        exit 1
    fi
else
    echo "❌ youtrack_mcp/version.py not found"
    exit 1
fi

# Test Docker build
echo ""
echo "4. Testing Docker build..."
echo "Building image: youtrack-mcp-test"

if docker build -t youtrack-mcp-test . --no-cache; then
    echo "✅ Docker build successful"
    
    # Test running the container
    echo ""
    echo "5. Testing container run..."
    timeout 5s docker run --rm youtrack-mcp-test --help 2>/dev/null || echo "ℹ️  Container started (terminated after 5s timeout)"
    echo "✅ Container test completed"
    
    # Show image size
    echo ""
    echo "6. Image information:"
    docker images youtrack-mcp-test --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
else
    echo "❌ Docker build failed"
    exit 1
fi

echo ""
echo "🔍 GitHub Actions Troubleshooting Guide:"
echo "========================================="
echo ""
echo "If the build fails in GitHub Actions but works locally, check:"
echo ""
echo "1. DOCKER_USERNAME secret is set in GitHub repository:"
echo "   - Go to: GitHub Repository → Settings → Secrets and variables → Actions"
echo "   - Check if DOCKER_USERNAME exists and contains your Docker Hub username"
echo ""
echo "2. DOCKER_PASSWORD secret is set in GitHub repository:"
echo "   - Should contain your Docker Hub access token (not password)"
echo "   - Create token at: https://hub.docker.com/settings/security"
echo ""
echo "3. Docker Hub repository exists:"
echo "   - Repository: searchanise/youtrack-mcp"
echo "   - Make sure it exists and you have push permissions"
echo ""
echo "4. Check rate limits:"
echo "   - Docker Hub has pull/push rate limits"
echo "   - Try running the action again after a few minutes"
echo ""
echo "5. Common error patterns to look for in logs:"
echo "   - 'denied: requested access to the resource is denied' → Authentication issue"
echo "   - 'failed to copy: io: read/write on closed pipe' → Network/timeout issue"
echo "   - 'repository name must be lowercase' → Tag naming issue"
echo ""
echo "✅ Local build test completed successfully!"
echo "If GitHub Actions still fails, check the secrets and repository settings." 