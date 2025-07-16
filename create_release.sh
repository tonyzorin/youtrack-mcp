#!/bin/bash

# GitHub Release Creation Script for v1.0.1
# Run this after authenticating with: gh auth login

set -e

echo "🚀 Creating GitHub release v1.0.1..."

# Create the release
gh release create v1.0.1 \
  --title "v1.0.1 - Fix Parameter Parsing Issue" \
  --notes "## 🐛 Bug Fix Release

### Fixed
- **Issue #11**: Parameter parsing issue where \`create_issue\` failed while \`get_projects\` worked
- Trailing commas in MCP parameter parsing logic
- \`create_issue\` now works correctly with all parameter formats

### Technical Changes
- Enhanced parameter parsing in \`youtrack_mcp/server.py\`
- Proper handling of key=value pairs from \`shlex.split()\`
- Quote removal and trailing comma cleanup
- Backward compatible

### Docker Images
- \`tonyzorin/youtrack-mcp:1.0.1\`
- \`tonyzorin/youtrack-mcp:latest\`

**Full Changelog**: https://github.com/tonyzorin/youtrack-mcp/compare/v1.0.0...v1.0.1" \
  --latest

echo "✅ Release v1.0.1 created successfully!"
echo "🐳 CI/CD will now build Docker images:"
echo "   - tonyzorin/youtrack-mcp:1.0.1"
echo "   - tonyzorin/youtrack-mcp:latest"
echo "🎯 Issue #11 will be automatically closed!" 