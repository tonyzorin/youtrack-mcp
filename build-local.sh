#!/bin/bash
# Build script for local Docker testing

# Get current version from version.py (try python3 first, then python)
VERSION=$(python3 -c "exec(open('youtrack_mcp/version.py').read()); print(__version__)" 2>/dev/null || python -c "exec(open('youtrack_mcp/version.py').read()); print(__version__)")

echo "🔨 Building local YouTrack MCP Docker image..."
echo "📦 Version: $VERSION"
echo "🏷️  Tag: youtrack-mcp-local:$VERSION-wip"
echo

# Build the Docker image with proper local naming
docker build -t "youtrack-mcp-local:$VERSION-wip" .

if [ $? -eq 0 ]; then
    echo
    echo "✅ Build successful!"
    echo "🐳 Image: youtrack-mcp-local:$VERSION-wip"
    echo
    echo "Next steps:"
    echo "  Test locally: ./run-docker-test.sh"
    echo "  Configure Claude Desktop with: youtrack-mcp-local:$VERSION-wip"
    echo "  When ready to release: git commit && git push (triggers CI/CD)"
else
    echo "❌ Build failed!"
    exit 1
fi 